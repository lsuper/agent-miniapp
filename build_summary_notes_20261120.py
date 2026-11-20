"""2026-11-20 notes-only synthesis. No quotes fetched, no forecasts issued/scored."""
from pathlib import Path
from datetime import datetime
import importlib.util,json,re,hashlib,subprocess,shutil
REPO=Path('/Users/sluan/Projects/agent-miniapp')
ROOT=Path('/Users/sluan/Documents/obsidian-vault/hermes-wiki/investment/research/daily-stock-runs')
DATE='2026-11-20'
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
 explicit_short=re.search(r'explicit\s+session\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 if explicit_short:target=explicit_short
 cal=re.search(r'calendar target(?: date)?\s*:?\s*(\d{4}-\d{2}-\d{2})',text,re.I)
 return dict(direction=direction,confidence=int(cm[1]) if cm else None,low=low,high=high,thesis=label(r'(?:brief )?thesis'),range_basis=label('range basis|basis'),drivers=[label(r'(?:key )?drivers')],falsifiers=[label('falsifiers')],target_session=target[1] if target else None,calendar_target=cal[1] if cal else None,scoring_rule=rule,status='pending / unscored (as published)')
QUOTES={
'NVDA':(141.07,'08:03:44 EST','Yahoo indication; separate Google 141.10 at 08:09 EST'),
'MU':(654.19,'08:10:26 EST','Yahoo indication; separate Google 653.75 at 08:14 EST'),
'INTC':(53.40,'08:17:40 EST','Yahoo indication; separate Google 53.29 at 08:19 EST'),
'ARM':(167.00,'08:22:51 EST','Yahoo indication; separate Google 166.25 at 08:29 EST'),
'ASML':(1321.33,'08:30:34 EST','Yahoo indication; separate Google 1321.64 at 08:34 EST'),
'TSM':(332.50,'08:52:45 EST','Yahoo indication; separate Google 332.40 at 08:51 EST'),
'SIMO':(136.50,'08:48:55 EST','Yahoo indication; separate Google 136.50 at 08:48 EST'),
'NET':(294.96,'08:59:49 EST','Yahoo indication; separate Google 293.80 at 08:49 EST'),
'AMD':(465.4287,'09:05:54 EST','Yahoo indication; separate Google 469.25 at 09:14 EST'),
'QCOM':(161.0372,'09:09:09 EST','Yahoo indication; separate Google 160.70 at 09:15 EST')}
BLURBS={
'NVDA':('Anthropic funding completion and Azure Rubin preview improve customer evidence; recovered November17 call is not a new guide.','RSI19.6 with less-negative VEL5 is selling deceleration, not reversal; yesterday missed its lower bound by two cents.','Leadership/export scrutiny, DSO64 and contingent customer guarantees remain risks despite strong operating growth.'),
'MU':('December17 results date authenticated; Anthropic closing advances prior conditional allocation, not another investment.','Yesterday reached760.01 then closed690.44; red indications and VEL5-8.2 argue against reflexive dip buying.','TrendForce NAND-downcycle forecast and HBM margin dilution challenge the demand narrative; customer funding is not MU cash collected.'),
'INTC':('Signed unnamed18A-P customer and Microsoft EMIB/Xeon evidence remain prior announcements, not new awards.','RSI31 and VEL5-2.4 repair modestly, but sharply red live indications threaten to erase the prior gain.','Undisclosed wafer economics, capex, dilution and weak client outlook constrain a self-funded turnaround.'),
'ARM':('Q2 guidance unchanged; capacity contracts and customer POs still require acceptance and collections.','Failed green rebound and fresh red indication align with RSI38.2/VEL5-5.2.','Contract assets, supplier advances and consolidated R&D costs put merchant-chip cash conversion at risk; Haas departure unconfirmed.'),
'ASML':('No new ASML guide; California investigation of NVIDIA adds authenticated customer-risk context, not canceled scanner orders.','RSI33.8 falls while VEL5 improves only marginally to-8.6; broad red peers dominate tactical placement.','Customer financing, acceptance timing and policy restrictions can weaken cash conversion despite scanner scarcity.'),
'TSM':('Element Labs venture exposure and Anthropic closing are investments, not fresh wafer orders; family purchase is Taiwan common shares.','ADR indication lags SOXX; Taipei falls4.76%; RSI34.4 with VEL5-12.8 shows no velocity recovery.','Customer-credit correlation, export policy and overseas margin execution compound relative tape weakness.'),
'SIMO':('New agentic-storage technical blog adds no award or guide; London event date conflicts between live calendar and release.','RSI32.5/VEL5-9.0 deteriorate after repeated failed relief; Sandisk split distorts naive peer comparisons.','Negative operating cash flow, inventory financing and qualification timing challenge conversion of growth to owner cash.'),
'NET':('Artifacts billing denominator clarified; inbound TCP/gRPC beta broadens integration without new financial guidance.','RSI crosses50.4 but VEL5-4.0 and red breadth contradict strong continuation after failed gap retention.','Raw operation growth overstates billable units; paid retention, reliability, model costs and dilution remain cash-quality tests.'),
'AMD':('Anthropic subscription closing authenticated; new export/firmware allegations require careful separation from regulator findings.','Prior close lost7.72%; RSI45.2 and VEL5-12.3 deteriorate while indications lag most peers.','Compliance scrutiny, investment outflows and customer acceptance/collections can outweigh strong growth; allegations are not findings.'),
'QCOM':('Form4 confirms the same2500-share planned sale, not another sale; Dragonwing longevity detail is not a new order.','Relative resilience and RSI42.2 repair coexist with VEL5-10.2 and all-red peers.','Handset weakness, custom-silicon concentration and gross buybacks largely offset by issuance constrain per-share cash returns.')}

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
 row=next((l for l in tech.splitlines() if re.match(r'^\s*\|?\s*(?:2026-)?11-19[\s|]',l)),None)
 assert row,(t,'no latest row')
 nums=re.findall(r'[-+]?\d+(?:\.\d+)?',row.split('11-19',1)[1].replace(',','').replace('$',''))
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
 risk_score={'AMD':30,'TSM':25}.get(t,0)
 return dict(ticker=t,company=mod.COMPANY_MAP[t],status='generated' if p.stem==DATE else 'stale',note_date=p.stem,note_path=f'research/daily-stock-runs/{t}/{p.name}',source_sha256=hashlib.sha256(raw.encode()).hexdigest(),reference_price=ref,reference_date=field(s,'reference_date'),current_price=price,current_time=clock,current_label='Frozen premarket snapshot',quote_context=qcontext,pct_vs_ref=(price/ref-1)*100,mytutopia=dict(rsi=rsi,vel5=vel,delta1=delta,momentum_gate='MOMENTUM-GATE '+gate[1].upper() if gate else None,bar_date='2026-11-19',data_context='Completed bar; advertised24-hour delay; not live'),today=hs['today'],**{'30d':hs['30d'],'90d':hs['90d'],'1y':hs['1y']},top_catalyst=catalyst,unusual_signal=unusual,top_risk=risk,calibration_note=caltext,adjustment_note=mod.clean_text(section(s,'Research adjustments')),social_note=mod.clean_text(section(s,'Social-media')) or 'n/a',google_finance_method='Frozen note observation; no quote refresh',_opp_score=hs['today']['confidence'],_risk_score=risk_score)

cards=[build_card(t) for t in mod.TICKERS]
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
up=[c['ticker'] for c in cards if c['today']['direction'] in ['up','flat_to_up']];down=[c['ticker'] for c in cards if c['today']['direction'] in ['down','flat_to_down']]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
bullets=[
f"All {len(cards)} same-day calls are down; all {len(neg)} completed VEL5 readings are negative. This is broad risk-off, not isolated ticker digestion. Frozen asynchronous indications, not live prices.",
'No tactical opportunities pass the up/flat-to-up gate. Conditional quarterly and annual recovery theses must not be labeled same-day buys.',
'AMD and TSM carry highlighted cautions: relative weakness combines with VEL5 below-10, export scrutiny/customer credit exposure. Rank is editorial, not measured downside probability.',
'Anthropic reports completed IPO and concurrent placement. This advances prior funding evidence, not a second vendor investment, hardware revenue or verified issuer bank balances.',
'MU announces December17 results; missed older TrendForce NAND-downcycle forecasts are a coverage correction, not a new MU guidance cut. Sandisk8-for-1 split requires comparable price bases.',
'INTC modest technical repair and QCOM relative resilience do not negate red absolute tape. ASML structural capacity ambition remains conditional on acceptance and cash conversion.',
'NET alone has RSI above50 but negative velocity; weighted Artifacts billable units mean raw usage is not revenue. SIMO and ARM retain working-capital/merchant-conversion risks.',
f"Close-window-v1: {len(violations)} cap violations across30 capped windows. All40 published targets remain pending as published. Inclusive exact-session close containment only; no widening, new scoring or legacy-partial credit."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='Broad risk-off: all ten Today calls are down; no tactical opportunities. AMD and TSM carry highlighted cautions.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Top opportunities',contract_violations=violations,source_mode='daily notes only; no ledgers, fresh research or new scoring')
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
html=html.replace("APP_DATA.top_opportunities.map(c => miniCard(c, 'opp')).join('')", "APP_DATA.top_opportunities.length ? APP_DATA.top_opportunities.map(c => miniCard(c, 'opp')).join('') : '<p class=muted>No tactical opportunities: all Today calls are down. Longer-horizon recovery theses remain conditional; see expanded cards.</p>'")
html=html.replace('Top 2 opportunities:', 'Tactical opportunities:').replace('Top 2 risks:', 'Highlighted risks:')
html=html.replace('Sort: opportunity score','Sort: tactical opportunity').replace('Sort: risk score','Sort: tactical caution').replace('>High risk<','>Top risks<')
html=html.replace('const cards = APP_DATA.cards.slice();','window.__dailyStockData = APP_DATA;\nconst cards = APP_DATA.cards.slice();')
extra='''<div class="detail-box" style="margin-top:10px"><strong>Frozen quote / forecast contract</strong><p>${esc(card.current_time)} · ${esc(card.quote_context)} · reference ${esc(card.reference_date)}. Technical bar ${esc(card.mytutopia.bar_date)};24-hour advertised delay.</p>${['today','30d','90d','1y'].map(h=>{const p=card[h];return `<p><strong>${esc(h.toUpperCase())}</strong>: target ${esc(p.target_session)} · calendar ${esc(p.calendar_target)} · ${esc(p.scoring_rule)} · ${esc(p.status)}<br>Width ${(p.window_width_fraction*100).toFixed(4)}% / cap ${p.max_window_width_fraction===null?'none specified':(p.max_window_width_fraction*100)+'%'} · ${p.contract_violation?'CONTRACT VIOLATION':'compliant'}<br>${esc(p.thesis)}</p>`;}).join('')}<p>Only inclusive exact-target regular-close containment is a binary hit; direction is diagnostic. Legacy scorecards below are separate. No new scoring in this synthesis.</p></div>'''
html=html.replace('<details class="stock-details"><summary>Expand details</summary>','<details class="stock-details"><summary>Expand details</summary>'+extra)
html=html.replace('<h2>Charts</h2>','<h2>Charts</h2><p class="muted">Confidence is subjective closing-window containment conviction, not expected return or a calibrated hit probability. Opportunity ordering uses Today containment confidence among up-biased calls; caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure, not a measured risk probability.</p>')
assert len(cards)==10 and len({c['ticker'] for c in cards})==10
assert all(c['today']['target_session']==DATE for c in cards)
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1120-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
assert json.loads(jp.read_text())['coverage']==coverage
print(json.dumps({'html':str(hp),'coverage':coverage,'opportunities':[c['ticker'] for c in opps],'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
