"""Notes-only stale fallback. No fresh forecasts, closes, scoring or messaging."""
from pathlib import Path
import json,re,hashlib,subprocess,shutil
from datetime import datetime
REPO=Path('/Users/sluan/Projects/agent-miniapp')
previous=(REPO/'build_summary_notes_20261125.py').read_text()
exec(previous[:previous.index('\ncards=[build_card')])
DATE='2026-11-26'
# Reparse the actual selected notes with the prior validated notes-only parser.
cards=[build_card(t) for t in TICKERS]
for c in cards:
 p=ROOT/c['ticker']/(c['note_date']+'.md');s=norm(p.read_text())
 assert c['source_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 for h in ['today','30d','90d','1y']:
  # The source has pending publication status, not verified present-day outcome.
  c[h]['status']='unscored in this synthesis; source publication status: pending'
  assert c[h]['target_session'] and c[h]['target_close']
 c['current_label']='STALE November 25 premarket snapshot'
 c['google_finance_method']='Prior note observation only; not rechecked November 26'
 c['quote_context']='STALE '+c['note_date']+' snapshot. '+c['quote_context']
coverage={k:[c['ticker'] for c in cards if c['status']==k] for k in ['generated','stale','missing']}
assert len(cards)==10 and len(coverage['stale'])==10 and not coverage['generated']
opps=sorted([c for c in cards if c['today']['direction'] in ['up','flat_to_up']],key=lambda c:(-c['_opp_score'],c['ticker']))[:2]
risks=sorted([c for c in cards if c['_risk_score']>0],key=lambda c:(-c['_risk_score'],c['ticker']))[:2]
violations=[f"{c['ticker']} {h}" for c in cards for h in ['today','30d','90d'] if c[h]['contract_violation']]
neg=[c['ticker'] for c in cards if c['mytutopia']['vel5']<0]
assert all(c['today']['direction']=='down' for c in cards)
bullets=[
'STALE FALLBACK: 0/10 same-day notes. All ten selected notes are November 25, 2026; the dashboard date is not the forecast date. No fresh ticker research was run.',
'All ten prior Today calls were down, targeting the November 25 close. These are historical forecasts, not November 26 recommendations, and are not shifted to the next session.',
f"The prior completed-bar snapshot had RSI below 50 across all ten tickers. Negative VEL5: {', '.join(neg)}; positive velocity elsewhere did not establish live gap absorption. Technical bars are November 24, not current.",
'No stale tactical opportunities qualify. Stale caution highlights are AMD (worsening negative velocity, relative weakness and cash conversion) and MU (failed momentum repair, NAND pricing forecasts and compensation reserves). These are editorial highlights, not ranked loss probabilities.',
'November 25 notes report Dell actuals corroborating AI-server demand and naming Rubin for most new orders. Dell system dollars are not NVIDIA revenue, AMD-specific orders, TSM wafer commitments or ASML scanner backlog. HP PC revenue growth coexists with unit declines.',
'Prior issuer deltas: NET Search for Agents beta lacks disclosed paid adoption; QCOM special grants are contingent compensation, not insider buying; ASML diplomacy is not enacted policy; TSM Texas recommendations remain nonbinding; SIMO samples are not production shipments.',
'All prices are frozen November 25 premarket indications from asynchronous source clocks; references are November 24 regular closes. No latest November 25 close was fetched; quotes and source calibration are not live or newly scored.',
f"Published close-window-v1 bounds are unchanged: {len(violations)} violations across 30 capped windows. All 40 targets remain unscored here, even where the target has passed. A verified exact-target regular close is required for binary scoring; legacy scorecards are separate."
]
data=dict(date=DATE,generated_at=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),headline='STALE FALLBACK — 0/10 same-day notes; latest notes November 25. Prior forecasts were uniformly defensive; no fresh market call.',coverage=coverage,cards=cards,market_bullets=bullets,top_opportunities=opps,top_risks=risks,opportunity_label='Stale opportunities — November 25',contract_violations=violations,source_mode='daily notes only; stale fallback; no ledgers, fresh research, forecasts or scoring')
data['telegram_summary']='STALE FALLBACK: 0/10 same-day; 10/10 prior notes from November 25. Prior Today: all down. Stale opportunities: none. Stale cautions: AMD, MU. Frozen quotes; no new scoring.'
prior=(REPO/'build_summary_notes_20261120.py').read_text()
render=prior[prior.index('html=mod.build_html(data)'):prior.index('assert len(cards)==10')]
render=render.replace('caution highlights AMD compliance/cash-conversion exposure and TSM policy/credit exposure','stale caution highlights AMD relative weakness/cash conversion and MU memory-pricing/compensation exposure')
exec(render)
html=html.replace('<ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>','').replace("document.getElementById('marketBullets').innerHTML = bulletsHtml; ",'')
html=html.replace('today range ','published target-close window ').replace('${esc(p.target_session)} · calendar','${esc(p.target_session)} (${esc(p.target_close)}) · calendar')
html=html.replace('<h2>Top opportunities</h2>','<h2>Stale opportunities — November 25</h2>').replace('<h2>Top risks</h2>','<h2>Stale risks — November 25</h2>')
html=html.replace('No tactical opportunities: all Today calls are down.','No stale tactical opportunities: all November 25 Today calls were down.')
html=html.replace('Only inclusive exact-target regular-close containment is a binary hit;', 'Historical source forecasts, not new calls. Past targets remain unscored here without a verified close. Only inclusive exact-target regular-close containment is a binary hit;')
assert '/Users/sluan' not in html and 'TELEGRAM_BOT_TOKEN' not in html
hp=REPO/f'daily-stock-summary-{DATE}.html';jp=REPO/f'daily-stock-summary-{DATE}.json'
hp.write_text(html);jp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
assert json.loads(jp.read_text())['coverage']==coverage
for i,script in enumerate(re.findall(r'<script(?![^>]*type=[\"\']application/json[\"\'])[^>]*>([\s\S]*?)</script>',html)):
 if script.strip():
  p=Path('/Users/sluan/.hermes/cache/scratch')/f'summary1126-inline-{i}.js';p.write_text(script);subprocess.run(['node','--check',str(p)],check=True)
(REPO/'dist-pages').mkdir(exist_ok=True);shutil.copy2(hp,REPO/'dist-pages'/hp.name)
print(json.dumps({'html':str(hp),'coverage':coverage,'risks':[c['ticker'] for c in risks],'violations':violations,'generated_at':data['generated_at']}))
for c in cards:print(c['ticker'],c['reference_price'],c['current_price'],c['mytutopia'],[(h,c[h]['direction'],c[h]['confidence'],c[h]['low'],c[h]['high'],c[h]['target_session']) for h in ['today','30d','90d','1y']])
