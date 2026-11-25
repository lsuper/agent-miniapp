"""Daily-note-only synthesis; no quote refresh, new forecast or scoring."""
from pathlib import Path
import re,json,hashlib,subprocess,shutil
from datetime import datetime
REPO=Path('/Users/sluan/Projects/agent-miniapp')
old=(REPO/'build_summary_notes_20261124.py').read_text()
exec(old[:old.index('QUOTES={')].replace("DATE='2026-11-24'","DATE='2026-11-25'"))
base_horizon=horizon
def horizon(block,heading,rule):
 h=base_horizon(block,heading,rule);text=norm(heading+'\n'+block)
 target=re.search(r'(?:explicit|exact)\s+(?:target\s+)?session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I) or re.search(r'target\s+(?:(?:regular|closing)\s+)?session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 h['target_session']=target[1] if target else None
 close=re.search(r'(?:regular\s*)?closes?\s*:?\s*(\d{4}-\d{2}-\d{2}[T ][\d:.+-]+)',text,re.I)
 h['target_close']=close[1].rstrip('.') if close else None
 return h
QUOTES={
'NVDA':(146.5361,'08:03:12 EST','Yahoo; separate Google 146.30 at 08:01 EST.'),
'MU':(588.75,'08:16 EST','Google; earlier Yahoo 589.59 at 08:09:36 EST. Google regular 630.07 differs from authoritative note reference 629.79; preserve vendor difference.'),
'INTC':(52.25,'08:21 EST','Google; earlier Yahoo 52.2001 at 08:16:16 EST.'),
'ARM':(152.45,'08:29 EST','Google; earlier Yahoo 152.05 at 08:22:29 EST.'),
'ASML':(1268.49,'08:34 EST','Google; earlier Yahoo 1269.97 at 08:30:30 EST.'),
'TSM':(329.42,'08:52 EST','Google; earlier Yahoo minute 330.15 at 08:43 EST and quote-info 329.87 at 08:44:55 EST.'),
'SIMO':(126.20,'08:46:20 EST','Yahoo and Google agree on 126.20; older minute stream ends 07:58.'),
'NET':(274.40,'09:01 EST','Google; earlier Yahoo 273.45 at 08:57:54 EST.'),
'AMD':(382.68,'09:06:06 EST','Yahoo; separate Google 385.10 at 09:10 EST.'),
'QCOM':(161.65,'09:17 EST','Google; earlier Yahoo 161.08 at 09:10:17 EST.')}
BLURBS={
'NVDA':('Dell actual orders explicitly corroborate Rubin demand; higher system guidance is not NVIDIA revenue or collected cash.','RSI 39.5 / VEL5 +17.0 fade after the relief spike while the selected indication is down 5.69%.','Investigations, concentrated receivables, customer financing and margin pressure remain unresolved.'),
'MU':('New proxy seeks 35M additional compensation-plan reserves; TrendForce cuts industry forecasts while Dell supports server demand.','RSI 37.4 / VEL5 -0.2 flip back into weakness; the 629.79 reference versus Google 630.07 difference affects prior scoring.','NAND oversupply forecasts, financed customer exposure, capex and dilution can overwhelm HBM demand.'),
'INTC':('HP PC revenue grows 14% while units fall 29%; Dell describes PC refresh deferrals despite server strength.','RSI 36.2 / VEL5 +6.5 decelerate after an 8.15% completed-session loss; positive velocity is not live gap absorption.','Client-unit weakness, node costs, capital commitments and dilution threaten a self-funded turnaround.'),
'ARM':('Fresh physical-AI paper expands ecosystem evidence, not paid customer counts or financial guidance.','RSI 38.2 / VEL5 -1.8 show failed one-bar repair while broad indications turn red again.','License recognition versus royalty collections, merchant-chip acceptance and retention dilution remain risks.'),
'ASML':('Fresh Dutch opposition to MATCH is diplomacy, not enacted protection; Dell AI strength is not scanner backlog.','RSI 38.1 / VEL5 +3.2 fade while the selected indication falls about 5%; only two of five velocity bars are positive.','Export restrictions, system acceptance and cash-collection delays can frustrate structural EUV demand.'),
'TSM':('October asset-activity 6-K and tiny dividend denominator adjustment do not create a new fab budget; Texas recommendation remains nonbinding.','RSI 40.2 / VEL5 +4.5 coexist with a 5.66% indication decline; good output and falling stock prices are distinct.','Geopolitics, customer funding, overseas returns and collection risk persist; Texas projections are not binding awards.'),
'SIMO':('Dell storage demand contrasts with HP PC-unit weakness; Kioxia Gen3 prototype samples are scheduled March 2027, not production GA.','RSI 35.5 / VEL5 +1.0 fade after a 12% completed-session drop; residual positive velocity is not a durable floor.','Negative operating cash flow, financed inventory and uncertain paid ramps challenge adjusted-profit quality.'),
'NET':('Search for Agents launches in beta across plans; distribution is not yet disclosed paid adoption or revenue.','RSI 46.4 falls while VEL5 improves to +2.1; fragile repair conflicts with a fresh 4.49% negative indication.','Rival bundling, retained paid usage, compute returns, reliability and dilution remain cash-per-share tests.'),
'AMD':('Dell majority-of-new-orders language names NVIDIA; AMD systems are named separately without order dollars.','RSI 38.7 / VEL5 -7.9 worsen; the 382.68 indication is down 7.40%, weaker than all six sampled comparisons.','Receivables/inventory conversion, customer financing, conditional dilution and client-unit pressure threaten owner cash.'),
'QCOM':('New $65M special grant disclosure changes incentives, not guidance; maximum units are contingent and not insider buying.','RSI 47.0 / VEL5 +2.3 are fragile repair; Tuesday absorbed much of an earlier gap, warning against literal premarket extrapolation.','No disclosed FCF hurdle in special awards; handset erosion, concentrated silicon execution and capital returns constrain cash.')}
func=old[old.index('def build_card(t):'):old.index('\ncards=[build_card')]
start=func.index(" row=next(");end=func.index(" gate=re.search",start)
func=func[:start]+''' row=next((l for l in tech.splitlines() if re.match(r'^\\s*\\|?\\s*(?:2026-)?11-24[\\s|]',l)),None)
 if row:
  nums=re.findall(r'[-+]?\\d+(?:\\.\\d+)?',row.split('11-24',1)[1].replace(',','').replace('$',''))
  close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 else:
  def metric(pattern):
   m=re.search(pattern,tech,re.I);assert m,(t,pattern);return float(m[1])
  rsi=metric(r'RSI\\s*14\\s*[=:]?\\s*([-+]?\\d+(?:\\.\\d+)?)');vel=metric(r'VEL5\\s*[=:]?\\s*([-+]?\\d+(?:\\.\\d+)?)');delta=metric(r'Δ1\\s*[=:]?\\s*([-+]?\\d+(?:\\.\\d+)?)')
''' +func[end:]
func=func.replace("assert clock.replace(' ','') in s.replace(' ',''),(t,clock)","assert clock.replace(' ','') in s.replace(' ',''),(t,clock)")
func=func.replace("risk_score={'MU':30,'AMD':25}.get(t,0)","risk_score={'AMD':30,'MU':25}.get(t,0)").replace("bar_date='2026-11-23'","bar_date='2026-11-24'")
exec(func)
cards=[build_card(t) for t in TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
assert len(cards)==10 and all(c['today']['direction']=='down' for c in cards)
assert all(c['mytutopia']['rsi']<50 for c in cards)
bullets=[
'Full same-day coverage: all ten Today calls are down. Every selected premarket indication is red; this is broad de-risking, not independently verified issuer-specific order cancellation.',
f"All ten RSI readings remain below 50; {', '.join(neg)} have negative VEL5. Positive five-bar readings elsewhere retain the relief-spike base and do not prove today’s gap is absorbed.",
'No tactical opportunities qualify. Medium/long recovery theses remain conditional; do not relabel a bearish Today forecast as a buy simply because its annual thesis is constructive.',
'AMD and MU are highlighted cautions: AMD has worsening negative velocity and relative weakness; MU has renewed negative velocity, NAND pricing forecast cuts and new compensation-capacity optics. Editorial highlights, not quantified downside probabilities.',
'Fresh Dell actuals corroborate AI-server demand, with majority-of-new-orders Rubin attribution; Dell system dollars are not NVIDIA revenue, AMD backlog, TSM wafer orders or ASML scanner orders. HP PC revenue growth masks a 29% unit decline.',
'Issuer-specific deltas: NET Search for Agents distribution has no paid-adoption figure; QCOM awards are contingent compensation, not insider cash buying; ASML diplomacy is not enacted policy; TSM Texas recommendation is nonbinding; SIMO samples are not production.',
'Frozen quote clocks span 08:03–09:17 Eastern and are asynchronous, indicative snapshots—not live executable prices. MU retains its 629.79 reference despite Google’s 630.07 shell; no vendor switching to rescue yesterday’s miss.',
f"Close-window-v1: {len(violations)} cap violations across 30 capped windows; all 40 forecasts pending as published. Exact target-session close containment alone scores. December 25 rolls to December 28; annual Thanksgiving rolls to November 26, 2027 early close. Legacy cohorts stay separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Broad de-risking: all ten Today calls are down. Dell demand strengthens, but weak momentum and funding/cash questions dominate the tape.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, new research or scoring')
data['telegram_summary']=mod.telegram_summary(data)
prior=(REPO/'build_summary_notes_20261120.py').read_text();render=prior[prior.index('html=mod.build_html(data)'):prior.index('assert len(cards)==10')]
render=render.replace('caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure','caution highlights AMD relative weakness/cash-conversion exposure and MU memory-pricing/compensation exposure')
exec(render)
html=html.replace('<ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>','').replace("document.getElementById('marketBullets').innerHTML = bulletsHtml; ",'')
html=html.replace('today range ','target-close window ').replace('${esc(p.target_session)} · calendar','${esc(p.target_session)} (${esc(p.target_close)}) · calendar')
assert all(c['today']['target_session']==DATE for c in cards)
assert all(c[h]['target_session'] and c[h]['target_close'] for c in cards for h in ['today','30d','90d','1y'])
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1125-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
