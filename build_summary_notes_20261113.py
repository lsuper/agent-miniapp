"""Notes-only dashboard; never imports ledger values or issues forecasts."""
from pathlib import Path
from datetime import datetime
import importlib.util, json, re, hashlib, subprocess, shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-13'
spec=importlib.util.spec_from_file_location('renderer',REPO/'build_daily_stock_summary.py'); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
TICKERS=mod.TICKERS

def norm(s): return s.replace('**','').replace('`','').replace('−','-').replace('\u00a0',' ')
def section(s, pattern):
 for m in re.finditer(r'^## ([^\n]+)\n([\s\S]*?)(?=^## |\Z)',s,re.M):
  if re.search(pattern,m[1],re.I): return m[2].strip()
 return ''
def field(s,key):
 m=re.search(r'^'+key+r':\s*(.+)$',s,re.M);return m[1].strip(' \"\'') if m else None

def horizon(block,heading,rule):
 text=norm(heading+'\n'+block)
 d=re.search(r'\b(flat_to_up|flat_to_down|neutral|flat|up|down)\b',text,re.I)
 c=re.search(r'\b(\d{1,3})\s*/\s*100\b',text)
 range_lines=[l for l in text.splitlines() if re.search(r'(?:closing.*(?:range|window)|expected.*range|\d+/100.*\$)',l,re.I)]
 low=high=None
 for line in range_lines:
  m=re.search(r'\$([\d,]+(?:\.\d+)?)\s*[-–—]\s*\$?([\d,]+(?:\.\d+)?)',line)
  if m: low,high=[float(x.replace(',','')) for x in m.groups()];break
 assert low is not None and 0<low<=high, (heading,range_lines)
 def label(p):
  m=re.search(r'^\s*-?\s*(?:'+p+r')\s*:\s*(.+)$',text,re.I|re.M);return m[1].strip() if m else None
 target_patterns=[r'(?:explicit |exact |actual )?target session\s*[: ]+\s*(\d{4}-\d{2}-\d{2})',r'target (?:closing )?session\s+(\d{4}-\d{2}-\d{2})',r'explicit regular close:\s*(\d{4}-\d{2}-\d{2})',r'actual session\s+(\d{4}-\d{2}-\d{2})',r'target\s+(\d{4}-\d{2}-\d{2})\s+regular close']
 target=next((m[1] for p in target_patterns if (m:=re.search(p,text,re.I))),None)
 cal=re.search(r'calendar target(?: date)?\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 return {'direction':('flat' if d and d[1].lower()=='neutral' else d[1].lower() if d else 'n/a'),'confidence':int(c[1]) if c else None,'low':low,'high':high,'thesis':label(r'(?:brief )?thesis'),'range_basis':label(r'range basis|basis'),'drivers':[label(r'(?:key )?drivers')],'falsifiers':[label('falsifiers')],'target_session':target,'calendar_target':cal[1] if cal else None,'scoring_rule':rule,'status':'pending / unscored (as published)'}

# Explicit timestamped samples from each selected daily note. No fresh quotes.
QUOTES={
 'NVDA':(168.98,'08:08:19 EST','Yahoo indication; Google 168.82 at 08:07 EST'),
 'MU':(792.10,'08:10:27 EST','Yahoo indication; Google 791.71 at 08:08 EST'),
 'INTC':(60.85,'08:20 EST','Google Finance; Yahoo 60.90 at 08:16:16 EST'),
 'ARM':(198.72,'08:27:33 EST','Yahoo indication; Google 197.80 at 08:17 EST'),
 'ASML':(1506.00,'08:35 EST','Google Finance; earlier Yahoo 1494.50 at 08:30:01 EST'),
 'TSM':(409.58,'08:55 EST','Google Finance; Yahoo 410.80 at 08:44:29 EST'),
 'SIMO':(176.00,'08:53 EST','Final designated Google Finance indication; earlier samples superseded'),
 'NET':(326.00,'09:03:19 EST','Yahoo indication; Google 324.60 at 09:01 EST'),
 'AMD':(569.53,'09:11 EST','Google Finance; earlier Yahoo 571.666 at 09:04:53 EST'),
 'QCOM':(176.75,'09:03 EST','Google Finance; Yahoo 176.7513 at 09:03:04 EST')}
BLURBS={
 'NVDA':('November 17 earnings: leadership continuity, collections and paid Rubin acceptance are the proof gates.','Oversold RSI with positive five-bar velocity; relief bid contrasts with softer AMD/semiconductor indications.','Leadership transition and customer cancellability/funding exposure keep the rebound fragile.'),
 'MU':('Applied Materials results corroborate memory investment; November 18 management discussion is the next checkpoint.','VEL5 improves while the latest RSI bar slips; the five-bar repair is not a confirmed above-50 trend.','Customer funding and future competing memory supply can undermine pricing and terminal margins.'),
 'INTC':('RadixArk/SGLang collaboration expands inference enablement, not disclosed orders or guidance.','Five positive velocity bars coexist with RSI below 50 and a modest red indication.','PC contraction, Fab28 usable-output uncertainty and investment needs constrain the turnaround.'),
 'ARM':('Mobile CSS update and stronger external licensing add operating evidence, not a royalty guidance raise.','RSI and price fell while five-bar velocity rose; modest red indication lags some peers.','Demanding valuation, affiliate collections and merchant-chip margin/capacity obligations remain unresolved.'),
 'ASML':('AMAT results support equipment demand while highlighting cleanroom and component bottlenecks.','Later Google indication turned positive; RSI remains below 50 despite stronger VEL5.','Q4 acceptance/collection and physical fab-readiness constraints can delay revenue conversion.'),
 'TSM':('Fresh 6-K adds customer capacity-retention receipts and statutory operating detail.','Positive premarket plus VEL5 repair; latest RSI still deteriorated and remains below 50.','Refundable/offsettable capacity receipts are not irrevocable revenue; overseas execution and geopolitics remain risks.'),
 'SIMO':('Fresh SC26 release adds controller specifications and platform demos, without new financial guidance.','Final Google indication turned red despite positive VEL5; latest RSI change stays negative.','Persistent cash burn, inventory collection and qualification-to-production conversion remain the economic tests.'),
 'NET':('Workers/DO spending controls and clarified AI Search billing are fresh product changes, not booked revenue.','Five higher closes and VEL5 +25 support repair; some Workers reliability problems remain unresolved.','Memory-heavy startup errors, gross-margin pressure and extended rebound can interrupt upside repair.'),
 'AMD':('Versal security roadmap and MI430X details add product evidence, not a new guide or paid order.','Strong completed-bar velocity conflicts with red premarket after a sharp five-session rally.','Profit taking, lost relative strength and financing/dilution exposures challenge an extended rally.'),
 'QCOM':('Auto/data-center delivery and handset pricing must convert existing guidance into collected cash.','Five higher closes; large VEL5 increase with little RSI progress raises exhaustion/chop risk.','Handset substitution, data-center concentration and capital returns above FCF pressure per-share economics.')}

def build_card(t):
 p=ROOT/t/(DATE+'.md')
 if not p.exists():
  prior=sorted(x for x in (ROOT/t).glob('????-??-??.md') if x.stem<DATE);p=prior[-1] if prior else None
 if p is None: raise RuntimeError('No note for '+t)
 raw=p.read_text();s=norm(raw);fm,body=mod.extract_frontmatter(s)
 ref=float(field(s,'reference_price')); pred=section(s,'^Predictions$');rule=field(s,'scoring_rule') or ('close-window-v1' if 'close-window-v1' in pred else 'n/a')
 hs={}
 for m in re.finditer(r'^### ([^\n]+)\n([\s\S]*?)(?=^### |\Z)',pred,re.M):
  h=m[1].lower(); key='today' if h.startswith('today') else '30d' if h.startswith('30') else '90d' if h.startswith('90') else '1y' if h.startswith('1') else None
  if key: hs[key]=horizon(m[2],m[1],rule)
 assert set(hs)=={'today','30d','90d','1y'}, (t,hs)
 tech=section(s,'Mytutopia technical check')
 # Latest completed table row is authoritative over earlier prose transitions.
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-12[\s|]',l)),None)
 assert row, t
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-12',1)[1].replace(',','').replace('$',''))
 close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 gate=re.search(r'momentum[- ]?gate[- ]*(?:\s|:|/)*(buying|selling)',tech,re.I) or re.search(r'momentum[- ]?gate[- ]*(?:\s|:|/)*(buying|selling)',s,re.I)
 price,clock,quote_context=QUOTES[t]
 assert str(price).rstrip('0').rstrip('.') in s.replace(',','') or f'{price:.2f}' in s.replace(',',''),(t,price)
 catalyst,unusual,risk=BLURBS[t]
 for key,h in hs.items():
  assert h['direction']!='n/a' and h['confidence'] is not None and h['target_session'],(t,key,h)
  h['window_width_fraction']=(h['high']-h['low'])/h['high'];h['max_window_width_fraction']={'today':.08,'30d':.15,'90d':.20}.get(key)
  h['contract_violation']=h['max_window_width_fraction'] is not None and h['window_width_fraction']>h['max_window_width_fraction']+1e-12
 status='generated' if p.stem==DATE else 'stale'
 cal=section(s,'Historical calibration review')
 cal_lines=[l.strip(' -') for l in cal.splitlines() if re.search(r'legacy|binary|close-window|scorecards|cohort',l,re.I) and not l.startswith('#')]
 risk_score=({'down':30,'flat_to_down':22}.get(hs['today']['direction'],0)+max(0,(ref-price)/ref*100)*2)
 # Qualitative governance caution stays visible even when tactical direction is up-biased.
 if t=='NVDA':risk_score+=12
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status=status,note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=quote_context,pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-12',data_context='Completed bar; advertised 24-hour delay; not live oscillators'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note='\n'.join(cal_lines) or mod.clean_text(cal),adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no new quote/research retrieval',_opp_score=hs['today']['confidence'],_risk_score=round(risk_score,2))

