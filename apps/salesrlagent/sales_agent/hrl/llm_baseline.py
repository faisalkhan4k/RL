"""Explicitly opted-in LLM-only action baseline. No hidden customer state."""
import json
import os
import httpx
from .state import Strategy

class LLMBaseline:
    def __init__(self):
        self.url=os.environ['SALES_LLM_URL'];self.key=os.environ['SALES_LLM_KEY'];self.model=os.environ['SALES_LLM_MODEL']
    def __call__(self,observation):
        payload={'model':self.model,'temperature':0,'response_format':{'type':'json_object'},'messages':[
            {'role':'system','content':'Choose the next sales action. Return JSON with a single action field from: '+', '.join(a.name for a in Strategy)+'. Observation: first 6 known flags, next 6 values (budget/3000, use, priority, performance, portability, battery); then turn/20, shown, objection, cart, estimated intent, engagement. Optimize useful recommendations and customer satisfaction without repeated questions.'},
            {'role':'user','content':json.dumps(observation.tolist())}]}
        response=httpx.post(self.url,headers={'Authorization':f'Bearer {self.key}'},json=payload,timeout=20)
        response.raise_for_status();body=json.loads(response.json()['choices'][0]['message']['content'])
        return Strategy[body['action']]
