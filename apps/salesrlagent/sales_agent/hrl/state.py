"""Observable belief features shared by simulation and the live policy."""
from enum import IntEnum
import math
import numpy as np

class Strategy(IntEnum):
    ASK_BUDGET = 0
    ASK_USE_CASE = 1
    ASK_PRIORITY = 2
    ASK_PERFORMANCE_REQUIREMENT = 3
    ASK_PORTABILITY = 4
    ASK_BATTERY_REQUIREMENT = 5
    SEARCH_PRODUCTS = 6
    RECOMMEND_PRODUCT = 7
    SHOW_ALTERNATIVE = 8
    COMPARE_PRODUCTS = 9
    EXPLAIN_FEATURE = 10
    EXPLAIN_VALUE = 11
    HANDLE_PRICE_OBJECTION = 12
    HANDLE_FEATURE_OBJECTION = 13
    HANDLE_TRUST_OBJECTION = 14
    UPSELL = 15
    DOWNSELL = 16
    ASK_FOR_PURCHASE = 17
    ADD_TO_CART = 18
    SCHEDULE_FOLLOWUP = 19
    WAIT = 20
    END_CONVERSATION = 21

class VoiceAction(IntEnum):
    LISTEN = 0
    WAIT = 1
    SPEAK = 2
    STOP_SPEAKING = 3
    YIELD_TURN = 4
    BACKCHANNEL = 5
    RESUME = 6
    ASK_CLARIFICATION = 7

SLOTS = ['budget', 'use_case', 'priority', 'performance', 'portability', 'battery']
OBS_SIZE = 18

def new_belief():
    return {'known': [False]*6, 'values': [0.5]*6, 'turn': 0, 'shown': False,
            'objection': False, 'cart': False, 'asked': [], 'last_action': None,
            'intent': 0.5, 'engagement': 1.0, 'products_shown': [], 'rejected_products': [], 'last_recommended': None}

def vector(b):
    return np.array([*map(float,b['known']), *b['values'], min(b['turn']/20,1),
                     float(b['shown']), float(b['objection']), float(b['cart']),
                     b['intent'], b['engagement']], dtype=np.float32)

def entropy(b):
    # Independent binary uncertainty proxy, not a calibrated posterior.
    return sum(0.0 if k else math.log(2) for k in b['known'])

def rule_action(obs):
    if not obs[0]: return Strategy.ASK_BUDGET
    if not obs[1]: return Strategy.ASK_USE_CASE
    if obs[14]: return Strategy.HANDLE_PRICE_OBJECTION
    if not obs[13]: return Strategy.RECOMMEND_PRODUCT
    if not obs[15]: return Strategy.ADD_TO_CART
    return Strategy.ASK_FOR_PURCHASE

def update_belief(previous, req, text):
    import copy
    b = copy.deepcopy(previous or new_belief())
    b['turn'] += 1
    if 'budget' in req: b['known'][0]=True; b['values'][0]=min(req['budget']/3000,1)
    if req.get('uses') or req.get('use') or b.get('last_action')=='ASK_USE_CASE': b['known'][1]=True
    t=text.lower()
    if any(w in t for w in ["don't like",'dont like','dislike','not that one']) and b.get('last_recommended'):
        b.setdefault('rejected_products',[]).append(b['last_recommended'])
    for i, words in [(2,['important','priority','matters']), (3,['gpu','performance','gaming','machine learning']),
                     (4,['carry','lightweight','portable']), (5,['battery'])]:
        if any(w in t for w in words): b['known'][i]=True; b['values'][i]=0.9
    b['objection']=any(w in t for w in ['expensive','cheaper',"don't like",'too much','not sure','trust'])
    b['engagement']=max(.1,1-b['turn']*.025)
    return b
