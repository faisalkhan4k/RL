"""WHAT: policy, tools; HOW: language realization. No LLM tool authority."""
import os
import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from .catalog import requirements, retrieve
from .telemetry import tracer
from .hrl.state import update_belief, vector
from .hrl.policy import decide
from .hrl.language import realize

class ShoppingState(TypedDict, total=False):
    messages:list
    requirements:dict
    belief:dict
    products:list
    prediction:dict
    strategy:str
    reply:str
    actions:list
    debug:dict
    skip_language:bool

def build_graph(predictor=None):
    def understand(state):
        with tracer.start_as_current_span('hrl.belief'):
            text=state['messages'][-1]['content']
            req=requirements(text,state.get('requirements'))
            if (state.get('belief') or {}).get('last_action')=='ASK_BUDGET':
                match=re.fullmatch(r'\s*\$?([\d,]+)(?: dollars)?\s*[.!]?\s*',text)
                if match:req['budget']=float(match[1].replace(',',''))
            previous=None if 'start over' in text.lower() else state.get('belief')
            return {'requirements':req,'belief':update_belief(previous,req,text)}
    def policy(state):
        with tracer.start_as_current_span('hrl.strategy'):
            decision=decide(vector(state['belief']),os.getenv('SALES_STRATEGY_POLICY'))
            selected=decision['action'];text=state['messages'][-1]['content'].lower();override=None
            if re.search(r'\b(stop|leave me alone|not interested|no thanks|do not recommend)\b',text):selected='END_CONVERSATION';override='customer_declined'
            elif 'compare' in text or 'difference' in text:selected='COMPARE_PRODUCTS';override='explicit_comparison'
            elif 'cheaper' in text or 'expensive' in text:selected='HANDLE_PRICE_OBJECTION';override='explicit_price_objection'
            elif any(w in text for w in ["don't like",'dont like','dislike','not that one']):selected='SHOW_ALTERNATIVE';override='customer_rejected_recommendation'
            elif re.search(r'\b(trust|reliable|reliability|warranty|legit|source)\b',text):selected='HANDLE_TRUST_OBJECTION';override='explicit_trust_question'
            elif re.search(r'\b(why|worth it|good about|value|convince me)\b',text):selected='EXPLAIN_VALUE';override='explicit_value_question'
            elif re.search(r'\b(specs?|feature|how (?:does|is)|tell me more|battery|display|camera)\b',text):selected='EXPLAIN_FEATURE';override='explicit_feature_question'
            elif re.search(r'\b(not sure|unsure|thinking about it|hesitant)\b',text):selected='EXPLAIN_VALUE';override='customer_uncertain'
            if selected.startswith('ASK_') and selected in state['belief']['asked']:
                selected='RECOMMEND_PRODUCT';override='avoid_repeated_question'
            return {'strategy':selected,'debug':{'strategy_policy':decision,'executed_action':selected,'override':override}}
    def tools(state):
        with tracer.start_as_current_span('hrl.product_tools'):
            action=state['strategy'];products=[] if action=='END_CONVERSATION' else retrieve(state['requirements'])
            products=[p for p in products if p['id'] not in state['belief'].get('rejected_products',[])]
            if action in ['DOWNSELL','HANDLE_PRICE_OBJECTION','SHOW_ALTERNATIVE']:products=sorted(products,key=lambda p:p['price'])
            actions=[]
            if products and not action.startswith('ASK_') and action not in ['WAIT','END_CONVERSATION']:
                actions=[{'type':'compare' if action=='COMPARE_PRODUCTS' else 'highlight','product_ids':[p['id'] for p in products[:2 if action=='COMPARE_PRODUCTS' else 1]]}]
            b=state['belief'];b['last_action']=action
            if action.startswith('ASK_'):b['asked']=(b['asked']+[action])[-20:]
            if actions:b['shown']=True;b['products_shown']=list(dict.fromkeys(b['products_shown']+[p['id'] for p in products]))[-18:];b['last_recommended']=products[0]['id']
            return {'products':products,'actions':actions,'belief':b}
    async def language(state):
        with tracer.start_as_current_span('hrl.language'):
            if state.get('skip_language'):
                reply,source='','groq_stream'
            else:
                reply,source=await realize(state['strategy'],state['belief'],state['products'],state['messages'],state['requirements'])
            debug={**state['debug'],'belief':state['belief'],'language_source':source,
                   'scope':'Experimental policies trained on synthetic customers; no real-world performance claim.'}
            return {'reply':reply,'debug':debug,'prediction':{'probability':None,'status':'replaced_by_action_policy','provenance':'none'}}
    g=StateGraph(ShoppingState)
    nodes=[('understand',understand),('strategy_policy',policy),('product_tools',tools),('language',language)]
    previous=START
    for name,fn in nodes:g.add_node(name,fn);g.add_edge(previous,name);previous=name
    g.add_edge(previous,END)
    return g.compile()
