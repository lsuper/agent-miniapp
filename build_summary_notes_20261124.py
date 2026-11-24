"""Notes-only synthesis. Preserve published forecast contracts; never issue or score."""
from pathlib import Path
from datetime import datetime
import importlib.util,json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-24'
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
 cm=re.search(r'\b(\d{1,3})\s*/\s*100\b',text)
 rm=re.search(r'\$([\d,]+(?:\.\d+)?)\s*[-–—]\s*\$?([\d,]+(?:\.\d+)?)',text)
 low,high=map(lambda x:float(x.replace(',','')),rm.groups()) if rm else (None,None)
 def label(p):
  m=re.search(r'^\s*-?\s*(?:'+p+r')\s*:\s*(.+)$',text,re.I|re.M);return m[1].strip() if m else None
 target=re.search(r'(?:explicit|exact)\s+(?:target\s+)?session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I) or re.search(r'target\s+(?:closing\s+)?(?:session|close)\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 cal=re.search(r'(?:target calendar date|calendar target(?: date)?)\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 close=re.search(r'(?:regular close|closes?|closing)\s*:?\s*(\d{4}-\d{2}-\d{2}T[\d:.+-]+)',text,re.I)
 return dict(direction=mod.parse_direction(dm[1]) if dm else 'n/a',confidence=int(cm[1]) if cm else None,low=low,high=high,thesis=label(r'(?:brief )?thesis'),range_basis=label('range basis|basis') or 'Published regular-close anchor; frozen premarket informs placement only.',drivers=[label(r'(?:key )?drivers')],falsifiers=[label('falsifiers')],target_session=target[1] if target else None,target_close=close[1] if close else None,calendar_target=cal[1] if cal else None,scoring_rule=rule,status='pending / unscored (as published)')
QUOTES={
'NVDA':(155.92,'08:11 EST','Google Finance; earlier Yahoo 157.523 at 08:02:44 EST.'),
'MU':(657.23,'08:12 EST','Google Finance; separate Yahoo 660 at 08:11:03 EST.'),
'INTC':(55.95,'08:21 EST','Google Finance; separate Yahoo 55.70 at 08:16:23 EST. Indication is below the published Today lower bound.'),
'ARM':(168.24,'08:26:03 EST','Yahoo; separate Google 168.21 at 08:30 EST.'),
'ASML':(1344.27,'08:32 EST','Google Finance; earlier Yahoo 1345.86 at 08:29:18 EST.'),
'TSM':(353.60,'08:49 EST','Google Finance; separate Yahoo 353.95 at 08:44 EST.'),
'SIMO':(144.26,'08:11:39 EST','Stale Yahoo indication, unchanged on 08:58 retrieval. Google showed prior close, not a fresh premarket print.'),
'NET':(281.50,'09:02 EST','Google Finance; stale Yahoo 282.01 at 08:45 EST, acquired 08:58:28 EST.'),
'AMD':(430.00,'09:13:31 EST','Yahoo; separate Google 426.55 at 09:10 EST and earlier Yahoo 427.43 at 09:06:32 EST.'),
'QCOM':(160.3209,'09:11:55 EST','Yahoo; separate Google 160.32 at 09:11 EST.')}
BLURBS={
'NVDA':('Reinstatement is now statutory evidence; independent/government investigations continue and the operating guide is unchanged.','RSI 42.9 / VEL5 +20.2 ignite after Monday +31.48%, while the frozen Google indication gives back 5.53%.','Continuing investigations, receivables concentration, customer financing and margin pressure remain unresolved.'),
'MU':('December 17 results remain the operating checkpoint; the note attributes a 2028 price-risk scenario to secondary Goldman coverage, not MU guidance.','RSI 42.5 / VEL5 +4.4 repair contrasts with a 7.13% indication decline after Monday +19.04%.','Conventional-memory pricing, customer credit and capex/collections can offset contracted HBM growth.'),
'INTC':('New management-access dates December 1/8/9 and Viettel production-use evidence are checkpoints, not a financial upgrade.','RSI 39.9 / VEL5 +10.0 ignition supports the recovery-close scenario, but the 55.95 indication is already below the 57.50 lower bound.','Failed gap absorption, weak external-customer margins, node delays, capex and dilution threaten owner cash.'),
'ARM':('New 6-K adds shareholder approval for elements of Haas retention; costs, dilution and meeting date are not disclosed.','RSI 42.0 / VEL5 +5.6 improve while the 168.24 indication falls 4.77%; completed repair is not live confirmation.','Undisclosed retention economics, governance, acceptance delays and weak royalty/cash conversion remain risks.'),
'ASML':('New repurchase release confirms the already-known 445,000-share workbook; no incremental execution or new authorization.','RSI 40.9 / VEL5 +4.6 ignition underpins a low-conviction recovery call despite a 2.86% red indication.','Export-policy pressure, scanner acceptance and collection delays can defeat recovery; employee-plan allocation is not automatic cancellation.'),
'TSM':('Recovered Texas incentive application is a conditional proposal, not approved construction or an added 2026 budget commitment.','RSI 43.1 / VEL5 +4.4 repair remains fragile; the 353.60 indication is down 2.75% after Monday relief.','Policy/customer-credit exposure and overseas capital-return hurdles persist; Texas is not guaranteed growth.'),
'SIMO':('New 6-K changes executive-office address, not capex or guidance; November 30 management commentary remains a checkpoint.','RSI 40.0 / VEL5 +4.2 improve, but the 144.26 indication is explicitly stale and peers are red.','Negative operating cash flow, financed inventory, collection risk and unproven paid ramps challenge profit quality.'),
'NET':('Fresh rival documents sharpen planned CRWD/ZS integration competition; NET changelogs are not paid-adoption or guide upgrades.','RSI 47.5 / VEL5 +0.7 are fragile repair, while Google indication is down 3.31%; regional incidents are not a global Workers outage.','Rival bundling, infrastructure returns, retained paid consumption, dilution and reliability can impair per-share cash.'),
'AMD':('New S-3ASR registers 336.934M possible resale shares, including existing conditional warrants; not new cash or executed selling.','RSI 42.6 / VEL5 -4.2 improve but remain negative; latest note indication is down 5.17%.','Conditional resale/dilution, customer funding, receivables and inventory conversion can overwhelm earnings growth.'),
'QCOM':('No new guide upgrade; two ownership filings describe one planned 628-share sale, not incremental operating weakness.','RSI 47.3 / VEL5 +1.3 sharply repair, but the 160.3209 indication is down 3.06%; the SELLING label persists.','Handset erosion, concentrated custom-silicon execution, financing overlap and returns exceeding FCF constrain owner cash.')}

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
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-23[\s|]',l)),None)
 assert row,(t,'no latest row')
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-23',1)[1].replace(',','').replace('$',''))
 close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 gate=re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',tech,re.I) or re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',s,re.I)
 price,clock,qcontext=QUOTES[t]
 assert f'{price:.2f}' in s.replace(',','') or str(price) in s.replace(',',''),(t,price)
 assert clock.replace(' ','') in s.replace(' ',''),(t,clock)
 catalyst,unusual,risk=BLURBS[t]
 for k,h in hs.items():
  assert h['low'] and 0<h['low']<=h['high'] and h['direction']!='n/a' and h['confidence'] is not None and h['target_session'] and h['thesis'],(t,k,h)
  h['window_width_fraction']=(h['high']-h['low'])/h['high'];h['max_window_width_fraction']={'today':.08,'30d':.15,'90d':.20}.get(k)
  h['contract_violation']=h['max_window_width_fraction'] is not None and h['window_width_fraction']>h['max_window_width_fraction']+1e-12
 caltext=mod.clean_text(section(s,'Historical calibration review'))
 risk_score={'MU':30,'AMD':25}.get(t,0)
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=qcontext+' All observations are asynchronous and indicative, not live executable prices.',pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-23',data_context='Completed bar; advertised 24-hour delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=caltext,adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no quote refresh',_opp_score=hs['today']['confidence'],_risk_score=risk_score)

cards=[build_card(t) for t in TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']]
down=[c['ticker'] for c in cards if c['today']['direction'] in ['down','flat_to_down']]
assert len(up)+len(down)==10
bullets=[
f"Coverage {len(coverage['generated'])}/10. {len(down)} Today calls lean down/flat-to-down; only {', '.join(up)} lean flat-to-up. All ten selected indications are red after Monday's relief surge: broad retracement, not isolated issuer deterioration.",
f"Completed November 23 momentum has repaired: {10-len(neg)} positive VEL5 readings, with only {', '.join(neg)} still negative. All ten RSI readings remain below 50. Delayed repair and fresh red tape can coexist.",
'ASML (43/100, $1,325–1,440) and INTC (37/100, $57.50–62.50) are low-conviction recovery-close opportunities, not clean momentum buys. Intel’s selected 55.95 indication is below its published lower bound; no retrospective rebasing.',
'MU is a highlighted caution: the selected indication is down 7.13% and secondary 2028 conventional-memory price scenarios challenge the valuation narrative. AMD remains negative-VEL5, with conditional resale and cash-conversion exposure. Highlights are editorial, not measured downside odds.',
'NVIDIA reinstatement is now officially authenticated in the notes, but investigations continue. Timing differs: early prior notes predated the filing; SIMO explicitly corrects a prior coverage omission. Leadership continuity is not exoneration, new orders or stronger collections.',
'New does not always mean incremental economics: ASML release repeats known buybacks, SIMO 6-K changes office address, QCOM filings describe one planned sale. Arm retention adds shareholder approval; TSM Texas application remains conditional; NET rival documents sharpen bundling competition.',
'Quote clocks span 08:11–09:13 Eastern and are frozen historical premarket snapshots, not current prices. SIMO and Yahoo NET indications are explicitly stale; preserve separate feed clocks, never synthesize a synchronized board.',
f"Close-window-v1: {len(violations)} cap violations across 30 capped windows; all 40 forecasts pending as published. Only inclusive exact-target regular-close containment counts. Preserve legacy scores separately; no new scoring, widened bounds or shifted targets."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Relief retraces: eight defensive Today calls; ASML and INTC alone lean toward recovery. Completed momentum improves, but all ten RSI readings remain below 50.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities — low-conviction recovery',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or new scoring')
data['telegram_summary']=mod.telegram_summary(data)
prior=(REPO/'build_summary_notes_20261120.py').read_text()
render=prior[prior.index('html=mod.build_html(data)'):prior.index('assert len(cards)==10')]
render=render.replace('caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure','caution highlights MU conventional-memory/customer-credit exposure and AMD conditional-resale/cash-conversion exposure')
exec(render)
html=html.replace('<ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>','')
html=html.replace("document.getElementById('marketBullets').innerHTML = bulletsHtml; ", '')
html=html.replace('today range ', 'target-close window ')
html=html.replace('${esc(p.target_session)} · calendar', '${esc(p.target_session)} (${esc(p.target_close)}) · calendar')
html=html.replace('Source: Obsidian daily-stock research notes only.', 'Source: Obsidian daily-stock research notes only.')
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1124-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
