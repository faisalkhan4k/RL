import unittest
from unittest.mock import patch
import numpy as np
from stable_baselines3.common.env_checker import check_env
from sales_agent.hrl.environments import CustomerGym,VoiceGym,PERSONAS
from sales_agent.hrl.state import Strategy,VoiceAction,entropy,new_belief,vector,rule_action
from sales_agent.hrl.policy import decide
from sales_agent.graph import build_graph
import asyncio
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sales_agent.app import create_app

class HRLTests(unittest.TestCase):
    def test_gym_contracts(self):
        check_env(CustomerGym());check_env(VoiceGym())
    def test_seed_and_hidden_state_isolation(self):
        a,b=CustomerGym(),CustomerGym()
        oa,_=a.reset(seed=12);ob,_=b.reset(seed=12)
        np.testing.assert_array_equal(oa,ob)
        a.hidden['budget']=2
        np.testing.assert_array_equal(vector(a.b),vector(b.b))
        a.step(Strategy.ASK_BUDGET);b.step(Strategy.ASK_BUDGET)
        self.assertNotEqual(a.b['values'][0],b.b['values'][0])
    def test_information_reward_and_repeat_cost(self):
        env=CustomerGym();env.reset(seed=4)
        before=entropy(env.b);_,first,*_=env.step(Strategy.ASK_BUDGET)
        self.assertLess(entropy(env.b),before)
        _,repeat,*_=env.step(Strategy.ASK_BUDGET)
        self.assertGreater(first,repeat);self.assertEqual(env.repeated,1)
    def test_split_disjointness(self):
        self.assertFalse(set(PERSONAS['train'])&set(PERSONAS['test']))
    def test_stop_overrides_policy_without_cart_mutation(self):
        result=asyncio.run(build_graph().ainvoke({'messages':[{'role':'user','content':'no thanks'}],'requirements':{}}))
        self.assertEqual(result['strategy'],'END_CONVERSATION');self.assertEqual(result['actions'],[])
        self.assertEqual(result['debug']['override'],'customer_declined')
    def test_rule_provenance(self):
        d=decide(vector(new_belief()))
        self.assertEqual(d['source'],'rule_baseline');self.assertEqual(d['action'],'ASK_BUDGET')
        self.assertAlmostEqual(sum(d['probabilities'].values()),1)
    def test_rejected_product_is_not_recommended_again(self):
        async def conversation():
            graph=build_graph()
            first=await graph.ainvoke({'messages':[{'role':'user','content':'laptop under 1500 for school'}],'requirements':{}})
            return first,await graph.ainvoke({'messages':[{'role':'user','content':"I don't like it"}],'requirements':first['requirements'],'belief':first['belief']})
        first,second=asyncio.run(conversation())
        self.assertEqual(second['strategy'],'SHOW_ALTERNATIVE')
        self.assertNotIn(first['products'][0]['id'],[p['id'] for p in second['products']])
    def test_voice_interruption_reward(self):
        env=VoiceGym();env.reset(seed=7);env.agent=True;env.user=True
        _,r,*_=env.step(VoiceAction.STOP_SPEAKING)
        self.assertGreater(r,0);self.assertEqual(env.recoveries,1)
    def test_voice_socket_pause_and_epoch(self):
        class Recognizer:
            def __init__(self,*args):pass
            def Reset(self):pass
            def AcceptWaveform(self,audio):return True
            def Result(self):return json.dumps({'text':'test utterance'})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'conf').mkdir();(root/'conf/model.conf').touch()
            with patch.dict('os.environ',{'SALES_VOSK_MODEL_PATH':folder,'SALES_VOICE_POLICY':''}),patch('sales_agent.app.load_voice_model',return_value=object()),patch.dict('sys.modules',{'vosk':SimpleNamespace(KaldiRecognizer=Recognizer)}):
                with TestClient(create_app(str(root/'test.sqlite3'))) as c:
                    c.post('/api/session')
                    with c.websocket_connect('/api/voice',headers={'origin':'http://testserver'}) as ws:
                        self.assertTrue(ws.receive_json()['ready'])
                        ws.send_json({'type':'reset','epoch':7,'paused':True});ws.send_bytes(b'\0\0'*200)
                        ws.send_json({'type':'timing','observation':[0,0,1,1,0,0]})
                        result=ws.receive_json();self.assertIn('timing',result);self.assertEqual(result['epoch'],7)
                        ws.send_json({'type':'reset','epoch':8,'paused':False});ws.send_bytes(b'\0\0'*200)
                        result=ws.receive_json();self.assertEqual(result,{'text':'test utterance','epoch':8})

if __name__=='__main__':unittest.main()
