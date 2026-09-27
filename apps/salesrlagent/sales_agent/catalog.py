"""Catalog facts and strict, inspectable constraint retrieval."""
import json
import re
from pathlib import Path

PRODUCTS = json.loads((Path(__file__).parent / 'data/catalog.json').read_text(encoding='utf-8'))
BY_ID = {p['id']: p for p in PRODUCTS}


def requirements(text, previous=None):
    result = dict(previous or {})
    t = re.sub(r'(?<=\d),(?=\d{3})', '', text.lower())
    if re.search(r'\b(start over|reset search|anything)\b', t):
        result = {}
    categories = [
        ('phones', r'\b(phones?|smartphones?)\b'), ('tablets', r'\b(tablets?|ipads?)\b'),
        ('monitors', r'\b(monitors?|ultrawide)\b'), ('wearables', r'\b(watches|watch|wearables?|fitness bands?)\b'),
        ('speakers', r'\b(speakers?|soundbars?)\b'), ('accessories', r'\b(keyboards?|mice|mouse|docks?|hubs?|external (?:ssd|drives?))\b'),
        ('headphones', r'\bheadphones?\b'), ('earbuds', r'\b(earbuds?|earphones?|in[- ]ear|airpods?|buds)\b'),
        ('laptops', r'\b(laptops?|notebooks?|computers?)\b'), ('tvs', r'\b(tvs?|televisions?)\b'),
        ('gaming', r'\b(consoles?|gaming systems?|handhelds?)\b'), ('cameras', r'\b(cameras?|mirrorless|vlogging)\b'),
        ('smart home', r'\b(smart home|doorbells?)\b'), ('networking', r'\b(wifi|wi-fi|routers?|mesh)\b'),
        ('appliances', r'\b(appliances?|vacuums?|air fryers?)\b')]
    departments = [('audio', r'\baudio\b'), ('computers', r'\bcomputers?\b'),
                   ('home theater', r'\bhome theater\b'), ('smart home', r'\bsmart home\b')]
    for category, pattern in categories:
        if re.search(pattern, t):
            if result.get('category') != category:
                result.pop('features', None)
            result['category'] = category
            result.pop('department', None)
            break
    else:
        for department, pattern in departments:
            if re.search(pattern, t):
                result['department'] = department
                result.pop('category', None)
                break
    budget = re.search(r'(?:close to|near|around|about|under|below|up to|max(?:imum)?|budget(?: of| is)?)\s*\$?\s*(\d+(?:\.\d{1,2})?)', t)
    if budget:
        result['budget'] = float(budget.group(1))
        result.pop('target_price',None)
        if re.search(r'\b(close to|near|around|about)\b',t):result['target_price']=result['budget']
    if 'no budget' in t or 'any price' in t:
        result.pop('budget', None)
    features = set(result.get('features', []))
    feature_patterns = [
        ('noise cancelling', r'noise cancel\w*|\banc\b'), ('wireless', r'\bwireless\b|bluetooth'),
        ('water resistant', r'water\s*(?:proof|resistant)|sweat'), ('wired', r'\bwired\b'),
        ('4k', r'\b4k\b'), ('120hz', r'\b120\s*hz\b'), ('144hz', r'\b144\s*hz\b'),
        ('oled', r'\boled\b'), ('16gb ram', r'\b16\s*gb(?: ram)?\b'), ('32gb ram', r'\b32\s*gb(?: ram)?\b'),
        ('1tb storage', r'\b1\s*tb\b'), ('long battery', r'long battery|battery life'),
        ('portable', r'\bportable\b|lightweight'), ('smart home', r'\bsmart home\b'),
        ('self emptying', r'self[- ]emptying'), ('dual zone', r'dual[- ]zone')]
    for feature, pattern in feature_patterns:
        if re.search(pattern, t):
            if re.search(r'(?:no|without|don.t need)\s+(?:active\s+)?(?:' + pattern + ')', t):
                features.discard(feature)
            else:
                features.add(feature)
    result['features'] = sorted(features)
    known_uses = ['travel', 'running', 'music', 'studio', 'home', 'portable', 'school', 'work',
                  'gaming', 'creator', 'movies', 'family', 'pets', 'security', 'bright room', 'machine learning']
    found_uses = [use for use in known_uses if use in t]
    if found_uses:
        result['uses'] = found_uses
        result.pop('use', None)
    return result


def retrieve(req):
    candidates = [p for p in PRODUCTS if p['stock'] > 0
                  and (not req.get('category') or p['category'] == req['category'])
                  and (not req.get('department') or p.get('department') == req['department'])
                  and p['price'] <= req.get('budget', float('inf'))
                  and all(f in p['features'] for f in req.get('features', []))]
    uses = req.get('uses', [req['use']] if req.get('use') else [])
    def score(p):
        value=sum(use in p['features'] for use in uses)
        if 'machine learning' in uses and 'dedicated graphics' in p['features']:value+=2
        return (-value,abs(p['price']-req['target_price']) if req.get('target_price') is not None else p['price'])
    return sorted(candidates,key=score)[:3]