cards=[build_card(t) for t in TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']];down=[c['ticker'] for c in cards if c['today']['direction'] in ['down','flat_to_down']]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
bullets=[
 f"Coverage: {len(coverage['generated'])}/10 same-day notes. Today: {len(up)} up/flat-to-up ({', '.join(up)}); {len(down)} down/flat-to-down ({', '.join(down)}).",
 'Selective repair, not broad risk-on: notes show NVDA/TSM relief and NET strength alongside weaker AMD and memory indications. Snapshots are asynchronous and premarket, not current live quotes.',
 'Every tracked latest completed-bar VEL5 is positive, but most RSI levels remain below 50. A better five-bar comparison does not imply the latest session accelerated.',
 'Applied Materials results strengthen the equipment/memory investment read-through; cleanroom readiness, shipment acceptance and collections remain separate gates for ASML, TSM and MU.',
 'NVIDIA succession and November 17 earnings are a cross-book uncertainty. Note-reported continuity assurances are not proof of unchanged orders; financing optionality is not proof of cancellations.',
 'AMD and SIMO are the leading tactical caution setups: profit taking/relative weakness for AMD, cash and qualification-to-production proof for SIMO. Positive VEL5 keeps rebound risk alive.',
 'NET has the clearest up call; product spending controls may improve adoption while constraining consumption. QCOM pairs resilience with velocity exhaustion and handset/cash-return pressure.',
 f"Close-window-v1: exact target-session close only; no partial credit or intraday rescue. {len(violations)} new-window violations found across 30 capped published windows; all remain pending as published. Legacy scorecards stay separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Selective repair: TSM and NET lead tactical setups; AMD and SIMO carry the sharpest same-day cautions.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or closing-price scoring')
data['telegram_summary']=mod.telegram_summary(data)
html=mod.build_html(data)
html=html.replace('Source: Obsidian daily-stock research notes and prediction ledgers.','Source: Obsidian daily-stock research notes only. All quotes are frozen premarket snapshots, not live prices. Exact closing windows are preserved; no new forecasts or scoring.')
html=html.replace("['flat_to_down','down','flat'].includes(card.today.direction)","['flat_to_down','down'].includes(card.today.direction)")
html=html.replace('<option value="ticker">Sort: ticker</option>','<option value="ticker">Sort: ticker</option><option value="company">Sort: company</option><option value="status">Sort: status</option><option value="direction">Sort: direction</option>')
html=html.replace("if(key === 'company') return a.company.localeCompare(b.company);","if(key === 'company') return a.company.localeCompare(b.company); if(key === 'status') return a.status.localeCompare(b.status); if(key === 'direction') return a.today.direction.localeCompare(b.today.direction);")
# Add provenance, snapshots and explicit contract details within every expanded card.
extra="""<div class="detail-box" style="margin-top:10px"><strong>Frozen quote / forecast contract</strong><p>${esc(card.current_time)} · ${esc(card.quote_context)} · reference ${esc(card.reference_date)}. Technical bar ${esc(card.mytutopia.bar_date)}; 24-hour advertised delay.</p>${['today','30d','90d','1y'].map(h=>{ const p=card[h];return `<p><strong>${esc(h.toUpperCase())}</strong>: target ${esc(p.target_session)} · calendar ${esc(p.calendar_target)} · ${esc(p.scoring_rule)} · ${esc(p.status)}<br>Width ${(p.window_width_fraction*100).toFixed(4)}% / cap ${p.max_window_width_fraction===null?'none':(p.max_window_width_fraction*100)+'%'} · ${p.contract_violation?'CONTRACT VIOLATION':'compliant'}<br>${esc(p.thesis)}</p>`;}).join('')}<p>No intraday-touch credit; direction is diagnostic. Only inclusive exact-target regular-close containment is a binary hit. No new scoring in this summary.</p></div>"""
html=html.replace('<details class="stock-details"><summary>Expand details</summary>','<details class="stock-details"><summary>Expand details</summary>'+extra)
# Expose exact serialized data for browser verification without relying on const-to-window behavior.
html=html.replace('const cards = APP_DATA.cards.slice();','window.__dailyStockData = APP_DATA;\nconst cards = APP_DATA.cards.slice();')
html=html.replace("document.getElementById('riskGrid').innerHTML = APP_DATA.top_risks.map(c => miniCard(c, 'risk')).join('');", "document.getElementById('riskGrid').innerHTML = APP_DATA.top_risks.map(c => miniCard(c, 'risk')).join('');")
html=html.replace("if(activeFilter === 'risk') return card.status === 'generated' && num(card._risk_score,0) > 0 && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';", "if(activeFilter === 'risk') return APP_DATA.top_risks.some(c=>c.ticker===card.ticker) && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';")
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert not violations,violations
assert all(c['today']['target_session']==DATE for c in cards)
assert next(c for c in cards if c['ticker']=='ARM')['90d']['target_session']=='2027-02-10'
# Public-safe: no secrets or full private filesystem paths in artifact.
html=html.replace('</script>','</script>')
assert 'TELEGRAM_BOT_TOKEN' not in html and '/Users/sluan' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if not script.strip():continue
 p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1113-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
# Stage only public artifacts, preserving all existing deployed content.
(REPO/'dist-pages').mkdir(exist_ok=True)
shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards: print(c['ticker'],c['reference_price'],c['current_price'],c['current_time'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
