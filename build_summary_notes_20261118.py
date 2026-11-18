"""2026-11-18 notes-only synthesis. No quotes fetched, no forecasts issued/scored."""
from pathlib import Path
from datetime import datetime
import importlib.util,json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-18'
spec=importlib.util.spec_from_file_location('renderer',REPO/'build_daily_stock_summary.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
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
 rm=re.search(r'\$([\d,]+(?:\.\d+)?)\s*[-–—]\s*\$?([\d,]+(?:\.\d+)?)',block)
 low,high=map(lambda x:float(x.replace(',','')),rm.groups()) if rm else (None,None)
 def label(p):
  m=re.search(r'^\s*-?\s*(?:'+p+r')\s*:\s*(.+)$',text,re.I|re.M);return m[1].strip() if m else None
 target=re.search(r'(?:target\s+(?:(?:closing\s+)?session\s+|close\s+|date/session\s+)?|explicit\s+(?:target\s+)?session\s+)(\d{4}-\d{2}-\d{2})',text,re.I)
 cal=re.search(r'calendar target(?: date)?\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 return dict(direction=direction,confidence=int(cm[1]) if cm else None,low=low,high=high,thesis=label(r'(?:brief )?thesis'),range_basis=label('range basis|basis'),drivers=[label(r'(?:key )?drivers')],falsifiers=[label('falsifiers')],target_session=target[1] if target else None,calendar_target=cal[1] if cal else None,scoring_rule=rule,status='pending / unscored (as published)')
QUOTES={
'NVDA':(159.62,'08:02:41 EST','Designated Yahoo indication; separate Google 159.11 at 08:08 EST'),
'MU':(724.90,'08:10:12 EST','Designated Yahoo indication; separate Google 724.24 at 08:21 EST'),
'INTC':(55.30,'08:16:15 EST','Yahoo indication; separate Google 55.33 at 08:20 EST'),
'ARM':(186.5604,'08:22:29 EST','Designated Yahoo indication; separate Google 187.30 at 08:28 EST'),
'ASML':(1400.98,'08:30:50 EST','Yahoo indication; separate Google 1404.02 at 08:38 EST'),
'TSM':(369.50,'08:44:09 EST','Designated Yahoo indication; separate Google 370.00 at 08:49 EST'),
'SIMO':(156.81,'08:51:36 EST','Yahoo-only indication; Google did not expose a premarket panel'),
'NET':(289.00,'09:03 EST','Google indication; separate Yahoo 288.8853 at 08:58:18 EST'),
'AMD':(512.50,'09:05:46 EST','Designated Yahoo indication; separate Google 511.96 at 09:10 EST'),
'QCOM':(167.00,'09:10:24 EST','Immutable Yahoo minute indication; later Google/vendor 167.30 at 09:13 EST')}
BLURBS={
'NVDA':('Actual Q3 earnings and Rubin shipments replace preview scenarios; Q4 guide includes a 14th week.','Oversold RSI22.5 with improving but negative VEL5 supports relief, not confirmed ignition.','DSO64, larger guarantees, guided margin compression and unresolved permanent succession qualify growth.'),
'MU':('NVIDIA multiyear memory procurement supports demand; supplier allocation is undisclosed.','Positive VEL5 +1.7 has stalled while RSI remains37.5; broad relief is not a breakout.','HBM mix is not automatically margin-accretive; labor, customer funding and future supply remain risks.'),
'INTC':('Government consortium designation is authenticated coverage correction, not a new dollar award.','Four declining closes and tiny green indication lag peers despite eight positive VEL5 bars.','Oversold RSI29.7 is not a bottom; Fab28 output, external awards and capital needs remain unproven.'),
'ARM':('Cobalt200 VMs reach GA in14 regions, advancing existing CSS adoption rather than merchant-chip revenue.','RSI40/VEL5+4.7 repair supports tentative continuation but the recent whipsaw limits confidence.','Demanding valuation, contract-asset collections, merchant margins and future capacity advances remain unresolved.'),
'ASML':('NVIDIA actual shipments/guide support equipment demand; no new ASML guidance authenticated.','Green premarket lags leading peers as RSI34.9 and VEL5-7.8 deteriorate.','Customer financing, cleanroom/acceptance timing and delayed pricing benefits can impede conversion.'),
'TSM':('NVIDIA shipments and Cobalt GA support conversion; director bought about$0.5M of ADS personally.','Nearly3% indicative bounce conflicts with RSI35.7/VEL5-8.4 and prior relative weakness.','Deteriorating momentum, overseas execution and conditional customer funding threaten a durable rebound.'),
'SIMO':('NVIDIA demand relief supports the sector; no fresh SIMO operating guide or collections result authenticated.','Yahoo indication rises3.14% while RSI34.5/VEL5-2.5 worsen; Google premarket unavailable.','Large operating cash outflow and qualification-to-production conversion challenge adjusted-profit growth.'),
'NET':('AI Search summaries add separately billed inference; Artifacts billing starts November19.','Green indication conflicts with RSI44.4/VEL5-6.6; PANW results arrive after this cash close.','Japan R2 investigation, billing friction, margin pressure and resolver jurisdiction risk qualify growth.'),
'AMD':('NVIDIA earnings support sector relief; Neysa deployment improves evidence without disclosed AMD economics.','Green indication does not lead peers; RSI46.6/VEL5-2.0 remain fragile and worsening.','Customer financing, acceptance delays, guarantees and dilution can outrun per-share cash generation.'),
'QCOM':('Official WARN detail quantifies known restructuring; startup article is ecosystem reach, not revenue.','Small green indication lags peers while RSI44.7 and VEL5-5.2 worsen.','Handset substitution, negative momentum, concentrated DC execution and weak net share shrink remain risks.')}

def build_card(t):
 p=ROOT/t/(DATE+'.md')
 if not p.exists():
  prior=sorted(x for x in (ROOT/t).glob('????-??-??.md') if x.stem<DATE);p=prior[-1] if prior else None
 if p is None:raise RuntimeError('No note for '+t)
 raw=p.read_text();s=norm(raw);ref=float(field(s,'reference_price'));pred=section(s,'^Predictions$');hs={}
 for m in re.finditer(r'^### ([^\n]+)\n([\s\S]*?)(?=^### |\Z)',pred,re.M):
  h=m[1].lower();key='today' if h.startswith('today') else '30d' if h.startswith('30') else '90d' if h.startswith('90') else '1y' if h.startswith('1') else None
  if key:hs[key]=horizon(m[2],m[1],field(s,'scoring_rule') or 'n/a')
 assert set(hs)=={'today','30d','90d','1y'},(t,hs)
 tech=section(s,'Mytutopia technical check')
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-17[\s|]',l)),None)
 assert row,(t,'no latest row')
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-17',1)[1].replace(',','').replace('$',''))
 close,rsi,delta,vel=map(float,nums[:4]);assert abs(close-ref)<.02,(t,close,ref)
 gate=re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',tech,re.I) or re.search(r'momentum[- ]?gate[- ]*\s*[:/ ]*\s*(buying|selling)',s,re.I)
 price,clock,qcontext=QUOTES[t];assert str(price).rstrip('0').rstrip('.') in s.replace(',','') or f'{price:.2f}' in s.replace(',',''),(t,price)
 catalyst,unusual,risk=BLURBS[t]
 for k,h in hs.items():
  assert h['low'] and 0<h['low']<=h['high'] and h['direction']!='n/a' and h['confidence'] is not None and h['target_session'],(t,k,h)
  h['window_width_fraction']=(h['high']-h['low'])/h['high'];h['max_window_width_fraction']={'today':.08,'30d':.15,'90d':.20}.get(k)
  h['contract_violation']=h['max_window_width_fraction'] is not None and h['window_width_fraction']>h['max_window_width_fraction']+1e-12
 cal=section(s,'Historical calibration review')
 # Preserve full cohort context rather than pooling incompatible legacy verdicts.
 caltext=mod.clean_text(cal)
 risk_score={'down':30,'flat_to_down':22}.get(hs['today']['direction'],0)+max(-vel,0)
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=qcontext,pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-17',data_context='Completed bar; advertised24-hour delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=caltext,adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no quote refresh',_opp_score=hs['today']['confidence'],_risk_score=risk_score)

cards=[build_card(t) for t in mod.TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']];down=[c['ticker'] for c in cards if c['today']['direction'] in ['down','flat_to_down']]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
bullets=[
f"Coverage {len(coverage['generated'])}/10 same-day notes; {len(up)} up/flat-to-up calls and {len(down)} defensive calls ({', '.join(down)}).",
'Broad indicative semiconductor relief follows NVIDIA actual earnings, but quotes are asynchronous frozen premarket samples, not live prices or demonstrated liquidity.',
f"All ten latest completed RSI readings remain below50. {len(neg)} have negative VEL5 ({', '.join(neg)}); a green indication does not establish momentum repair.",
'NVIDIA earnings/Rubin shipments strengthen demand evidence. The extra Q4 week, lower guided margins, extended terms and larger guarantees prevent a clean headline-to-cash extrapolation.',
'MU benefits from memory procurement read-through without disclosed vendor allocation. ASML and TSM still need funded capacity, acceptance and collections rather than announcements alone.',
'ARM Cobalt GA improves CSS deployment evidence, not merchant-chip revenue. Intel and Qualcomm remain relative laggards despite green sector indications.',
'NET pairs new billable inference with reliability/legal friction; PANW reports after today’s target close. SIMO retains a profit-versus-operating-cash gap.',
f"Preserve close-window-v1: inclusive exact-target regular close only; no intraday rescue or partial credit. {len(violations)} cap violations among30 capped windows. All40 published horizons remain pending; legacy scorecards separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Earnings-led relief, not confirmed repair: negative momentum persists; Intel and Qualcomm lag.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or new scoring')
data['telegram_summary']=mod.telegram_summary(data)
html=mod.build_html(data)
html=html.replace('Source: Obsidian daily-stock research notes and prediction ledgers.','Source: Obsidian daily-stock research notes only. Frozen premarket snapshots, not live prices; all quoted catalysts are note-reported, not independently refreshed. Published closing bounds preserved.')
html=html.replace("['flat_to_down','down','flat'].includes(card.today.direction)","['flat_to_down','down'].includes(card.today.direction)")
html=html.replace('<option value="ticker">Sort: ticker</option>','<option value="ticker">Sort: ticker</option><option value="company">Sort: company</option><option value="status">Sort: status</option><option value="direction">Sort: direction</option>')
html=html.replace("if(key === 'company') return a.company.localeCompare(b.company);","if(key === 'company') return a.company.localeCompare(b.company); if(key === 'status') return a.status.localeCompare(b.status); if(key === 'direction') return a.today.direction.localeCompare(b.today.direction);")
html=html.replace("if(activeFilter === 'risk') return card.status === 'generated' && num(card._risk_score,0) > 0 && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';","if(activeFilter === 'risk') return APP_DATA.top_risks.some(c=>c.ticker===card.ticker) && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';")
html=html.replace('Risk ${card._risk_score}','Tactical caution')
html=html.replace('Sort: opportunity score','Sort: tactical opportunity').replace('Sort: risk score','Sort: tactical caution').replace('>High risk<','>Top risks<')
html=html.replace('const cards = APP_DATA.cards.slice();','window.__dailyStockData = APP_DATA;\nconst cards = APP_DATA.cards.slice();')
extra='''<div class="detail-box" style="margin-top:10px"><strong>Frozen quote / forecast contract</strong><p>${esc(card.current_time)} · ${esc(card.quote_context)} · reference ${esc(card.reference_date)}. Technical bar ${esc(card.mytutopia.bar_date)};24-hour advertised delay.</p>${['today','30d','90d','1y'].map(h=>{const p=card[h];return `<p><strong>${esc(h.toUpperCase())}</strong>: target ${esc(p.target_session)} · calendar ${esc(p.calendar_target)} · ${esc(p.scoring_rule)} · ${esc(p.status)}<br>Width ${(p.window_width_fraction*100).toFixed(4)}% / cap ${p.max_window_width_fraction===null?'none specified':(p.max_window_width_fraction*100)+'%'} · ${p.contract_violation?'CONTRACT VIOLATION':'compliant'}<br>${esc(p.thesis)}</p>`;}).join('')}<p>Only inclusive exact-target regular-close containment is a binary hit; direction is diagnostic. Legacy scorecards below are separate. No new scoring in this synthesis.</p></div>'''
html=html.replace('<details class="stock-details"><summary>Expand details</summary>','<details class="stock-details"><summary>Expand details</summary>'+extra)
html=html.replace('<h2>Charts</h2>','<h2>Charts</h2><p class="muted">Confidence is subjective closing-window containment conviction, not expected return or a calibrated hit probability. Opportunity ordering uses Today containment confidence among up-biased calls; caution ranks defensive calls then negative VEL5.</p>')
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1118-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
