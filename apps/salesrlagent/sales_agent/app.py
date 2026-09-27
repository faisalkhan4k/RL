"""Same-origin voice storefront. Run with one worker for per-session serialization."""
import asyncio
from contextlib import asynccontextmanager
from collections import OrderedDict
from functools import lru_cache
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import time
import wave
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field
from .catalog import PRODUCTS, BY_ID, retrieve
from .graph import build_graph
from .store import Store
from .telemetry import logger, tracer, turns, latency, feedback
from .hrl.policy import decide
from .cascade import CascadeSession, configuration
from .commands import command, remember_result
from .commerce import commerce_command

STATIC = Path(__file__).parent / 'static'
DEFAULT_VOICE_MODEL = Path('data/models/vosk-model-small-en-us-0.15')
DEFAULT_TTS_MODEL = Path('data/models/piper/en_US-lessac-medium.onnx')


@lru_cache(maxsize=2)
def load_voice_model(path):
    from vosk import Model
    return Model(path)


@lru_cache(maxsize=2)
def load_tts_model(path):
    from piper import PiperVoice
    return PiperVoice.load(path)


class Message(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    request_id: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9-]+$')


class Rating(BaseModel):
    turn_id: str
    helpful: bool


class CartChange(BaseModel):
    product_id: str
    quantity: int = Field(ge=0, le=5)


class ViewState(BaseModel):
    product_ids: list[str] = Field(max_length=6)
    focused_product: str | None = None


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)


