"""2026-11-19 notes-only synthesis. No quotes fetched, no forecasts issued/scored."""
from pathlib import Path
from datetime import datetime
import importlib.util,json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-19'
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
 rm=re.search(r'\$([\d,]+(?:\.\d+)?)\s*[-–—]\s*\$?([\d,]+(?:\.\d+)?)',text)
 low,high=map(lambda x:float(x.replace(',','')),rm.groups()) if rm else (None,None)
 def label(p):
  m=re.search(r'^\s*-?\s*(?:'+p+r')\s*:\s*(.+)$',text,re.I|re.M);return m[1].strip() if m else None
 target=re.search(r'(?:target\s+(?:(?:closing\s+)?session\s*:?\s*|close\s*:?\s*|date/session\s*:?\s*)?|explicit\s+(?:target\s+)?session\s*:?\s*)(\d{4}-\d{2}-\d{2})',text,re.I)
 explicit=re.search(r'(?:explicit|actual|exact)?\s*target\s+(?:closing\s+)?session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 if explicit:target=explicit
 cal=re.search(r'calendar target(?: date)?\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 return dict(direction=direction,confidence=int(cm[1]) if cm else None,low=low,high=high,thesis=label(r'(?:brief )?thesis'),range_basis=label('range basis|basis'),drivers=[label(r'(?:key )?drivers')],falsifiers=[label('falsifiers')],target_session=target[1] if target else None,calendar_target=cal[1] if cal else None,scoring_rule=rule,status='pending / unscored (as published)')
QUOTES={
'NVDA':(152.93,'08:02:37 EST','Designated Yahoo indication; separate Google 153.55 at 08:09 EST'),
'MU':(740.75,'08:09:14 EST','Yahoo indication; separate Google 738.40 at 08:17 EST'),
'INTC':(57.2101,'08:15:43 EST','Yahoo indication; separate Google 57.07 at 08:20 EST'),
'ARM':(190.42,'08:24:55 EST','Yahoo indication; separate Google 190.43 at 08:18 EST'),
'ASML':(1440.75,'08:30 EST','Yahoo indication; separate Google 1437.00 at 08:37 EST'),
'TSM':(366.49,'08:44:35 EST','Yahoo indication; separate Google 366.21 at 08:42 EST'),
'SIMO':(155.00,'08:16:53 EST','Stale Yahoo indication relative to 08:57 collection; Google no premarket panel'),
'NET':(314.50,'09:10:24 EST','Yahoo indication; separate Google 314.00 at 09:08 EST'),
'AMD':(541.04,'09:05:34 EST','Yahoo indication; separate Google 542.72 at 09:12 EST'),
'QCOM':(163.81,'09:19:07 EST','Yahoo indication; separate Google 163.94 at 09:17 EST')}
BLURBS={
'NVDA':('Recovered earnings slide shows nearly $20B incremental Rubin revenue; RTX Spark reaches sales channels.','Another green indication follows failed earnings relief; RSI21.1 and VEL5-7.6 both deteriorate.','DSO64, guided margin compression, contingent guarantees and unresolved permanent succession qualify growth.'),
'MU':('TomorrowX demand reassurance and priced Anthropic allocation add evidence, not a revised MU guide.','About5% indicative gap conflicts with VEL5 crossing to-8.1; zero sampled volume does not prove liquidity.','Client-memory demand destruction, HBM mix margins and customer credit/conditional settlement remain risks.'),
'INTC':('Executive confirms signed external18A-P customer; Microsoft separately validates EMIB and Xeon capacity.','Strong indication beats sampled peers while VEL5 turns negative after eight positive bars.','Undisclosed customer economics, Fab28 recovery, capex and dilution constrain a self-funding turnaround.'),
'ARM':('RTX Spark expands Arm-based customer distribution; fresh Form4 cluster is mostly vesting/withholding.','About4% bid coexists with VEL5+4.7 to-4.6 and another prior opening rally that faded.','Succession reports remain unauthenticated; valuation, collections and merchant-chip cash economics stay unresolved.'),
'ASML':('Official remote-access export rule becomes effective today; no new ASML guidance authenticated.','RSI improves to36.3 while VEL5 worsens to-8.9; broad equipment relief is not trend repair.','Effective policy, customer financing and acceptance timing can disrupt revenue-to-cash conversion.'),
'TSM':('Exchange supplement specifies about$500M Anthropic holding under an older authorization, not another investment.','US indication lags SOXX while Taipei falls3.45%; RSI improves but VEL5 deteriorates to-12.8.','Reported Chinese order pauses pending licenses, overseas execution and correlated customer-credit exposure.'),
'SIMO':('Publisher reports Gen6 final tape-out/late2027–early2028 drives; existing dividend payment date arrives.','Another relief attempt follows a full binary miss; VEL5 worsens and the$155 indication is stale.','Q3 operating cash outflow and inventory financing challenge profit quality; qualification dates are not revenue.'),
'NET':('Clairic pricing/model update and PANW results add monetization and category-demand evidence.','RSI49.6 and less-negative VEL5 show repair; broad cyber/CDN repricing is not one launch effect.','Inference/R&D burden, SBC, competitive secure inference and failed paid retention threaten per-share cash.'),
'AMD':('Anthropic final pricing clarifies conditional$2.5B allocation; OpenAI authenticates IP-block design optimization.','RSI rises above50 after a5.31% close gain, but VEL5 worsens to-3.3 and premarket trails SOXX.','Customer funding is also AMD cash outflow; financing, acceptance, guarantees and dilution may outrun cash growth.'),
'QCOM':('New CFO planned-sale notice is not execution; Cirrascale evaluation is older coverage, not paid production.','Green indication lags SOXX after a failed opening rally; VEL5 deepens to-11.8.','Handset pressure, custom-silicon concentration, export exposure and weak net share shrink constrain recovery.')}

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
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-18[\s|]',l)),None)
 assert row,(t,'no latest row')
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-18',1)[1].replace(',','').replace('$',''))
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
 risk_score={'TSM':30,'QCOM':25}.get(t,0)
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=qcontext,pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-18',data_context='Completed bar; advertised24-hour delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=caltext,adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no quote refresh',_opp_score=hs['today']['confidence'],_risk_score=risk_score)

cards=[build_card(t) for t in mod.TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']];down=[c['ticker'] for c in cards if c['today']['direction'] in ['down','flat_to_down']]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
bullets=[
f"Coverage {len(coverage['generated'])}/10 same-day notes: {len(up)} up/flat-to-up, {len(down)} down-biased; NVDA is neutral. Frozen asynchronous premarket snapshots, not live prices.",
f"All ten completed VEL5 readings are negative; nine RSI readings remain below50. Broad green indications signal relief, not confirmed trend repair.",
'ASML has the highest Today containment conviction; MU and NET tie next. These are subjective capped-window forecasts, not expected-return rankings or calibrated hit probabilities.',
'Intel gains stronger external-customer evidence: unnamed signed18A-P customer, named Microsoft EMIB use and separate Xeon capacity. No disclosed wafer economics or new financial guide.',
'Anthropic pricing clarifies conditional AMD/MU funding and TSM investment terms. Do not double-count old authorizations or equate priced allocation with verified bank settlement or hardware revenue.',
'TSM combines weak Taipei trading, US relative lag and reported Chinese order pauses. ASML separately faces an effective remote-access rule; policy publication is not quantified order cancellation.',
'NET has improving RSI/VEL5 and security-demand read-through, but competition and model costs matter. SIMO retains negative operating cash flow; QCOM velocity deteriorates despite a green indication.',
f"Close-window-v1: {len(violations)} cap violations across30 published capped windows. Exact target-session regular-close containment only; all40 new horizons pending as published. Legacy grades remain separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Broad relief versus damaged momentum: ASML and MU lead containment-ranked opportunities; TSM and QCOM carry key cautions.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or new scoring')
data['telegram_summary']=mod.telegram_summary(data)
html=mod.build_html(data)
html=html.replace('served by the local-first Cloudflare router','served by Cloudflare Pages')
html=html.replace('Source: Obsidian daily-stock research notes and prediction ledgers.','Source: Obsidian daily-stock research notes only. Frozen premarket snapshots, not live prices; all quoted catalysts are note-reported, not independently refreshed. Published closing bounds preserved.')
html=html.replace("['flat_to_down','down','flat'].includes(card.today.direction)","['flat_to_down','down'].includes(card.today.direction)")
html=html.replace('<option value="ticker">Sort: ticker</option>','<option value="ticker">Sort: ticker</option><option value="company">Sort: company</option><option value="status">Sort: status</option><option value="direction">Sort: direction</option>')
html=html.replace("if(key === 'company') return a.company.localeCompare(b.company);","if(key === 'company') return a.company.localeCompare(b.company); if(key === 'status') return a.status.localeCompare(b.status); if(key === 'direction') return a.today.direction.localeCompare(b.today.direction);")
html=html.replace("if(activeFilter === 'risk') return card.status === 'generated' && num(card._risk_score,0) > 0 && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';","if(activeFilter === 'risk') return APP_DATA.top_risks.some(c=>c.ticker===card.ticker) && String(card.top_risk || 'n/a').toLowerCase() !== 'n/a';")
html=html.replace("if(key === 'opp') return num(b._opp_score) - num(a._opp_score);", "if(key === 'opp') return num(b._opp_score) - num(a._opp_score) || a.ticker.localeCompare(b.ticker);")
html=html.replace('Risk ${card._risk_score}','Tactical caution')
html=html.replace('Sort: opportunity score','Sort: tactical opportunity').replace('Sort: risk score','Sort: tactical caution').replace('>High risk<','>Top risks<')
html=html.replace('const cards = APP_DATA.cards.slice();','window.__dailyStockData = APP_DATA;\nconst cards = APP_DATA.cards.slice();')
extra='''<div class="detail-box" style="margin-top:10px"><strong>Frozen quote / forecast contract</strong><p>${esc(card.current_time)} · ${esc(card.quote_context)} · reference ${esc(card.reference_date)}. Technical bar ${esc(card.mytutopia.bar_date)};24-hour advertised delay.</p>${['today','30d','90d','1y'].map(h=>{const p=card[h];return `<p><strong>${esc(h.toUpperCase())}</strong>: target ${esc(p.target_session)} · calendar ${esc(p.calendar_target)} · ${esc(p.scoring_rule)} · ${esc(p.status)}<br>Width ${(p.window_width_fraction*100).toFixed(4)}% / cap ${p.max_window_width_fraction===null?'none specified':(p.max_window_width_fraction*100)+'%'} · ${p.contract_violation?'CONTRACT VIOLATION':'compliant'}<br>${esc(p.thesis)}</p>`;}).join('')}<p>Only inclusive exact-target regular-close containment is a binary hit; direction is diagnostic. Legacy scorecards below are separate. No new scoring in this synthesis.</p></div>'''
html=html.replace('<details class="stock-details"><summary>Expand details</summary>','<details class="stock-details"><summary>Expand details</summary>'+extra)
html=html.replace('<h2>Charts</h2>','<h2>Charts</h2><p class="muted">Confidence is subjective closing-window containment conviction, not expected return or a calibrated hit probability. Opportunity ordering uses Today containment confidence among up-biased calls; caution highlights TSM policy/credit exposure and QCOM momentum/customer concentration, not a measured risk probability.</p>')
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1119-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
