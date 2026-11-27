"""Notes-only summary. No fresh research, forecasts, scoring or direct messaging."""
from pathlib import Path
from datetime import datetime
import json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
base=(REPO/'build_summary_notes_20261124.py').read_text()
exec(base[:base.index('QUOTES={')].replace("DATE='2026-11-24'","DATE='2026-11-27'"))
base_horizon=horizon
def horizon(block,heading,rule):
 h=base_horizon(block,heading,rule);text=norm(heading+'\n'+block)
 target=re.search(r'(?:explicit\s+(?:target\s+)?(?:(?:regular|closing)\s+)?session|target\s+(?:(?:regular|closing)\s+)?session)\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 h['target_session']=target[1] if target else None
 close=re.search(r'(?:regular\s+close|closing|closes?|close)\s*:?\s*(\d{4}-\d{2}-\d{2}[T ][\d:.+-]+)',text,re.I)
 h['target_close']=close[1].rstrip('.') if close else None
 cal=re.search(r'calendar target\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I) or re.search(r'nominal\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 h['calendar_target']=cal[1] if cal else None
 basis=re.search(r'^\s*-?\s*(?:range basis|basis):\s*(.+)$',text,re.I|re.M)
 h['range_basis']=basis[1] if basis else 'Regular-session close anchor explicitly stated in source note; premarket informs placement only.'
 return h
QUOTES={
'NVDA':(153.88,'08:11 EST','Google; separate Yahoo 154.10 at 08:02:51 EST.'),
'MU':(637.42,'08:16 EST','Google; separate earlier Yahoo 638.0197 at 08:10:51 EST.'),
'INTC':(56.83,'08:23:55 EST','Yahoo; separate Google 56.90 at 08:22 EST.'),
'ARM':(171.37,'08:29:09 EST','Yahoo; separate Google 171.87 at 08:30 EST.'),
'ASML':(1330.26,'08:35 EST','Google; separate Yahoo 1330.69 at 08:31:15 EST.'),
'TSM':(355.60,'09:02 EST','Google; separate Yahoo 355.10 at 08:42 EST.'),
'SIMO':(146.50,'08:52:14 EST','Yahoo; separate Google 146.50 at 08:52 EST. Yahoo captured at 08:56:29 EST.'),
'NET':(293.06,'08:58 EST','Google; separate Yahoo minute 293.00 at 08:58 and quote 293.01 at 08:59:01 EST.'),
'AMD':(422.55,'09:05 EST','Yahoo; separate Google 422.02 at 09:10 EST.'),
'QCOM':(173.90,'09:05:21 EST','Yahoo; separate Google 173.90 at 09:05 EST.')}
BLURBS={
'NVDA':('Newly recovered Dell Q&A adds customer underwriting evidence; proposed crypto-era settlement does not resolve current investigations.','RSI 37.5 / VEL5 +16.3 continue decelerating despite broad green indications.','Compliance reporting, concentrated receivables and customer credit remain unresolved; legal settlement is proposed, not final.'),
'MU':('Anthropic funding confirmation corrects old coverage; Dell content demand contrasts with PC unit weakness.','About +6% premarket relief conflicts with RSI 35.7 / VEL5 -1.3.','Negative velocity, conventional-memory pricing and labor mediation create risk; no fab shutdown was authenticated.'),
'INTC':('December 1/8/9 appearances remain checkpoints; no new financial or wafer-economics upgrade authenticated.','RSI 35.9 / VEL5 +6.5 retain repair after Wednesday’s deep intraday reversal, not a confirmed bottom.','Client absorption, manufacturing execution, capex and dilution can consume server-led gains.'),
'ARM':('New HPC and Infinity Nikki documents expand ecosystem evidence, not paid royalty or merchant orders.','RSI 38.2 / VEL5 -1.6 lack uptrend confirmation despite the strong relief indication.','Affiliate collections, merchant acceptance, shared R&D economics and retention dilution remain unproven.'),
'ASML':('Solidigm US-fab decision remains undetermined; Fouquet commentary and Dutch opposition are not enacted export relief.','RSI 36.3 / VEL5 displayed -0.0: stalled repair while ASML lags equipment peers.','Export access, Q4 acceptance/collections and deferred customer decisions remain risks.'),
'TSM':('Restricted-award capital registration implements an old cancellation, not a new buyback; Dell Q&A qualifies unit demand.','RSI 38.9 / VEL5 +2.1 weaken despite broad relief; Wednesday missed the prior ceiling by $0.34.','Customer credit, overseas returns and geopolitical/export constraints can overwhelm strong advanced-node demand.'),
'SIMO':('Kioxia originals clarify future GP2 samples; November 30 webcast is the next cash-conversion checkpoint.','RSI 36.6 / VEL5 +2.8 improve modestly as storage peers rebound.','Q3 operating cash flow -$256.110M and financed inventory challenge accounting growth; samples are not paid production.'),
'NET':('CLI/MCP paid activation reduces checkout friction; December 1 AI Search billing must produce retained paid usage.','RSI 45.3 / VEL5 -4.3 turn negative despite roughly +3.4% relief.','Negative velocity, recurring control-plane friction, compute commitments and SBC exceeding FCF threaten cash per share.'),
'AMD':('TokenSpeed recipes improve some serving points, but higher throughput can coexist with worse time-to-first-token.','RSI 38.0 / VEL5 -12.3 deteriorate despite roughly +4% green relief.','Worsening negative velocity, financed customers, receivables/inventory conversion and conditional dilution make the bounce fragile.'),
'QCOM':('Fresh local-agent memory tutorial is ecosystem evidence; December 1 UBS remains a future checkpoint.','RSI 49.6 / VEL5 +9.5 improve, but only three of the latest five velocity bars are positive.','Handset erosion, concentrated custom-silicon delivery and capital returns exceeding FCF constrain owner cash.')}
TICKERS=['NVDA','MU','INTC','ARM','ASML','TSM','SIMO','NET','AMD','QCOM']
def build_card(t):
 p=ROOT/t/(DATE+'.md')
 if not p.exists():
  prior=sorted(x for x in (ROOT/t).glob('????-??-??.md') if x.stem<DATE);p=prior[-1] if prior else None
 assert p is not None,t
 raw=p.read_text();s=norm(raw);rf=field(s,'reference_price')
 if rf:ref=float(rf)
 else:
  m=re.search(r'Reference:?\s*\$([\d,]+(?:\.\d+)?)',s,re.I);assert m,t;ref=float(m[1].replace(',',''))
 hs={};pred=section(s,'^Predictions$')
 for m in re.finditer(r'^### ([^\n]+)\n([\s\S]*?)(?=^### |\Z)',pred,re.M):
  heading=m[1].lower();k='today' if heading.startswith('today') else '30d' if heading.startswith('30') else '90d' if heading.startswith('90') else '1y' if heading.startswith('1') else None
  if k:hs[k]=horizon(m[2],m[1],'close-window-v1' if 'close-window-v1' in s else 'n/a')
 assert set(hs)=={'today','30d','90d','1y'},(t,hs)
 tech=section(s,'Mytutopia technical check')
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-25[\s|]',l)),None)
 if row:
  nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-25',1)[1].replace(',','').replace('$',''))
  close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 else:
  m=re.search(r'RSI\s*\(?14\)?\s*[=:;]?\s*([-+]?\d+(?:\.\d+)?)\s*;?\s*[/,;]?\s*VEL5\s*([-+]?\d+(?:\.\d+)?)\s*;?\s*[/,;]?\s*Δ1\s*([-+]?\d+(?:\.\d+)?)',tech,re.I)
  assert m,(t,'technical metrics');rsi,vel,delta=map(float,m.groups())
 gate=re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',tech,re.I)
 price,clock,context=QUOTES[t]
 assert f'{price:.2f}' in s.replace(',',''),(t,price)
 assert re.sub(r'\s','',clock) in re.sub(r'\s','',s),(t,clock)
 for k,h in hs.items():
  assert h['low'] and 0<h['low']<=h['high'] and h['direction']!='n/a' and h['confidence'] is not None and h['target_session'] and h['target_close'] and h['thesis'],(t,k,h)
  h['window_width_fraction']=(h['high']-h['low'])/h['high'];h['max_window_width_fraction']={'today':.08,'30d':.15,'90d':.20}.get(k)
  h['contract_violation']=h['max_window_width_fraction'] is not None and h['window_width_fraction']>h['max_window_width_fraction']+1e-12
  h['source_block_sha256']=hashlib.sha256((h['target_session']+str(h['low'])+str(h['high'])).encode()).hexdigest()
 catalyst,unusual,risk=BLURBS[t]
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date') or '2026-11-25',current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=context+' Frozen November 27, asynchronous indicative observations; not live or executable prices.',pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-25',data_context='Completed November 25 bar; 24-hour advertised delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=mod.clean_text(section(s,'Historical calibration review')),adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Note-reported capture; not refreshed in summary',_opp_score=hs['today']['confidence'],_risk_score={'AMD':30,'NET':25}.get(t,0))
cards=[build_card(t) for t in TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
bullets=[
'Full same-day coverage: all ten Today calls lean up or flat-to-up on broad holiday relief. These are original premarket forecasts, not refreshed live recommendations. November 27 regular trading ends at 13:00 EST / 10:00 PST.',
f"Every completed-bar RSI remains below 50; negative VEL5 persists in {', '.join(neg)}. ASML velocity displays -0.0, effectively flat. A green gap is not confirmed trend repair.",
'Tactical opportunities by Today confidence among up-biased calls: SIMO 52/100 ($140–152) and QCOM 49/100 ($166–180). SIMO has modest oscillator repair; QCOM has stronger velocity. Confidence is subjective, not a calibrated return probability.',
'Highlighted risks: AMD velocity worsens to -12.3 despite green tape; NET flips to -4.3 while compute commitments, SBC and reliability require cash-per-share proof. Editorial caution highlights, not quantified loss probabilities.',
'Newly recovered Dell Q&A says server units declined while cores, memory and storage content rose. Strong system dollars do not equal proportional wafer/controller/scanner units or guaranteed collections. HP client-unit weakness remains a counterweight.',
'Publication and economics differ: NVIDIA proposed crypto settlement does not clear current compliance investigations; ASML diplomacy is not enacted relief; TSM capital registration is not a buyback; ARM/AMD/QCOM software evidence is not booked revenue.',
'Upcoming checks: SIMO November 30 webcast; multiple December 1 management events and NET billing; MU December 17 earnings and reported December 2/4 labor mediation. No new financial guide raise is established by the selected notes.',
f"Frozen quote clocks span 08:11–09:05:21 EST (NET separately 08:58); anchors and technical bars are November 25. {len(violations)} width violations across 30 capped windows; all 40 source forecasts remain pending. Exact-target regular-close containment only; legacy grades are separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Half-day relief, not an all-clear: all ten Today calls lean up; every RSI remains below 50. SIMO and QCOM lead tactical confidence; AMD and NET carry highlighted cautions.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities — low-conviction relief',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research, forecasts or scoring')
data['telegram_summary']=mod.telegram_summary(data)
prior=(REPO/'build_summary_notes_20261120.py').read_text();render=prior[prior.index('html=mod.build_html(data)'):prior.index('assert len(cards)==10')]
render=render.replace('caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure','caution highlights AMD worsening velocity/cash conversion and NET negative velocity/compute/dilution exposure')
exec(render)
html=html.replace('<ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>','').replace("document.getElementById('marketBullets').innerHTML = bulletsHtml; ",'')
html=html.replace('today range ','target-close window ').replace('${esc(p.target_session)} · calendar','${esc(p.target_session)} (${esc(p.target_close)}) · calendar')
html=html.replace('Confidence is subjective closing-window containment conviction','Confidence is source-reported subjective conviction (wording varies by note)')
assert len(cards)==len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert all(c['today']['direction'] in ['up','flat_to_up'] for c in cards)
assert not violations
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
assert json.loads(jp.read_text())['coverage']==coverage
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1127-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session'],c[h]['target_close']) for h in ['today','30d','90d','1y']])
