"""Seeded synthetic POMDPs. Hidden customer values never enter observations."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import json
from pathlib import Path
# Keep published simulation experiments independent of the storefront snapshot.
PRODUCTS = json.loads((Path(__file__).parents[1] / 'data/simulation_catalog.json').read_text(encoding='utf-8'))
from .state import Strategy, VoiceAction, new_belief, vector, entropy, OBS_SIZE

PERSONAS = {'train': ['decisive','beginner','price_sensitive','technical','impatient'],
            'validation': ['skeptical','comparison'], 'test': ['contradictory','uncertain']}

class CustomerGym(gym.Env):
    def __init__(self, split='train', information_reward=True):
        self.split=split; self.information_reward=information_reward
        self.action_space=spaces.Discrete(len(Strategy))
        self.observation_space=spaces.Box(0,1,(OBS_SIZE,),dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.persona=str(self.np_random.choice(PERSONAS[self.split]))
        self.hidden={'budget':float(self.np_random.uniform(300,1800)),
                     'values':self.np_random.uniform(0,1,6),
                     'patience':int(self.np_random.integers(7,16)),
                     'intent':float(self.np_random.uniform(.35,.95))}
        if self.persona=='impatient': self.hidden['patience']=6
        if self.persona=='price_sensitive': self.hidden['budget']*=.6
        if self.persona=='decisive':self.hidden['intent']=.95
        if self.persona=='beginner':self.hidden['patience']=16
        if self.persona=='technical':self.hidden['values'][3]=.95
        if self.persona=='skeptical':self.hidden['intent']=.25
        if self.persona=='comparison':self.hidden['intent']=.45
        if self.persona=='contradictory':self.hidden['budget']=500;self.hidden['values'][3]=1.
        if self.persona=='uncertain':self.hidden['intent']=.4
        self.b=new_belief(); self.quality=0.; self.success=False; self.abandoned=False
        self.questions=0; self.repeated=0; self.gain=0.; self.reward_total=0.; self.ended=False
        return vector(self.b), {}

    def step(self, action):
        if self.ended: raise RuntimeError('Reset after episode end')
        a=Strategy(int(action)); before=entropy(self.b); r=-.1; done=False
        self.b['turn']+=1
        if self.persona=='uncertain' and self.b['turn']==4:
            self.hidden['budget']*=.7
            self.b['known'][0]=False
            self.b['objection']=True
        if a.value<6:
            self.questions+=1
            if self.b['known'][a.value]: r-=1; self.repeated+=1
            else:
                self.b['known'][a.value]=True
                self.b['values'][a.value]=min(self.hidden['budget']/3000,1) if a.value==0 else float(self.hidden['values'][a.value])
                r+=-.4 if a.value>=2 else .5
            self.b['asked'].append(a.name)
        elif a in [Strategy.RECOMMEND_PRODUCT,Strategy.SEARCH_PRODUCTS,Strategy.SHOW_ALTERNATIVE,
                   Strategy.COMPARE_PRODUCTS,Strategy.DOWNSELL,Strategy.HANDLE_PRICE_OBJECTION,Strategy.UPSELL]:
            missing_core=int(not self.b['known'][0])+int(not self.b['known'][1])
            budget=self.b['values'][0]*3000 if self.b['known'][0] else 1000
            candidates=[p for p in PRODUCTS if p['price']<=budget and p['category']=='laptops']
            if a in [Strategy.DOWNSELL,Strategy.HANDLE_PRICE_OBJECTION]: candidates=sorted(candidates,key=lambda p:p['price'])
            else: candidates=sorted(candidates,key=lambda p:p['price'],reverse=True)
            p=candidates[0] if candidates else None
            affordable=bool(p and p['price']<=self.hidden['budget'])
            performance=float(bool(p and ('gaming' in p['features'] or 'creator' in p['features'])))
            self.quality=(.6+.4*(1-abs(performance-self.hidden['values'][3]))) if affordable else 0.
            if missing_core:
                self.quality*=.25
                r-=1.5*missing_core
            if not self.b['shown']: r+=4*self.quality if affordable else -2
            else: r-=.2
            if a==Strategy.UPSELL: r-=2
            self.b['shown']=True; self.b['objection']=not affordable
        elif a==Strategy.ADD_TO_CART:
            # The policy may invite an action, but only the customer command is
            # allowed to mutate a real cart. Discourage simulated auto-adds.
            r-=2
        elif a==Strategy.ASK_FOR_PURCHASE:
            grounded=self.b['known'][0] and self.b['known'][1]
            if grounded and self.b['shown'] and self.np_random.random()<self.hidden['intent']*self.quality:
                self.b['cart']=True;self.success=True;done=True;r+=10
            else:r-=3 if not grounded else .5;self.b['objection']=True
        elif a==Strategy.END_CONVERSATION: done=True;r-=3 if not self.success else 0
        elif a in [Strategy.EXPLAIN_VALUE,Strategy.EXPLAIN_FEATURE,Strategy.HANDLE_TRUST_OBJECTION,Strategy.HANDLE_FEATURE_OBJECTION]:
            useful=self.b['shown'] and (self.b['objection'] or self.persona in ['skeptical','technical','uncertain'])
            r+=1 if useful else -.4;self.b['objection']=False
            if useful:self.hidden['intent']=min(.9,self.hidden['intent']+.15)
        elif a==Strategy.SCHEDULE_FOLLOWUP: done=True;r-=1
        else: r-=.3
        gain=before-entropy(self.b)
        if a.value in range(2,6):gain*=.1
        self.gain+=gain
        if self.information_reward:r+=gain
        if not done and self.b['turn']>=self.hidden['patience']: done=True; self.abandoned=True; r-=5
        self.b['engagement']=max(0,1-self.b['turn']/20)
        self.b['last_action']=a.name; self.reward_total+=r
        truncated=self.b['turn']>=20 and not done; self.ended=done or truncated
        info={} if not self.ended else {'success':self.success,'cart':self.b['cart'],'quality':self.quality,
              'abandoned':self.abandoned,'turns':self.b['turn'],'questions':self.questions,'repeated':self.repeated,
              'information_efficiency':self.gain/max(self.questions,1),'persona':self.persona}
        return vector(self.b),float(r),done,truncated,info

class VoiceGym(gym.Env):
    """250ms timing steps; silence may be hesitation or a completed user turn."""
    def __init__(self):
        self.action_space=spaces.Discrete(len(VoiceAction))
        self.observation_space=spaces.Box(0,1,(6,),dtype=np.float32)
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed); self.t=0; self.silence=0.; self.agent=False
        self.user=True; self.complete=False; self.interruptions=0; self.recoveries=0
        return self.obs(),{}
    def obs(self):
        return np.array([self.user,self.agent,self.silence,self.complete,self.user and self.agent,.7 if self.user else .05],dtype=np.float32)
    def step(self, action):
        a=VoiceAction(int(action)); r=0.
        if self.user:
            if self.agent:
                if a in [VoiceAction.STOP_SPEAKING,VoiceAction.YIELD_TURN]: self.agent=False;r=.5;self.recoveries+=1
                else:r=-2;self.interruptions+=1
            elif a==VoiceAction.LISTEN:r=.5
            elif a in [VoiceAction.SPEAK,VoiceAction.RESUME,VoiceAction.BACKCHANNEL]:r=-1;self.interruptions+=1
        elif self.complete and not self.agent:
            if a in [VoiceAction.SPEAK,VoiceAction.RESUME]:r=.8;self.agent=True
            else:r=-.5*self.silence
        elif not self.complete and not self.agent:
            r=.3 if a in [VoiceAction.WAIT,VoiceAction.LISTEN] else -.5
        else:r=.1 if a==VoiceAction.WAIT else -.2
        self.t+=1
        self.user=bool(self.np_random.random()<(.25 if self.agent else .6))
        self.silence=0. if self.user else min(1,self.silence+.125)
        self.complete=bool(not self.user and self.np_random.random()<min(.95,self.silence*2))
        if self.agent and self.np_random.random()<.2:self.agent=False
        done=self.t>=80
        return self.obs(),float(r),False,done,{'interruptions':self.interruptions,'recoveries':self.recoveries} if done else {}