def create_app(db_path=None, predictor=None):
    if os.getenv('SALES_DATABASE_URL') and db_path is None:
        from .postgres_store import PostgresStore
        store=PostgresStore(os.environ['SALES_DATABASE_URL'])
    else:
        store = Store(db_path or os.getenv('SALES_DB_PATH', 'data/sales.sqlite3'))
    graph = build_graph(predictor)
    # A bounded stripe table avoids one permanent lock per anonymous session.
    locks = [asyncio.Lock() for _ in range(128)]
    tts_lock = asyncio.Lock()
    voice_decisions=OrderedDict()
    active_voice=set()

    @asynccontextmanager
    async def lifespan(app):
        logger.info('server.started', extra={'fields': {'model_loaded': predictor is not None}})
        yield

    app = FastAPI(title='Hierarchical RL Voice Sales Agent', version='0.3.0', lifespan=lifespan)
    app.state.store = store

    @app.middleware('http')
    async def guard(request, call_next):
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin:
            expected = os.getenv('SALES_PUBLIC_ORIGIN', str(request.base_url).rstrip('/'))
            if origin != expected:
                return JSONResponse({'detail': 'Cross-origin write rejected'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers['Permissions-Policy'] = 'microphone=(self)'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    def session(request):
        sid = request.cookies.get('sales_session', '')
        state = store.get(sid) if sid else None
        if state is None:
            raise HTTPException(401, 'Session expired. Refresh to start again.')
        return sid, state

    def lock(sid):
        return locks[sum(sid.encode()) % len(locks)]

    @app.get('/healthz')
    def health():
        with store.connect() as db:
            db.execute('SELECT 1')
        voice_path = Path(os.getenv('SALES_VOSK_MODEL_PATH', DEFAULT_VOICE_MODEL))
        tts_path = Path(os.getenv('SALES_PIPER_MODEL_PATH', DEFAULT_TTS_MODEL))
        return {'status': 'ok', 'model': 'experimental' if predictor else 'not_trained',
                'strategy_policy': 'ppo_simulation' if Path(os.getenv('SALES_STRATEGY_POLICY','')).is_file() else 'rule_baseline',
                'voice_policy': 'ppo_simulation' if Path(os.getenv('SALES_VOICE_POLICY','')).is_file() else 'rule_baseline',
                'offline_voice': (voice_path / 'conf/model.conf').is_file(),
                'natural_voice': tts_path.is_file() and Path(f'{tts_path}.json').is_file()}

    @app.get('/api/voice/config')
    def voice_config():
        return configuration()

    @app.websocket('/api/voice/cascade')
    async def cascade_socket(ws: WebSocket):
        sid=ws.cookies.get('sales_session','')
        scheme='https' if ws.url.scheme=='wss' else 'http'
        expected=os.getenv('SALES_PUBLIC_ORIGIN',f'{scheme}://{ws.headers.get("host", "")}')
        if ws.headers.get('origin')!=expected or not sid or store.get(sid) is None:
            await ws.close(code=1008);return
        await ws.accept()
        config=configuration()
        if not config['configured']:
            await ws.send_json({'type':'error','message':'Set DEEPGRAM_API_KEY and GROQ_API_KEY in the server environment. Voice is not connected.'})
            await ws.close(code=1008);return
        if active_voice:
            await ws.send_json({'type':'error','message':'One voice session is already active. Stop it before starting another.'})
            await ws.close(code=1008);return
        active_voice.add(sid)

        async def prepare(text):
            async with lock(sid):
                state=store.get(sid)
                if state is None:raise RuntimeError('Session expired')
                messages=(state['messages']+[{'role':'user','content':text}])[-24:]
                result=await commerce_command(text,state) or command(text,state) or await graph.ainvoke({'messages':messages,'requirements':state['requirements'],'belief':state.get('belief'),'skip_language':True})
                remember_result(state,result)
                result['turn_id']=str(uuid4())
                state.update(messages=messages,requirements=result['requirements'],belief=result['belief'])
                store.save(sid,state)
                context={'selected_action':result['strategy'],'belief':result['belief'],'products':result['products'],'conversation':messages[-8:],'tool_reply':result.get('tool_reply'),'cart':state['cart']}
                return {k:result[k] for k in ['turn_id','reply','products','actions','requirements','debug','strategy','cart','focus_product_id'] if k in result},context

        async def finish(result,text,complete):
            async with lock(sid):
                state=store.get(sid)
                if state is None:return
                # Generated text can exceed what played; label interrupted turns explicitly.
                if text:state['messages']=(state['messages']+[{'role':'assistant','content':text+('' if complete else ' [reply interrupted; some audio may not have played]')}])[-24:]
                result['reply']=text;result['debug']['interrupted']=not complete
                remember_result(state,result)
                state['turn_ids']=(state['turn_ids']+[result['turn_id']])[-100:]
                state['events']=(state['events']+[{'request_id':result['turn_id'],'text':'','at':time.time(),'response':result}])[-40:]
                store.save(sid,state)
        try:
            await CascadeSession(ws,prepare,finish).run()
        except (WebSocketDisconnect,RuntimeError):pass
        except Exception as exc:
            logger.warning('voice.cascade_failed',extra={'fields':{'kind':type(exc).__name__}})
            try:await ws.send_json({'type':'error','message':'Deepgram connection failed. Check your API key, credits and network.'})
            except Exception:pass
        finally:
            active_voice.discard(sid)
            try:await ws.close()
            except Exception:pass

    @app.websocket('/api/voice')
    async def voice_socket(websocket: WebSocket):
        origin = websocket.headers.get('origin')
        scheme = 'https' if websocket.url.scheme == 'wss' else 'http'
        expected = os.getenv('SALES_PUBLIC_ORIGIN', f'{scheme}://{websocket.headers.get("host", "")}')
        sid = websocket.cookies.get('sales_session', '')
        if (origin and origin != expected) or not sid or store.get(sid) is None:
            await websocket.close(code=1008)
            return
        voice_path = Path(os.getenv('SALES_VOSK_MODEL_PATH', DEFAULT_VOICE_MODEL))
        if not (voice_path / 'conf/model.conf').is_file():
            await websocket.accept()
            await websocket.send_json({'error': 'Offline speech model is not installed.'})
            await websocket.close(code=1011)
            return
        await websocket.accept()
        try:
            from vosk import KaldiRecognizer
            model = await asyncio.to_thread(load_voice_model, str(voice_path.resolve()))
            recognizer = KaldiRecognizer(model, 16000)
            epoch=0
            paused=False
            await websocket.send_json({'ready': True})
            while True:
                packet=await websocket.receive()
                if packet['type']=='websocket.disconnect':break
                if packet.get('text'):
                    if len(packet['text'])>2048: await websocket.close(code=1009);return
                    control=json.loads(packet['text'])
                    if control.get('type')=='reset':
                        epoch=int(control.get('epoch',0));paused=bool(control.get('paused',False));recognizer.Reset()
                    elif control.get('type')=='timing':
                        values=control.get('observation',[])
                        if len(values)==6 and all(isinstance(v,(int,float)) and 0<=v<=1 for v in values):
                            result=await asyncio.to_thread(decide,values,os.getenv('SALES_VOICE_POLICY'),True)
                            voice_decisions[sid]=result
                            voice_decisions.move_to_end(sid)
                            if len(voice_decisions)>128:voice_decisions.popitem(last=False)
                            await websocket.send_json({'timing':result,'epoch':epoch})
                    continue
                audio = packet.get('bytes',b'')
                if paused:continue
                if len(audio) > 131072:
                    await websocket.close(code=1009)
                    return
                if await asyncio.to_thread(recognizer.AcceptWaveform,audio):
                    text = json.loads(recognizer.Result()).get('text', '').strip()
                    if text:
                        await websocket.send_json({'text': text,'epoch':epoch})
                else:
                    partial = json.loads(recognizer.PartialResult()).get('partial', '').strip()
                    if partial:
                        await websocket.send_json({'partial': partial,'epoch':epoch})
        except WebSocketDisconnect:
            return
        except Exception:
            logger.exception('voice.websocket_failed')
            try:
                await websocket.close(code=1011)
            except RuntimeError:
                pass

    @app.post('/api/speech')
    async def speech(body: SpeechRequest, request: Request):
        session(request)
        tts_path = Path(os.getenv('SALES_PIPER_MODEL_PATH', DEFAULT_TTS_MODEL))
        if not tts_path.is_file() or not Path(f'{tts_path}.json').is_file():
            raise HTTPException(503, 'Natural voice model is not installed')

        def render():
            voice = load_tts_model(str(tts_path.resolve()))
            output = BytesIO()
            with wave.open(output, 'wb') as wav_file:
                voice.synthesize_wav(body.text, wav_file)
            return output.getvalue()

        try:
            async with tts_lock:
                audio = await asyncio.to_thread(render)
        except Exception:
            logger.exception('speech.synthesis_failed')
            raise HTTPException(503, 'Natural voice is temporarily unavailable') from None
        return Response(audio, media_type='audio/wav', headers={'Cache-Control': 'no-store'})

    @app.get('/api/catalog')
    def catalog():
        return {'products': PRODUCTS, 'demo': True, 'currency': 'USD'}

    @app.get('/api/integrations')
    def integrations():
        return {'commerce': {'mode': 'local_demo', 'transport': 'MCP stdio',
                'tools': ['inventory_lookup', 'order_lookup'], 'read_only': True,
                'example_orders': ['DEMO-1001', 'DEMO-1002', 'DEMO-1003']}}

    @app.post('/api/session')
    def start(request: Request, response: Response):
        sid = request.cookies.get('sales_session')
        state = store.get(sid) if sid else None
        if state is None:
            sid = store.create()
            state = store.get(sid)
        # Retire unavailable fictional SKUs without deleting conversation history.
        valid_cart = [item for item in state['cart'] if item['product_id'] in BY_ID]
        if valid_cart != state['cart']:
            state['cart'] = valid_cart
            store.save(sid, state)
        response.set_cookie('sales_session', sid, httponly=True, samesite='strict',
                            secure=os.getenv('SALES_SECURE_COOKIES', 'false').lower() == 'true', max_age=86400)
        return {'messages': state['messages'], 'cart': state['cart'], 'requirements': state['requirements'],
                'products': retrieve(state['requirements']) if state['requirements'] else PRODUCTS,
                'model': 'experimental' if predictor else 'not_trained'}

    @app.delete('/api/session')
    async def forget(request: Request, response: Response):
        sid, _ = session(request)
        async with lock(sid):
            store.delete(sid)
        response.delete_cookie('sales_session')
        return {'deleted': True}

    @app.post('/api/chat')
    async def chat(body: Message, request: Request):
        sid, _ = session(request)
        if not body.text.strip():
            raise HTTPException(422, 'Message cannot be blank')
        async with lock(sid):
            state = store.get(sid)
            if state is None:
                raise HTTPException(401, 'Session expired')
            for event in state['events']:
                if event['request_id'] == body.request_id:
                    if event['text'] != body.text:
                        raise HTTPException(409, 'Request ID already used for different text')
                    return event['response']
            now = time.time()
            if len([e for e in state['events'] if e['at'] > now - 60]) >= 20:
                raise HTTPException(429, 'Please wait a moment before sending more messages')
            start_time = time.perf_counter()
            with tracer.start_as_current_span('sales.turn') as span:
                messages = (state['messages'] + [{'role': 'user', 'content': body.text}])[-24:]
                try:
                    result = await commerce_command(body.text,state) or command(body.text,state) or await asyncio.wait_for(graph.ainvoke({'messages': messages, 'requirements': state['requirements'], 'belief': state.get('belief')}), timeout=20)
                except Exception:
                    logger.error('turn.failed')
                    raise HTTPException(503, 'The guide is unavailable. Please try again.') from None
                remember_result(state,result)
                elapsed = (time.perf_counter() - start_time) * 1000
                turn_id = str(uuid4())
                output = {k: result[k] for k in ['reply', 'products', 'actions', 'requirements', 'prediction', 'strategy', 'debug','cart']}
                output['focus_product_id']=result.get('focus_product_id')
                output.update(turn_id=turn_id, latency_ms=round(elapsed, 1), trace_id=format(span.get_span_context().trace_id, '032x'))
                state['messages'] = (messages + [{'role': 'assistant', 'content': result['reply']}])[-24:]
                state['requirements'] = result['requirements']
                state['belief'] = result['belief']
                state['turn_ids'] = (state['turn_ids'] + [turn_id])[-100:]
                state['events'] = (state['events'] + [{'request_id': body.request_id, 'text': body.text, 'at': now, 'response': output}])[-40:]
                store.save(sid, state)
                span.set_attribute('sales.strategy', result['strategy'])
                turns.add(1, {'strategy': result['strategy']})
                latency.record(elapsed)
                logger.info('turn.completed', extra={'fields': {'duration_ms': round(elapsed, 1), 'strategy': result['strategy'], 'matches': len(result['products'])}})
                return output

    @app.post('/api/feedback')
    async def rate(body: Rating, request: Request):
        sid, _ = session(request)
        async with lock(sid):
            state = store.get(sid)
            if not state or body.turn_id not in state['turn_ids']:
                raise HTTPException(404, 'Turn not found')
            accepted = store.rate(sid, body.turn_id, body.helpful)
            if accepted:
                feedback.add(1, {'helpful': str(body.helpful).lower()})
            return {'accepted': accepted}

    @app.put('/api/view')
    async def view(body: ViewState, request: Request):
        sid, _ = session(request)
        if any(pid not in BY_ID for pid in body.product_ids) or (body.focused_product and body.focused_product not in body.product_ids):
            raise HTTPException(422,'Unknown product reference')
        async with lock(sid):
            state=store.get(sid)
            if state is None:raise HTTPException(401,'Session expired')
            state['view_ids']=body.product_ids
            if body.focused_product:state['focused_product']=body.focused_product
            store.save(sid,state)
        return {'ok':True}

    @app.put('/api/cart')
    async def cart(body: CartChange, request: Request):
        sid, _ = session(request)
        if body.product_id not in BY_ID:
            raise HTTPException(404, 'Product not found')
        if body.quantity > BY_ID[body.product_id]['stock']:
            raise HTTPException(409, 'Quantity exceeds demo inventory')
        async with lock(sid):
            state = store.get(sid)
            if not state:
                raise HTTPException(401, 'Session expired')
            state['cart'] = [p for p in state['cart'] if p['product_id'] != body.product_id]
            if body.quantity:
                state['cart'].append(body.model_dump())
            if state.get('belief'):state['belief']['cart']=bool(state['cart'])
            store.save(sid, state)
            return {'cart': state['cart'], 'total': sum(BY_ID[p['product_id']]['price'] * p['quantity'] for p in state['cart'])}

    @app.post('/api/checkout')
    async def checkout(request: Request):
        sid, _ = session(request)
        async with lock(sid):
            state = store.get(sid)
            if not state or not state['cart']:
                raise HTTPException(400, 'Your bag is empty')
            total = sum(BY_ID[p['product_id']]['price'] * p['quantity'] for p in state['cart'])
            state['cart'] = []
            store.save(sid, state)
            return {'demo': True, 'total': total, 'message': 'Demo complete. No order placed and no payment taken.'}

    app.mount('/static', StaticFiles(directory=STATIC), name='static')
    if (STATIC / 'ui').is_dir():
        app.mount('/ui', StaticFiles(directory=STATIC / 'ui'), name='ui')

    @app.get('/')
    @app.get('/deals')
    @app.get('/sales')
    @app.get('/categories')
    @app.get('/categories/{category}')
    @app.get('/cart')
    @app.get('/orders')
    @app.get('/recommendations')
    def index():
        built=STATIC / 'ui/index.html'
        return FileResponse(built if built.is_file() else STATIC / 'index.html')

    @app.get('/research')
    def research():
        return FileResponse(STATIC / 'research.html')

    @app.get('/api/research')
    def research_state(request: Request):
        sid,state=session(request)
        events=state.get('events',[])
        return {'latest':events[-1]['response'].get('debug',{}) if events else {},
                'voice':voice_decisions.get(sid),
                'strategy_checkpoint':bool(os.getenv('SALES_STRATEGY_POLICY')),
                'voice_checkpoint':bool(os.getenv('SALES_VOICE_POLICY'))}

    FastAPIInstrumentor.instrument_app(app, excluded_urls='healthz,/static/.*', exclude_spans=['send', 'receive'])
    return app
