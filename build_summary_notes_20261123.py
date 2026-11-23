"""Notes-only November 23 synthesis: no research refresh or forecast issuance."""
from pathlib import Path
from datetime import datetime
import importlib.util,json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-23'
spec=importlib.util.spec_from_file_location('renderer',REPO/'build_daily_stock_summary.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
TICKERS=['NVDA','MU','INTC','ARM','ASML','TSM','SIMO','NET','AMD','QCOM']
def norm(s):return s.replace('**','').replace('`','').replace('−','-').replace('\u00a0',' ')
def section(s,pattern):
 for m in re.finditer(r'^## ([^\n]+)\n([\s\S]*?)(?=^## |\Z)',s,re.M):
  if re.search(pattern,m[1],re.I):return m[2].strip()
 return ''
def field(s,key):
 m=re.search(r'^'+key+r':\s*(.+)$',s,re.M);return m[1].strip(' \"\'') if m else None

def horizon(block,heading,rule):
 text=norm(heading+'\n'+block)
 dm=re.search(r'\b(flat[_ -]to[_ -]up|flat[_ -]to[_ -]down|neutral|flat|up|down)\b',text,re.I)
 direction=mod.parse_direction(dm[1]) if dm else 'n/a'
 cm=re.search(r'\b(\d{1,3})\s*/\s*100\b',text)
 # First currency-anchored range is the published endpoint window, never a date.
 rm=re.search(r'\$([\d,]+(?:\.\d+)?)\s*[-–—]\s*\$?([\d,]+(?:\.\d+)?)',text)
 low,high=map(lambda x:float(x.replace(',','')),rm.groups()) if rm else (None,None)
 def label(p):
  m=re.search(r'^\s*-?\s*(?:'+p+r')\s*:\s*(.+)$',text,re.I|re.M);return m[1].strip() if m else None
 explicit=re.search(r'explicit\s+(?:(?:target|regular|closing)\s+)?session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 target=explicit or re.search(r'target\s+(?:closing\s+)?(?:session|close)\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 cal=re.search(r'(?:target calendar date|calendar target(?: date)?)\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 return dict(direction=direction,confidence=int(cm[1]) if cm else None,low=low,high=high,thesis=label(r'(?:brief )?thesis'),range_basis=label('range basis|basis') or 'Published regular-close anchor; frozen premarket informs placement only.',drivers=[label(r'(?:key )?drivers')],falsifiers=[label('falsifiers')],target_session=target[1] if target else None,calendar_target=cal[1] if cal else None,scoring_rule=rule,status='pending / unscored (as published)')
QUOTES={
'NVDA':(135.75,'08:03:22 ET','Yahoo indication; Google separately 135.40 at 08:00 ET. This early note predates later AMD-note leadership news.'),
'MU':(626.79,'08:12:01 EST','Yahoo indication; Google separately 626.79 at 08:17 EST'),
'INTC':(54.39,'08:17:09 EST','Yahoo indication; Google separately 54.46 at 08:20 EST'),
'ARM':(165.75,'08:30:22 EST','Yahoo indication; Google separately 165.69 at 08:28 EST'),
'ASML':(1342.12,'08:30:38 EST','Yahoo indication; Google separately 1344.72 at 08:38 EST'),
'TSM':(337.50,'08:44 EST','Yahoo indication; Google separately 337.08 at 08:46 EST'),
'SIMO':(141.0,'08:56 EST','Google Finance indication; earlier Yahoo 140 at 08:21 EST'),
'NET':(289.7112,'08:58:43 EST','Yahoo indication; Google separately 288.26 at 08:56 EST'),
'AMD':(456.0,'09:05:41 EST','Yahoo indication; Google separately 451.54 at 09:10 EST'),
'QCOM':(166.4645,'09:12:47 EST','Yahoo indication; Google separately 166.42 at 09:17 EST')}
BLURBS={
'NVDA':('Early note cites conditional political softening; later AMD note reports reinstatement. Keep issuance chronology, not a new NVIDIA forecast.','RSI 15.0 / VEL5 -9.8 deteriorated despite an early 8% indication; deeply oversold is not trend confirmation.','Investigation, concentrated receivables, customer financing and collection quality remain unresolved; the early note misses later leadership evidence.'),
'MU':('December 17 results remain the operating checkpoint; no new issuer guide authenticated in the selected note.','RSI 29.5 / VEL5 -12.9 worsen despite a 5.43% indication; ATR exceeds the entire closing window.','Customer-credit exposure, NAND pricing disagreement and inventory/capex conversion can undermine apparent low-multiple value.'),
'INTC':('Prior signed unnamed 18A-P customer and Microsoft EMIB/Xeon evidence are not another fresh award.','A 6% indication still fails to reclaim Thursday; RSI 28.0 and VEL5 -4.4 deteriorated.','Node delays, capex and dilution without recurring outside-customer margins can frustrate a self-funded recovery.'),
'ARM':('Note reports Haas retention through 2033 and SoftBank vice-chair role from December 1; no new financial guide.','Relative premarket strength coexists with RSI 31.8 / VEL5 -8.8 and Friday closing-window failure.','Supplier credit, inventory, royalty collections and dilution remain risks; dual-role governance does not prove cash improvement.'),
'ASML':('New weekly workbook reports 445,000 repurchased shares, allocated to employee plans; no new authorization.','Roughly 6% indication contrasts with RSI 28.9 / VEL5 -13.4; this is damaged-momentum relief.','Policy restrictions and accepted-system/collection delays remain risks; gross employee-plan buybacks are not permanent share shrinkage.'),
'TSM':('Named-management reporting says current order/shipment adjustments were not seen; not a filed revenue increase or future guarantee.','RSI 28.3 / VEL5 -17.0 deteriorate despite relief; price remains far below 20/50-session averages.','Customer credit, policy/geopolitics and overseas-margin dilution can offset genuine demand; worsening velocity leaves the rebound fragile.'),
'SIMO':('No new issuer operating packet; SK/Kioxia conversion and Micron calendar are coverage corrections, not new orders.','RSI 29.3 / VEL5 -9.5 weaken while broad green peers support a tentative bounce.','Negative operating cash flow and financed inventory challenge adjusted-profit quality and production-to-cash conversion.'),
'NET':('Note reports CRWD/ZS merger agreement as a competitive delta; NET adds developer features without a financial-guidance revision.','RSI 42.4 / VEL5 -8.0 worsen despite green tape; cyber breadth is deal-driven and mixed.','Stronger rival bundling, paid-retention/compute economics, insider-sale supply and control-plane reliability require scrutiny.'),
'AMD':('Later note reports NVIDIA reinstatement authenticated by a new 8-K; AMD governance filing and ROCm coverage are not new orders.','A 6–7% indication trails most peers after a 13.25% Friday loss; VEL5 repair is only marginal.','Customer investments consume cash; compliance, acceptance, collections, guarantees and dilution can overwhelm revenue growth.'),
'QCOM':('No authenticated operating upgrade; broad relief rather than a newly quantified award drives the note framing.','An 11% indication contrasts with RSI 35.1 / VEL5 -13.7; zero reported minute volume does not prove depth.','Capital returns exceed FCF with little net share shrinkage; handset erosion, customer concentration and debt overlap constrain owner cash.')}

def build_card(t):
 p=ROOT/t/(DATE+'.md')
 if not p.exists():
  prior=sorted(x for x in (ROOT/t).glob('????-??-??.md') if x.stem<DATE);p=prior[-1] if prior else None
 if p is None:raise RuntimeError('No available note for '+t)
 raw=p.read_text();s=norm(raw);ref=float(field(s,'reference_price'));pred=section(s,'^Predictions$');hs={}
 for m in re.finditer(r'^### ([^\n]+)\n([\s\S]*?)(?=^### |\Z)',pred,re.M):
  h=m[1].lower();key='today' if h.startswith('today') else '30d' if h.startswith('30') else '90d' if h.startswith('90') else '1y' if h.startswith('1') else None
  if key:hs[key]=horizon(m[2],m[1],field(s,'scoring_rule') or 'n/a')
 assert set(hs)=={'today','30d','90d','1y'},(t,hs)
 tech=section(s,'Mytutopia technical check')
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-20[\s|]',l)),None)
 assert row,(t,'no latest row')
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-20',1)[1].replace(',','').replace('$',''))
 close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 gate=re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',tech,re.I) or re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',s,re.I)
 price,clock,qcontext=QUOTES[t]
 assert str(price).rstrip('0').rstrip('.') in s.replace(',','') or f'{price:.2f}' in s.replace(',',''),(t,price)
 assert clock.replace(' ','') in s.replace(' ','') or t=='NVDA',(t,clock)
 catalyst,unusual,risk=BLURBS[t]
 for k,h in hs.items():
  assert h['low'] and 0<h['low']<=h['high'] and h['direction']!='n/a' and h['confidence'] is not None and h['target_session'] and h['thesis'],(t,k,h)
  h['window_width_fraction']=(h['high']-h['low'])/h['high'];h['max_window_width_fraction']={'today':.08,'30d':.15,'90d':.20}.get(k)
  h['contract_violation']=h['max_window_width_fraction'] is not None and h['window_width_fraction']>h['max_window_width_fraction']+1e-12
 caltext=mod.clean_text(section(s,'Historical calibration review'))
 risk_score={'TSM':30,'NVDA':25}.get(t,0)
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=qcontext,pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-20',data_context='Completed bar; advertised 24-hour delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=caltext,adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no quote refresh',_opp_score=hs['today']['confidence'],_risk_score=risk_score)

cards=[build_card(t) for t in TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']]
bullets=[
f"Coverage {len(coverage['generated'])}/10; all {len(up)} Today calls lean up/flat-to-up, but all {len(neg)} completed VEL5 readings remain negative. Broad relief after Friday liquidation, not confirmed trend repair.",
'Quotes are frozen, asynchronous premarket snapshots from 08:00–09:17 Eastern, not current prices. Later peer observations are much stronger than early samples; do not merge them into one live board.',
'Important chronology: early NVDA/TSM notes did not establish reinstatement; the later AMD note reports a new NVIDIA 8-K accepted at 13:57:54 UTC. Preserve the early NVIDIA forecast and bounds; do not retrofit it to later news.',
'INTC and NET lead tactical containment-confidence ordering at 49/100; TSM ties at 49 but is third alphabetically. This is subjective window conviction, not expected upside or calibrated probability.',
'TSM has the most negative displayed VEL5; NVDA has RSI 15 and collection/governance uncertainty. Their caution highlights can coexist with up-biased bounce forecasts.',
'ARM retention is fresh management continuity, not new orders. ASML employee-plan repurchases are real execution but not guaranteed net share shrinkage; MU December 17 results remain the operating checkpoint.',
'NET notes report a CRWD/ZS merger agreement: fresh competitive context, not NET contract losses. SIMO negative cash conversion, AMD customer-funding outflows and QCOM returns above FCF remain owner-cash tests.',
f"Close-window-v1: {len(violations)} cap violations across 30 capped windows; all 40 horizons remain pending as published. Exact target-close containment only; legacy evaluations remain separate. No new research, scoring, widening or target shifts."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Broad relief, damaged momentum: all ten Today calls are up-biased, all ten completed VEL5 readings negative. Snapshot timing matters.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or new scoring')
data['telegram_summary']=mod.telegram_summary(data)
# Reuse only the renderer adaptations from the audited prior builder, not its old market data.
prior=(REPO/'build_summary_notes_20261120.py').read_text()
render=prior[prior.index('html=mod.build_html(data)'):prior.index('assert len(cards)==10')]
render=render.replace('caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure','caution highlights TSM damaged momentum/policy-credit exposure and NVDA governance/collection exposure')
exec(render)
html=html.replace('No tactical opportunities: all Today calls are down.','No up-biased tactical opportunities in the available source notes.')
html=html.replace('<ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>','')
html=html.replace('today range ', 'target-close window ')
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
# Avoid a removed duplicate bullet-list element breaking the shared renderer.
html=html.replace("document.getElementById('marketBullets').innerHTML = bulletsHtml; ", '')
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1123-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
