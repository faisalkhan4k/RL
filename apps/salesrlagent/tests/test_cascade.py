import asyncio
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from sales_agent.cascade import CascadeSession, Providers, configuration
from sales_agent.app import create_app
import tempfile
from pathlib import Path

class Socket:
    def __init__(self):self.events=[]
    async def send_json(self,event):self.events.append(event)

class CascadeTests(unittest.IsolatedAsyncioTestCase):
    async def test_named_product_focus_follows_generated_speech(self):
        from sales_agent.catalog import BY_ID
        class Fake:
            async def sentences(self,context):yield 'The Google Pixel 9a is close to your budget.'
            async def audio(self,text):yield b'\0\0'
        async def prepare(text):return {'turn_id':'test','products':[BY_ID['apple-ipad-128'],BY_ID['google-pixel-9a']], 'focus_product_id':'apple-ipad-128'},{}
        async def finish(result,text,complete):pass
        ws=Socket();session=CascadeSession(ws,prepare,finish,Fake())
        await session.start_turn('phones');await session.reply
        self.assertEqual([e['product_id'] for e in ws.events if e['type']=='focus'],['google-pixel-9a'])

    async def test_tool_confirmation_bypasses_llm(self):
        provider=Providers()
        try:
            self.assertEqual([x async for x in provider.sentences({'tool_reply':'Added Google Pixel 9a to your cart.'})],['Added Google Pixel 9a to your cart.'])
        finally:await provider.http.aclose()

    async def test_noise_and_echo_do_not_cancel_but_customer_speech_does(self):
        from unittest.mock import AsyncMock
        session=CascadeSession(Socket(),AsyncMock(),AsyncMock(),object())
        session.playback_pending=True
        session.spoken=['This laptop has a bright screen. What is your budget?']
        await session.handle_transcript({'type':'SpeechStarted'})
        await session.handle_transcript({'type':'Results','is_final':True,'speech_final':True,'channel':{'alternatives':[{'transcript':'What is your budget?','confidence':.99}]}})
        self.assertEqual(session.generation,0)
        self.assertEqual(session.parts,[])
        self.assertTrue(session.playback_pending)
        await session.handle_transcript({'type':'Results','channel':{'alternatives':[{'transcript':'Actually I want a TV','confidence':.99}]}})
        self.assertEqual(session.generation,1)
        self.assertFalse(session.playback_pending)
        self.assertEqual(session.ws.events[0]['type'],'interrupted')

    async def test_playback_completion_is_generation_scoped(self):
        session=CascadeSession(Socket(),None,None,object())
        session.generation=2;session.playback_pending=True
        session.playback_finished(1)
        self.assertTrue(session.playback_pending)
        session.playback_finished(2)
        self.assertFalse(session.playback_pending)

    async def test_interrupt_cancels_generation_and_persists_partial(self):
        started=asyncio.Event();cancelled=asyncio.Event();saved=[]
        class Fake:
            async def sentences(self,context):yield 'First sentence.'
            async def audio(self,text):
                yield b'\0\0'
                started.set()
                try:await asyncio.Event().wait()
                finally:cancelled.set()
        async def prepare(text):return {'turn_id':'test'},{}
        async def finish(result,text,complete):saved.append((text,complete))
        socket=Socket();session=CascadeSession(socket,prepare,finish,Fake())
        await session.start_turn('laptop');await asyncio.wait_for(started.wait(),1)
        await session.interrupt()
        self.assertTrue(cancelled.is_set());self.assertEqual(saved,[('First sentence.',False)])
        self.assertEqual(socket.events[-1]['type'],'interrupted')
        self.assertEqual(socket.events[-1]['generation'],2)
        self.assertFalse(any(e['type']=='done' for e in socket.events))
    async def test_sentence_stream_precedes_full_reply_and_ignores_reasoning(self):
        stream='data: {"choices":[{"delta":{"reasoning":"secret reasoning","content":"Hello. "}}]}\n\ndata: {"choices":[{"delta":{"content":"What is your budget?"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
        with patch.dict('os.environ',{'GROQ_API_KEY':'test','DEEPGRAM_API_KEY':'test'}):
            provider=Providers();await provider.http.aclose()
            provider.http=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,text=stream)))
            parts=[s async for s in provider.sentences({})]
            self.assertEqual(parts,['Hello.','What is your budget?']);await provider.http.aclose()
    async def test_http_rate_limit_not_retried(self):
        calls=[]
        def respond(request):calls.append(request);return httpx.Response(429,json={'error':'limit'})
        with patch.dict('os.environ',{'GROQ_API_KEY':'test'}):
            p=Providers();await p.http.aclose();p.http=httpx.AsyncClient(transport=httpx.MockTransport(respond))
            with self.assertRaises(httpx.HTTPStatusError):_=[s async for s in p.sentences({})]
            self.assertEqual(len(calls),1);await p.http.aclose()
    async def test_missing_credentials_never_opens_provider(self):
        with patch.dict('os.environ',{'GROQ_API_KEY':'','DEEPGRAM_API_KEY':''}),tempfile.TemporaryDirectory() as tmp:
            with TestClient(create_app(str(Path(tmp)/'test.db'))) as client:
                client.post('/api/session')
                self.assertFalse(client.get('/api/voice/config').json()['configured'])
                with client.websocket_connect('/api/voice/cascade',headers={'origin':'http://testserver'}) as ws:
                    result=ws.receive_json();self.assertEqual(result['type'],'error');self.assertIn('API_KEY',result['message'])
    async def test_configuration_never_exposes_secrets(self):
        with patch.dict('os.environ',{'GROQ_API_KEY':'secret-value-1','DEEPGRAM_API_KEY':'secret-value-2'}):
            c=configuration();self.assertTrue(c['configured']);self.assertNotIn('secret-value',str(c));self.assertEqual(c['max_seconds'],180)
