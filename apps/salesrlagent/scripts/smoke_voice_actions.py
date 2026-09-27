"""Optional real-provider smoke test using synthetic audio, never the microphone.
Run from the app directory: python scripts/smoke_voice_actions.py
Uses a short Deepgram TTS/STT call and creates a separate disposable session.
"""
import asyncio, base64, json, os, sys
from pathlib import Path
import httpx
import numpy as np
from dotenv import load_dotenv
from websockets.asyncio.client import connect
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sales_agent.cascade import Providers

async def main():
 load_dotenv(Path(__file__).resolve().parents[1]/'.env')
 provider=Providers()
 try: audio=b''.join([x async for x in provider.audio('Add Google Pixel nine a to my cart.')])
 finally:await provider.http.aclose()
 samples=np.frombuffer(audio,dtype='<i2')
 pcm=np.interp(np.arange(0,len(samples),1.5),np.arange(len(samples)),samples).astype('<i2').tobytes()+b'\0'*32000
 async with httpx.AsyncClient() as http:
  (await http.post('http://127.0.0.1:8000/api/session')).raise_for_status()
  cookie='; '.join(f'{k}={v}' for k,v in http.cookies.items())
  try:
   async with connect('ws://127.0.0.1:8000/api/voice/cascade',origin='http://127.0.0.1:8000',additional_headers={'Cookie':cookie}) as ws:
    assert json.loads(await asyncio.wait_for(ws.recv(),15))['type']=='ready'
    async def feed():
     for start in range(0,len(pcm),2560):
      await ws.send(pcm[start:start+2560]);await asyncio.sleep(.08)
    feed_task=asyncio.create_task(feed());got_result=False;audio_bytes=0
    try:
     while True:
      e=json.loads(await asyncio.wait_for(ws.recv(),25))
      if e['type']=='error':raise RuntimeError(e['message'])
      if e['type']=='user':print('Synthetic transcript:',e['text'])
      if e['type']=='result':
       assert e['result']['cart']==[{'product_id':'google-pixel-9a','quantity':1}],(e['result']['cart'],e['result'].get('reply'))
       assert any(a['type']=='open_cart' for a in e['result']['actions'])
       got_result=True
      if e['type']=='audio':audio_bytes+=len(base64.b64decode(e['pcm']))
      if e['type']=='done':break
    finally:feed_task.cancel();await asyncio.gather(feed_task,return_exceptions=True)
    assert got_result and audio_bytes>0
    print(json.dumps({'synthetic_speech_to_cart':'passed','spoken_confirmation_seconds':round(audio_bytes/48000,2)}))
  finally:await http.delete('http://127.0.0.1:8000/api/session')

if __name__=='__main__':asyncio.run(main())
