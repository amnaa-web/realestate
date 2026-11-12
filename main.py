"""Demonstration property-matching API. Synthetic listings, deterministic ranking.
No OpenAI requests and no live MLS connectivity are used in this demo.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3, os, re, uuid
from datetime import datetime, timezone

app=FastAPI(title='NestMatch AI API', version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('ALLOWED_ORIGINS','*').split(','),allow_methods=['*'],allow_headers=['*'])
DB=os.getenv('DB_PATH',os.path.join(os.path.dirname(__file__),'leads.db'))

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    with conn() as c:
        c.execute('CREATE TABLE IF NOT EXISTS leads (id TEXT PRIMARY KEY,name TEXT,email TEXT,buyer_text TEXT,budget INTEGER,location TEXT,bedrooms INTEGER,status TEXT,property_ids TEXT,created_at TEXT)')
init()

LISTINGS=[
 {'id':'P-1001','title':'Sunlit Modern Townhome','location':'Austin','neighborhood':'East Austin','price':575000,'beds':3,'baths':2,'area':1840,'type':'Townhouse','tags':['parking','modern','school','yard'],'image':'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=900&q=80'},
 {'id':'P-1002','title':'Hill Country Family Haven','location':'Austin','neighborhood':'Cedar Park','price':689000,'beds':4,'baths':3,'area':2610,'type':'House','tags':['garage','garden','school','family'],'image':'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=900&q=80'},
 {'id':'P-1003','title':'Downtown Skyline Loft','location':'Austin','neighborhood':'Downtown','price':419000,'beds':2,'baths':2,'area':1210,'type':'Condo','tags':['downtown','walkable','balcony','modern'],'image':'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=900&q=80'},
 {'id':'P-1004','title':'Lakeview Contemporary','location':'Seattle','neighborhood':'Green Lake','price':820000,'beds':3,'baths':2,'area':2100,'type':'House','tags':['lake','parking','modern','garden'],'image':'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=900&q=80'},
 {'id':'P-1005','title':'Urban Garden Residence','location':'Seattle','neighborhood':'Ballard','price':645000,'beds':3,'baths':2,'area':1750,'type':'Townhouse','tags':['garden','school','parking','walkable'],'image':'https://images.unsplash.com/photo-1600573472591-ee6b68d14c68?w=900&q=80'},
 {'id':'P-1006','title':'Coastal Light Apartment','location':'Miami','neighborhood':'Brickell','price':530000,'beds':2,'baths':2,'area':1320,'type':'Condo','tags':['waterfront','balcony','pool','modern'],'image':'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=900&q=80'},
 {'id':'P-1007','title':'Palm Grove Family Home','location':'Miami','neighborhood':'Coral Gables','price':745000,'beds':4,'baths':3,'area':2450,'type':'House','tags':['family','school','parking','pool'],'image':'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=900&q=80'},
 {'id':'P-1008','title':'Riverside Starter Home','location':'Austin','neighborhood':'Riverside','price':349000,'beds':2,'baths':1,'area':990,'type':'House','tags':['parking','yard','affordable'],'image':'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=900&q=80'},
]

class MatchRequest(BaseModel):
    message:str=Field(min_length=3,max_length=1500)
class LeadRequest(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    email:str=Field(min_length=3,max_length=200)
    buyer_text:str=Field(min_length=3,max_length=1500)
    budget:Optional[int]=None
    location:Optional[str]=None
    bedrooms:Optional[int]=None
    property_ids:list[str]=[]

CITIES=['Austin','Seattle','Miami']
TAG_ALIASES={'parking':['parking','garage','car space'],'school':['school','schools','school district'],'garden':['garden','yard','backyard'],'walkable':['walkable','walking','walk to'],'pool':['pool','swimming'],'modern':['modern','contemporary'],'balcony':['balcony'],'waterfront':['waterfront','ocean','water view','beach','lake'],'downtown':['downtown','city center'],'family':['family','kids','children']}

def extract(text):
    t=text.lower()
    city=next((c for c in CITIES if c.lower() in t),None)
    budget=None
    # dollars: 650k, $650,000, $1.2m, under 700000
    m=re.search(r'(?:\$\s*)?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(k|m|million|thousand)?\b',t)
    for hit in re.finditer(r'(?:\$\s*)?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(k|m|million|thousand)?\b',t):
        num=float(hit.group(1).replace(',','')); suffix=hit.group(2)
        val=int(num*(1000000 if suffix in ('m','million') else 1000 if suffix in ('k','thousand') else 1))
        if val>=100000: budget=val; break
    bed=None
    bm=re.search(r'(\d+)\s*(?:\+\s*)?(?:bed(?:room)?s?|br)\b',t)
    if not bm:
        words={'one':1,'two':2,'three':3,'four':4,'five':5}
        bm2=re.search(r'\b(one|two|three|four|five)[ -]bed(?:room)?s?\b',t)
        if bm2: bed=words[bm2.group(1)]
    else: bed=int(bm.group(1))
    tags=[tag for tag,aliases in TAG_ALIASES.items() if any(a in t for a in aliases)]
    ptype=next((x for x in ['Condo','House','Townhouse'] if x.lower() in t or (x=='House' and 'home' in t)),None)
    return {'location':city,'budget':budget,'bedrooms':bed,'preferences':tags,'type':ptype}

def matches(pref):
    ranked=[]
    for x in LISTINGS:
        if pref['location'] and x['location']!=pref['location']:continue
        if pref['budget'] and x['price']>pref['budget']:continue
        if pref['bedrooms'] and x['beds']<pref['bedrooms']:continue
        if pref['type'] and x['type']!=pref['type']:continue
        overlap=[tag for tag in pref['preferences'] if tag in x['tags']]
        score=60+len(overlap)*12
        if pref['budget']:score+=max(0,12-int(12*x['price']/pref['budget']))
        if pref['bedrooms'] and x['beds']==pref['bedrooms']:score+=6
        ranked.append({**x,'score':min(99,score),'reasons':overlap or ['Matches your key criteria']})
    return sorted(ranked,key=lambda x:(-x['score'],x['price']))[:6]

@app.get('/api/health')
def health():return {'ok':True,'mode':'deterministic-demo'}
@app.get('/api/listings')
def listings():return LISTINGS
@app.post('/api/match')
def match(req:MatchRequest):
    pref=extract(req.message); result=matches(pref)
    missing=[field for field in ['location','budget','bedrooms'] if not pref[field]]
    if result:
        response=f"I found {len(result)} available demo listing{'s' if len(result)!=1 else ''} that fit your criteria. Here are the strongest matches."
    else:
        response='No demo listings meet every requested constraint. Try a higher budget, fewer bedrooms, or another city.'
    followup={'location':'Which city are you looking in — Austin, Seattle, or Miami?','budget':'What is your maximum budget?','bedrooms':'How many bedrooms do you need?'}
    return {'preferences':pref,'matches':result,'response':response,'follow_up':followup[missing[0]] if missing else 'Would you like an agent to contact you about these properties?'}
@app.post('/api/leads')
def create_lead(req:LeadRequest):
    if '@' not in req.email:raise HTTPException(422,'Enter a valid email')
    lid='L-'+uuid.uuid4().hex[:7].upper(); date=datetime.now(timezone.utc).isoformat()
    with conn() as c:
        c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?)',(lid,req.name,req.email,req.buyer_text,req.budget,req.location,req.bedrooms,'Warm lead',','.join(req.property_ids),date))
    return {'id':lid,'status':'Warm lead','created_at':date}
@app.get('/api/leads')
def get_leads():
    with conn() as c:rows=c.execute('SELECT * FROM leads ORDER BY created_at DESC').fetchall()
    return [dict(row) for row in rows]
