"""Explicit shopper commands: validated catalog tools, shared by text and voice."""
import re
from .catalog import PRODUCTS, BY_ID
from .hrl.state import new_belief


def normalized(text):
    words=re.findall(r'[a-z0-9]+', text.lower())
    numbers={'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10'}
    return ' '.join(numbers.get(word,word) for word in words)


def named_products(text):
    text=' '+normalized(text)+' '
    matches=[]
    for p in PRODUCTS:
        for alias in [p['name'],p['id'],*p.get('aliases',[])]:
            needle=' '+normalized(alias)+' '
            start=text.find(needle)
            if start>=0:matches.append((p,start,start+len(needle)))
    # A longer model name wins over its prefix (AirPods 5 Wireless Case vs 5).
    exact=[]
    for p,start,end in matches:
        if not any(a<=start and b>=end and b-a>end-start for _,a,b in matches) and p not in exact:exact.append(p)
    if exact:return exact
    # STT may join brand/model words or spell "phone" phonetically. Require a
    # complete catalog name (including its model number), not fuzzy similarity.
    compact=lambda value:normalized(value).replace(' ','').replace('phone','fone')
    joined=[p for p in PRODUCTS if compact(p['name']) in compact(text)]
    if joined:return joined
    return []


def command(text,state):
    t=normalized(text)
    add=bool(re.search(r'\b(add|put|place)\b',t))
    remove=bool(re.search(r'\b(remove|delete|take out)\b',t))
    cart=bool(re.search(r'\b(cart|basket|bag)\b',t))
    show=bool(re.search(r'\b(show|open|view|see|display|navigate|go|bring|check)\b',t))
    if re.search(r'\b(don t|do not|dont|never)\b',t):return None
    targets=named_products(text)
    actions=[];reply=None;focus=None
    page_match=re.search(r'\b(deal of the day|sales|categories|home page)\b',t)
    if show and page_match and not cart and not add and not remove:
        page={'deal of the day':'/deals','sales':'/sales','categories':'/categories','home page':'/'}[page_match[1]]
        actions=[{'type':'navigate_page','path':page,'product_ids':[]}];reply='Opening '+page_match[1]+'.'
    elif (cart and re.search(r'\b(close|hide|dismiss)\b',t)) or re.search(r'\b(back to|return to)\s+(products|shopping|browsing)\b',t):
        actions=[{'type':'close_panels','product_ids':[]}];reply='Back to the products.'
    elif cart and show and not add and not remove:
        actions=[{'type':'open_cart','product_ids':[]}]
        count=sum(x['quantity'] for x in state['cart'])
        total=sum(BY_ID[x['product_id']]['price']*x['quantity'] for x in state['cart'])
        reply=f'Here is your cart. You have {count} items, totaling ${total:,.2f}.' if count else 'Here is your cart. It is empty right now.'
    elif add or (remove and (cart or targets)):
        if not targets:
            visible=state.get('view_ids',[])
            ordinal=re.search(r'\b(first|second|third)\b',t)
            if ordinal:
                index=['first','second','third'].index(ordinal[1]);pid=visible[index] if index<len(visible) else None
            elif re.search(r'\b(that|this|it)\b',t):pid=state.get('focused_product')
            else:pid=None
            if pid in BY_ID:targets=[BY_ID[pid]]
        if not targets:reply='Which product should I '+('remove' if remove else 'add')+'? Please say its name.'
        else:
            pending=[dict(x) for x in state['cart']]
            for product in targets:
                existing=next((x for x in pending if x['product_id']==product['id']),None)
                quantity=1
                match=re.search(r'\b(\d+|one|two|three|four|five|six)\s+(?:of\s+)?(?:the\s+)?'+re.escape(' '.join(normalized(product['name']).split()[:2])),t)
                if not match and len(targets)==1:match=re.search(r'\b(?:add|put|place)\s+(\d+)\b',t)
                if match:quantity=int(match[1]) if match[1].isdigit() else ['zero','one','two','three','four','five','six'].index(match[1])
                desired=0 if remove else quantity+(existing['quantity'] if existing else 0)
                if desired>min(5,product['stock']):
                    reply=f'I could not add those items. {product["name"]} exceeds the available stock or five-item limit.';break
                pending=[x for x in pending if x['product_id']!=product['id']]
                if desired:pending.append({'product_id':product['id'],'quantity':desired})
            if reply is None:
                state['cart']=pending
                reply=('Removed ' if remove else 'Added ')+', '.join(p['name'] for p in targets)+(' from' if remove else ' to')+' your cart.'
                actions=[{'type':'open_cart','product_ids':[]}]
    elif show and targets:
        focus=targets[0]['id'];actions=[{'type':'highlight','product_ids':[focus]}]
        reply=f'Here is {targets[0]["name"]}, priced at ${targets[0]["price"]:,.0f}. {targets[0]["description"]}'
    elif re.search(r'\b(next|previous|last)\s+(page|slide|products|options)\b',t):
        actions=[{'type':'navigate_products','direction':-1 if re.search(r'\b(previous|last)\b',t) else 1,'product_ids':[]}]
        reply='Moving to the '+('previous' if actions[0]['direction']<0 else 'next')+' page of products.'
    if reply is None:return None
    belief=state.get('belief') or new_belief();belief['cart']=bool(state['cart'])
    products=[BY_ID[i] for i in state.get('result_ids',state.get('view_ids',[])) if i in BY_ID]
    if focus and focus not in [p['id'] for p in products]:products=[targets[0]]+products
    return {'reply':reply,'products':products,'actions':actions,'requirements':state['requirements'],'belief':belief,
            'cart':state['cart'],'focus_product_id':focus,'strategy':'CUSTOMER_COMMAND','tool_reply':reply,
            'prediction':{'probability':None},'debug':{'strategy_policy':{'source':'explicit_customer_command'},'executed_action':'CUSTOMER_COMMAND','language_source':'tool_result'}}


def remember_result(state,result):
    state['result_ids']=[p['id'] for p in result['products']]
    focus=result.get('focus_product_id')
    if not focus:
        named=named_products(result.get('reply',''))
        focus=next((p['id'] for p in named if p['id'] in state['result_ids']),None)
    if not focus:
        focus=next((a['product_ids'][0] for a in result['actions'] if a['type']=='highlight' and a['product_ids']),None)
    if focus:state['focused_product']=focus;result['focus_product_id']=focus
    result['cart']=state['cart']
