from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

TICKERS = ["NVDA", "MU", "LRCX", "ARM", "ASML", "FSLY", "TSM", "SIMO", "NET", "AMD"]
COMPANY_MAP = {
    "NVDA": "NVIDIA",
    "MU": "Micron Technology",
    "LRCX": "Lam Research Corporation",
    "ARM": "Arm Holdings",
    "ASML": "ASML Holding N.V.",
    "FSLY": "Fastly",
    "TSM": "Taiwan Semiconductor Manufacturing",
    "SIMO": "Silicon Motion Technology Corp.",
    "NET": "Cloudflare",
    "AMD": "Advanced Micro Devices",
}
VAULT = Path.home() / "Documents/obsidian-vault/hermes-wiki/investment"
RUNS = VAULT / "research/daily-stock-runs"
REPO = Path("/Users/sluan/Projects/agent-miniapp")
DATE = datetime.now().strftime("%Y-%m-%d")
GENERATED_AT = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def clean_text(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"`{1,3}", "", s)
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"^>\s?", "", s, flags=re.M)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm_text = text[4:end]
            body = text[end + 5 :]
            data: dict[str, Any] = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    data[k.strip()] = v.strip()
            return data, body
    return {}, text


def get_section(body: str, heading: str) -> str | None:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", body, re.M)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"^##\s+", body[start:], re.M)
    end = start + next_m.start() if next_m else len(body)
    return body[start:end].strip()


def get_subsection(body: str, heading: str) -> str | None:
    m = re.search(rf"^###\s+{re.escape(heading)}(?:\s*\([^\n]*\))?\s*$", body, re.M)
    if not m:
        return None
    start = m.end()
    next_m = re.search(r"^###\s+", body[start:], re.M)
    end = start + next_m.start() if next_m else len(body)
    return body[start:end].strip()


def first_meaningful_line(section: str | None) -> str | None:
    if not section:
        return None
    for raw in section.splitlines():
        line = clean_text(raw.lstrip("-* "))
        if line and not line.startswith("###"):
            return line
    return None


def parse_floatish(val: Any) -> float | None:
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() in {"n/a", "na", "none", "null"}:
        return None
    s = s.replace(",", "")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def parse_intish(val: Any) -> int | None:
    num = parse_floatish(val)
    if num is None:
        return None
    return int(round(num))


def parse_direction(val: Any) -> str:
    s = clean_text(str(val)) if val is not None else None
    if not s:
        return "n/a"
    s = s.lower().replace("neutral", "flat")
    s = s.replace("flat-to-", "flat_to_").replace("flat to ", "flat_to_")
    s = s.replace("flat to down", "flat_to_down").replace("flat to up", "flat_to_up")
    s = s.replace("neutral_to_up", "flat_to_up").replace("neutral-to-up", "flat_to_up")
    s = s.replace("neutral_to_down", "flat_to_down").replace("neutral-to-down", "flat_to_down")
    s = s.replace("flat/up", "flat_to_up").replace("flat/down", "flat_to_down")
    s = s.strip("* ")
    s = s.replace(" ", "_")
    allowed = {"up", "down", "flat", "flat_to_up", "flat_to_down"}
    return s if s in allowed else s


def parse_price_range_from_text(text: str | None) -> tuple[float | None, float | None]:
    if not text:
        return None, None
    m = re.search(r"\$?([0-9][0-9,]*\.?[0-9]*)\s*(?:to|-|–|—)\s*\$?([0-9][0-9,]*\.?[0-9]*)", text)
    if not m:
        return None, None
    return parse_floatish(m.group(1)), parse_floatish(m.group(2))


def normalize_horizon_obj(obj: dict[str, Any]) -> dict[str, Any]:
    thesis = obj.get("thesis")
    low = obj.get("price_range_low", obj.get("low"))
    high = obj.get("price_range_high", obj.get("high"))
    if (low is None or high is None) and thesis:
        plow, phigh = parse_price_range_from_text(str(thesis))
        low = low if low is not None else plow
        high = high if high is not None else phigh
    return {
        "direction": parse_direction(obj.get("direction")),
        "confidence": parse_intish(obj.get("confidence")),
        "low": parse_floatish(low),
        "high": parse_floatish(high),
        "thesis": clean_text(str(thesis)) if thesis is not None else None,
        "range_basis": clean_text(str(obj.get("range_basis") or obj.get("range_context"))) if (obj.get("range_basis") or obj.get("range_context")) else None,
    }


def parse_note_prediction_block(block: str | None) -> dict[str, Any]:
    if not block:
        return {"direction": "n/a", "confidence": None, "low": None, "high": None, "thesis": None, "range_basis": None}
    data: dict[str, Any] = {}
    for key in ["direction", "confidence", "price_range_low", "price_range_high", "range_basis", "thesis"]:
        m = re.search(rf"[-*]\s*\*\*{re.escape(key)}\*\*:\s*(.+)", block, re.I)
        if m:
            data[key] = clean_text(m.group(1))
    for key in ["direction", "confidence", "range_basis", "thesis"]:
        if key not in data:
            m = re.search(rf"[-*]\s*{re.escape(key)}:\s*(.+)", block, re.I)
            if m:
                data[key] = clean_text(m.group(1))
    low, high = parse_price_range_from_text(block)
    if low is not None:
        data.setdefault("price_range_low", low)
        data.setdefault("price_range_high", high)
    if "thesis" not in data:
        paras = [clean_text(p) for p in block.split("\n\n")]
        data["thesis"] = next((p for p in paras if p), None)
    return normalize_horizon_obj(data)


def note_fallback_horizons(pred_sec: str | None) -> dict[str, dict[str, Any]]:
    mapping = {}
    for label, key in [("Today", "today"), ("30D", "30d"), ("30 days", "30d"), ("90D", "90d"), ("1Y", "1y"), ("1 year", "1y")]:
        if key not in mapping:
            block = get_subsection(pred_sec or "", label)
            if block:
                mapping[key] = parse_note_prediction_block(block)
    return mapping


def normalize_horizons(record: dict[str, Any], note_pred_sec: str | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if isinstance(record.get("horizons"), list):
        for h in record["horizons"]:
            if not isinstance(h, dict):
                continue
            name = str(h.get("horizon", "")).lower().strip()
            key = {
                "today": "today",
                "1 day": "today",
                "1d": "today",
                "30d": "30d",
                "30 days": "30d",
                "30 day": "30d",
                "days_30": "30d",
                "90d": "90d",
                "90 days": "90d",
                "90 day": "90d",
                "days_90": "90d",
                "1y": "1y",
                "1 year": "1y",
                "year_1": "1y",
            }.get(name)
            if key:
                out[key] = normalize_horizon_obj(h)
    preds = record.get("predictions")
    if isinstance(preds, dict):
        for key, value in preds.items():
            lk = str(key).lower().strip()
            lk = {
                "today": "today",
                "1d": "today",
                "30d": "30d",
                "30 days": "30d",
                "days_30": "30d",
                "90d": "90d",
                "90 days": "90d",
                "days_90": "90d",
                "1y": "1y",
                "1 year": "1y",
                "year_1": "1y",
            }.get(lk, lk)
            if lk in {"today", "30d", "90d", "1y"} and isinstance(value, dict) and lk not in out:
                out[lk] = normalize_horizon_obj(value)
    elif isinstance(preds, list):
        for item in preds:
            if not isinstance(item, dict):
                continue
            lk = str(item.get("horizon", "")).lower().strip()
            lk = {
                "today": "today",
                "1 day": "today",
                "1d": "today",
                "30d": "30d",
                "30 days": "30d",
                "30 day": "30d",
                "days_30": "30d",
                "90d": "90d",
                "90 days": "90d",
                "90 day": "90d",
                "days_90": "90d",
                "1y": "1y",
                "1 year": "1y",
                "year_1": "1y",
            }.get(lk, lk)
            if lk in {"today", "30d", "90d", "1y"} and lk not in out:
                out[lk] = normalize_horizon_obj(item)
    for key, value in note_fallback_horizons(note_pred_sec).items():
        out.setdefault(key, value)
    for key in ["today", "30d", "90d", "1y"]:
        out.setdefault(key, {"direction": "n/a", "confidence": None, "low": None, "high": None, "thesis": None, "range_basis": None})
    return out


def load_latest_record(ledger_path: Path, today: str) -> dict[str, Any] | None:
    if not ledger_path.exists():
        return None
    latest = None
    same_day = None
    for line in ledger_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if latest is None or str(obj.get("date", "")) >= str(latest.get("date", "")):
            latest = obj
        if obj.get("date") == today:
            same_day = obj
    return same_day or latest


def pick_note(ticker: str, today: str) -> tuple[str, Path | None]:
    tdir = RUNS / ticker
    files = []
    if tdir.exists():
        for p in tdir.glob("*.md"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", p.name)
            if m:
                files.append((m.group(1), p))
    files.sort()
    same = [p for d, p in files if d == today]
    if same:
        return "generated", same[-1]
    if files:
        return "stale", files[-1][1]
    return "missing", None


def extract_google_method(body: str) -> str | None:
    sec = get_section(body, "What's new since last run") or ""
    m = re.search(r"Google Finance[^\n:]*[:\-]\s*(.+)", sec, re.I)
    return clean_text(m.group(1)) if m else None


def extract_note_value(section: str | None, *patterns: str) -> str | None:
    if not section:
        return None
    for pat in patterns:
        m = re.search(pat, section, re.I)
        if m:
            return clean_text(m.group(1))
    return None


def extract_first_falsifier(obj: dict[str, Any] | None) -> str | None:
    if not isinstance(obj, dict):
        return None
    falsifiers = obj.get("falsifiers")
    if isinstance(falsifiers, list):
        for item in falsifiers:
            cleaned = clean_text(str(item))
            if cleaned:
                return cleaned
    elif falsifiers is not None:
        return clean_text(str(falsifiers))
    return None


def pick_semantic_risk(*candidates: str | None) -> str | None:
    risk_words = (
        'risk', 'overhang', 'overbought', 'fade', 'weakness', 'softness', 'underperformance',
        'digestion', 'crowded', 'insider', 'supply', 'pressure', 'geopolit', 'delay', 'blocked',
        'negative', 'cooling', 'lagging', 'valuation', 'reversal', 'volatility', 'challeng', 'wobble',
        'caution', 'cautionary', 'damaged', 'fragile', 'compression', 'bearish', 'deteriorat', 'reject'
    )
    for text in candidates:
        cleaned = clean_text(text)
        if not cleaned:
            continue
        lower = cleaned.lower()
        if any(word in lower for word in risk_words):
            return cleaned
    # second pass: if a candidate has a strong concessive pivot, keep the cautionary tail only when it stays risk-like
    for text in candidates:
        cleaned = clean_text(text)
        if not cleaned:
            continue
        lower = cleaned.lower()
        for sep in (' but ', ' however ', ' though '):
            if sep in lower:
                tail = cleaned[lower.index(sep) + len(sep):].strip(' .;:-')
                if tail and any(word in tail.lower() for word in risk_words):
                    return tail[:1].upper() + tail[1:]
    for text in candidates:
        cleaned = clean_text(text)
        if cleaned and any(word in cleaned.lower() for word in ('falsifier', 'resistance', 'selloff', 'drawdown')):
            return cleaned
    return None


def build_card(ticker: str, today: str) -> dict[str, Any]:
    status, note_path = pick_note(ticker, today)
    note_text = note_path.read_text() if note_path and note_path.exists() else ""
    frontmatter, body = extract_frontmatter(note_text)
    company = frontmatter.get("company") or ticker
    if not company or company == ticker:
        company = COMPANY_MAP.get(ticker, ticker)

    sections = {name: get_section(body, name) for name in [
        "What's new since last run",
        "Deep dive on earnings / major catalysts",
        "Unusual signals",
        "Balance sheet and capital allocation",
        "Social-media / public-discussion signals",
        "Mytutopia technical check",
        "Predictions",
        "Historical calibration review",
        "Research adjustments based on past accuracy",
    ]}

    ledger = load_latest_record((RUNS / ticker / "predictions.jsonl"), today) or {}
    horizons = normalize_horizons(ledger, sections["Predictions"])

    ref = parse_floatish(ledger.get("reference_price"))
    current = parse_floatish(ledger.get("premarket_price") or ledger.get("current_price") or ledger.get("intraday_price"))
    current_label = "premarket" if ledger.get("premarket_price") is not None else ("current" if current is not None else "live")
    current_time = (
        ledger.get("premarket_time_et")
        or ledger.get("premarket_time")
        or ledger.get("premarket_timestamp")
        or ledger.get("google_finance_premarket_timestamp")
        or ledger.get("current_time_et")
        or ledger.get("intraday_time_et")
        or ledger.get("intraday_timestamp")
    )

    raw_my = ledger.get("mytutopia")
    my: dict[str, Any] = raw_my if isinstance(raw_my, dict) else {}
    gate = my.get("momentum_gate_status") or my.get("momentum_gate") or my.get("gate") or my.get("data_context")
    mytutopia = {
        "rsi": parse_floatish(my.get("rsi")),
        "vel5": parse_floatish(my.get("vel5")),
        "delta1": parse_floatish(my.get("delta1")),
        "momentum_gate": clean_text(str(gate)) if gate is not None else None,
        "page": my.get("page"),
    }

    wn = sections["What's new since last run"]
    if ref is None:
        ref = parse_floatish(extract_note_value(wn, r"reference close[^\n$]*\$([0-9][0-9,]*\.?[0-9]*)", r"prior close[^\n$]*\$([0-9][0-9,]*\.?[0-9]*)"))
    if current is None:
        current = parse_floatish(extract_note_value(wn, r"premarket[^\n$]*\$([0-9][0-9,]*\.?[0-9]*)", r"current[^\n$]*\$([0-9][0-9,]*\.?[0-9]*)"))
    if mytutopia["rsi"] is None:
        my_sec = sections["Mytutopia technical check"] or ""
        mytutopia["rsi"] = parse_floatish(extract_note_value(my_sec, r"RSI[^\n:]*[:\-]\s*([0-9]+\.?[0-9]*)"))
        mytutopia["vel5"] = parse_floatish(extract_note_value(my_sec, r"VEL5[^\n:]*[:\-]\s*([+-]?[0-9]+\.?[0-9]*)", r"VEL 5[^\n:]*[:\-]\s*([+-]?[0-9]+\.?[0-9]*)"))

    pct = ((current - ref) / ref * 100.0) if (ref is not None and current is not None and ref != 0) else None

    unusual = first_meaningful_line(sections["Unusual signals"])
    catalyst = first_meaningful_line(sections["Deep dive on earnings / major catalysts"]) or first_meaningful_line(sections["What's new since last run"])
    today_thesis = horizons["today"].get("thesis") if isinstance(horizons.get("today"), dict) else None
    risk = pick_semantic_risk(
        extract_first_falsifier(horizons["today"]),
        today_thesis,
        unusual,
        first_meaningful_line(sections["What's new since last run"]),
        first_meaningful_line(sections["Balance sheet and capital allocation"]),
        extract_first_falsifier(next((item for item in ledger.get("predictions", []) if isinstance(item, dict) and str(item.get("horizon", "")).lower().strip() in {"today", "1 day", "1d"}), None) if isinstance(ledger.get("predictions"), list) else None),
        first_meaningful_line(sections["Deep dive on earnings / major catalysts"]),
    )
    social = first_meaningful_line(sections["Social-media / public-discussion signals"])
    calibration = first_meaningful_line(sections["Historical calibration review"])
    adjustments = first_meaningful_line(sections["Research adjustments based on past accuracy"])

    # Heuristic opportunity/risk scoring for ranking only.
    opp = 0.0
    risk_score = 0.0
    today_dir = horizons["today"]["direction"]
    today_conf = horizons["today"]["confidence"] or 0
    if status == "generated":
        opp += 8
    if today_dir in {"up", "flat_to_up"}:
        opp += 18
    if horizons["30d"]["direction"] == "up":
        opp += 12
    if horizons["90d"]["direction"] == "up":
        opp += 7
    if horizons["1y"]["direction"] == "up":
        opp += 6
    opp += today_conf * 0.7
    if mytutopia["vel5"] is not None:
        opp += max(min(mytutopia["vel5"], 20), -20) * 1.1
        risk_score += max(-mytutopia["vel5"], 0) * 1.4
    if mytutopia["rsi"] is not None:
        if 50 <= mytutopia["rsi"] <= 75:
            opp += 6
        if mytutopia["rsi"] >= 80:
            risk_score += 10 + (mytutopia["rsi"] - 80) * 0.9
        elif mytutopia["rsi"] <= 35:
            risk_score += (35 - mytutopia["rsi"]) * 0.5
    if pct is not None and pct < -2:
        risk_score += abs(pct) * 1.4
    if today_dir in {"down", "flat_to_down"}:
        risk_score += 10
    if today_conf:
        risk_score += max(today_conf - 50, 0) * 0.35 if today_dir in {"down", "flat_to_down"} else 0
    if status != "generated":
        risk_score += 12
    opp = round(opp, 2)
    risk_score = round(risk_score, 2)

    return {
        "ticker": ticker,
        "company": company,
        "status": status,
        "note_date": note_path.stem if note_path else None,
        "note_path": str(note_path) if note_path else None,
        "reference_price": ref,
        "current_price": current,
        "current_label": current_label,
        "current_time": current_time,
        "pct_vs_ref": pct,
        "mytutopia": mytutopia,
        "today": horizons["today"],
        "30d": horizons["30d"],
        "90d": horizons["90d"],
        "1y": horizons["1y"],
        "unusual_signal": unusual or "n/a",
        "top_catalyst": catalyst or "n/a",
        "top_risk": risk or "n/a",
        "social_note": social or "n/a",
        "calibration_note": calibration or "n/a",
        "adjustment_note": adjustments or "n/a",
        "google_finance_method": clean_text(str(ledger.get("google_finance_method") or ledger.get("google_finance_access") or extract_google_method(body) or "n/a")),
        "_opp_score": opp,
        "_risk_score": risk_score,
    }


def market_bullets(cards: list[dict[str, Any]]) -> list[str]:
    generated = [c for c in cards if c["status"] == "generated"]
    basis = generated if generated else [c for c in cards if c["status"] in {"generated", "stale"}]
    upish = [c for c in basis if c["today"]["direction"] in {"up", "flat_to_up"}]
    downish = [c for c in basis if c["today"]["direction"] in {"down", "flat_to_down"}]
    hot = [c for c in basis if isinstance(c["mytutopia"]["rsi"], (int, float)) and c["mytutopia"]["rsi"] >= 75]
    neg_vel = [c for c in basis if isinstance(c["mytutopia"]["vel5"], (int, float)) and c["mytutopia"]["vel5"] < 0]
    big_red = [c for c in basis if isinstance(c["pct_vs_ref"], (int, float)) and c["pct_vs_ref"] <= -2.0]
    semi = [c for c in basis if c["ticker"] in {"NVDA", "MU", "LRCX", "ARM", "ASML", "TSM", "SIMO", "AMD"}]
    software = [c for c in basis if c["ticker"] in {"FSLY", "NET"}]

    bullets = []
    if not generated:
        note_dates = sorted(str(c.get("note_date")) for c in basis if c.get("note_date"))
        latest_note_date = note_dates[-1] if note_dates else "n/a"
        bullets.append(f"No same-day ticker notes were found for this cycle, so the dashboard falls back to the latest available notes/ledgers, which currently top out at {latest_note_date}.")
        bullets.append(f"On that fallback set, {len(upish)} names leaned up or flat-to-up and {len(downish)} leaned flat-to-down or down across the most recent available calls.")
    else:
        bullets.append(f"Coverage is {len(generated)}/{len(cards)} same-day notes; {len(upish)} names lean up or flat-to-up, while {len(downish)} lean flat-to-down or down.")
    if hot:
        bullets.append(f"Momentum remains crowded in parts of AI semis: high-RSI names include {', '.join(c['ticker'] for c in hot[:5])}, which caps 1-day confidence even when longer-horizon calls stay constructive.")
    if neg_vel:
        bullets.append(f"Several setups still show damaged or cooling 5-bar momentum ({', '.join(c['ticker'] for c in neg_vel[:5])}), so the regime is selective rather than a clean all-clear risk-on tape.")
    if big_red:
        bullets.append(f"Premarket weakness is concentrated in {', '.join(c['ticker'] for c in big_red[:4])}, which looks more like stock-specific digestion and overhangs than a universal breakdown in the AI/semi complex.")
    if semi:
        bullets.append(f"Semiconductor / infrastructure names still dominate the medium-term upside stack: {', '.join(c['ticker'] for c in sorted(semi, key=lambda x: x['_opp_score'], reverse=True)[:4])} carry the strongest multi-horizon constructive bias.")
    if software:
        bullets.append("Software-edge names remain more idiosyncratic than the semis: NET and FSLY are still trading as special situations driven by credibility, ownership, and reset dynamics rather than simple sector beta.")
    bullets.append("The most common pattern is constructive 30D/90D/1Y framing paired with lower-conviction same-day calls, meaning tape damage is tactical while the business thesis often stays intact.")
    bullets.append("Calibration lessons continue to point to range-width discipline: recent misses skew more toward undershooting move magnitude than getting the broad direction wrong.")
    return bullets[:8]


def headline_from_cards(cards: list[dict[str, Any]]) -> str:
    generated = [c for c in cards if c["status"] == "generated"]
    basis = generated if generated else [c for c in cards if c["status"] in {"generated", "stale"}]
    upish = sum(1 for c in basis if c["today"]["direction"] in {"up", "flat_to_up"})
    downish = sum(1 for c in basis if c["today"]["direction"] in {"down", "flat_to_down"})
    hot = sum(1 for c in basis if isinstance(c["mytutopia"]["rsi"], (int, float)) and c["mytutopia"]["rsi"] >= 75)
    if not generated:
        return "No same-day stock notes were available, so this dashboard is a clearly labeled stale fallback built from the latest prior run artifacts."
    if downish > upish:
        return "Long-horizon AI and semiconductor theses remain broadly intact, but today's tape is skewing defensive, crowded, and digestion-heavy."
    if hot >= 3:
        return "The book still leans constructive on AI infrastructure, but many leaders are overbought enough that same-day conviction is capped and risk management matters more than fresh chasing."
    return "The cross-ticker read stays constructive overall, but today still looks selective rather than a broad clean risk-on continuation."


def telegram_summary(data: dict[str, Any]) -> str:
    opps = ", ".join(x["ticker"] for x in data["top_opportunities"][:2]) or "n/a"
    risks = ", ".join(x["ticker"] for x in data["top_risks"][:2]) or "n/a"
    covered = len(data["coverage"]["generated"])
    total = sum(len(v) for v in data["coverage"].values())
    if covered == 0:
        return f"No same-day ticker notes were available. Showing latest stale fallback notes for {total}/{total} tracked names. Top stale opportunities: {opps}. Top stale risks: {risks}."
    return f"{data['headline']} Coverage {covered}/{total}. Top opportunities: {opps}. Top risks: {risks}."


def build_html(data: dict[str, Any]) -> str:
    app_json = json.dumps(data, ensure_ascii=False)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Daily Stock Summary {data['date']}</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{{--bg:#07111f;--bg2:#0d1a30;--panel:#0d182bcc;--panel2:#122342ee;--line:#94a3b82e;--text:#e5eefb;--muted:#93a4c5;--green:#4ade80;--red:#f87171;--cyan:#22d3ee;--purple:#a78bfa;color-scheme:dark}}
    *{{box-sizing:border-box}} body{{margin:0;min-height:100vh;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;background:radial-gradient(circle at top,#16305f 0%,var(--bg) 52%);color:var(--text);padding:max(18px,env(safe-area-inset-top)) 14px max(26px,env(safe-area-inset-bottom))}}
    main{{max-width:1420px;margin:0 auto}} h1,h2,h3,p{{margin:0}} .muted{{color:var(--muted)}}
    .hero{{background:linear-gradient(180deg,#234676f2,#0b1527f5);border:1px solid var(--line);border-radius:24px;padding:20px}}
    .panel{{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:18px;margin-top:18px}}
    .kpis,.hero-grid,.chart-grid,.mini-grid,.card-grid,.price-grid,.metric-grid,.horizon-grid,.signal-grid{{display:grid;gap:14px}}
    .kpis{{grid-template-columns:repeat(5,minmax(0,1fr));margin-top:16px}} .hero-grid{{grid-template-columns:1.35fr .85fr;margin-top:16px}} .chart-grid,.mini-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}} .card-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .kpi,.box,.mini-card,.ticker-card,.chart-box{{background:#122342dd;border:1px solid var(--line);border-radius:18px;padding:14px}}
    .kpi .value{{font-size:24px;font-weight:700;margin-top:6px}} .chip,.badge,.btn{{display:inline-flex;align-items:center;justify-content:center;padding:7px 12px;border-radius:999px;border:1px solid var(--line);background:#ffffff0d;color:var(--text);font-size:12px}}
    .chip.generated{{background:#4ade8020;color:#c4ff8a}} .chip.stale{{background:#fbbf2420;color:#fde68a}} .chip.missing{{background:#f8717120;color:#fecaca}}
    .badge.up{{background:#4ade8020;color:#9ff4bf}} .badge.down{{background:#f8717120;color:#fecaca}} .badge.flat,.badge.neutral{{background:#a78bfa20;color:#e0d0ff}}
    .controls,.chips,.mini-meta,.topline,.ticker-line{{display:flex;flex-wrap:wrap;gap:8px}} .topline{{justify-content:space-between;align-items:center}} .ticker-line{{align-items:center}}
    .company,.label,.small,.path{{color:var(--muted)}} .label,.small{{display:block;font-size:12px;margin-bottom:4px}} .small{{text-transform:uppercase;letter-spacing:.08em}} .pos{{color:var(--green)}} .neg{{color:var(--red)}}
    .price-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}} .metric-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}} .horizon-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}} .signal-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}
    .thesis,.signal,.pathbox,.summary-box,.detail-box{{background:#ffffff08;border:1px solid #ffffff10;border-radius:14px;padding:10px 12px}} .thesis p,.signal p,.mini-card p,li{{line-height:1.5;color:#dae6fb}}
    .stock-points{{margin:10px 0 0;padding-left:20px}} .stock-points li{{margin:0 0 6px}}
    details.stock-details{{margin-top:10px}} details.stock-details summary{{cursor:pointer;color:var(--cyan);font-weight:600;list-style:none}} details.stock-details summary::-webkit-details-marker{{display:none}} details.stock-details[open] summary{{margin-bottom:10px}}
    .controls input,.controls select{{background:#ffffff0d;color:var(--text);border:1px solid var(--line);border-radius:12px;padding:10px 12px;min-height:42px}} .btn.active{{border-color:var(--cyan);box-shadow:0 0 0 1px #22d3ee55 inset}}
    .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px}} table{{width:100%;border-collapse:collapse;min-width:1040px;background:var(--panel2)}} th,td{{padding:10px 12px;border-bottom:1px solid #ffffff12;text-align:left;font-size:13px;vertical-align:top}} th button{{all:unset;cursor:pointer;color:#d9e9ff;font-weight:700}}
    canvas{{width:100%!important;height:320px!important}}
    @media (max-width:980px){{.kpis,.hero-grid,.chart-grid,.mini-grid,.card-grid,.price-grid,.metric-grid,.horizon-grid,.signal-grid{{grid-template-columns:1fr!important}} canvas{{height:260px!important}}}}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <div class="muted">Daily stock synthesis · {data['date']} · generated {data['generated_at']}</div>
    <h1 style="margin-top:6px;font-size:clamp(28px,5vw,44px)">Daily Stock Summary Mini App</h1>
    <p style="margin-top:10px;font-size:16px;line-height:1.55;max-width:980px">{data['headline']}</p>
    <div class="kpis" id="kpis"></div>
    <div class="hero-grid">
      <div class="box">
        <strong>Executive summary</strong>
        <div class="summary-box" style="margin-top:10px">{telegram_summary(data)}</div>
        <ul id="marketBullets" style="margin-top:10px;padding-left:20px"></ul>
      </div>
      <div class="box">
        <strong>Coverage</strong>
        <div class="chips" id="coverageChips" style="margin-top:10px"></div>
        <p style="margin-top:12px">Top 2 opportunities: <span id="topOpps"></span></p>
        <p style="margin-top:6px">Top 2 risks: <span id="topRisks"></span></p>
      </div>
    </div>
  </section>

  <section class="panel"><h2>Market read</h2><ul id="marketBullets2" style="padding-left:20px;margin:10px 0 0"></ul></section>
  <section class="panel"><h2>Top opportunities</h2><div class="mini-grid" id="oppGrid"></div></section>
  <section class="panel"><h2>Top risks</h2><div class="mini-grid" id="riskGrid"></div></section>
  <section class="panel"><h2>Charts</h2><div class="chart-grid"><div class="chart-box"><canvas id="confidenceChart"></canvas></div><div class="chart-box"><canvas id="rsiVelChart"></canvas></div></div></section>
  <section class="panel"><h2>Scan controls</h2><div class="controls"><input id="searchBox" type="search" placeholder="Filter tickers or company"><select id="sortSelect"><option value="ticker">Sort: ticker</option><option value="confidence">Sort: today confidence</option><option value="rsi">Sort: RSI</option><option value="vel5">Sort: VEL5</option><option value="pct">Sort: % vs ref</option><option value="opp">Sort: opportunity score</option><option value="risk">Sort: risk score</option></select><button class="btn active" data-filter="all">All</button><button class="btn" data-filter="generated">Same-day</button><button class="btn" data-filter="bullish">Bullish bias</button><button class="btn" data-filter="downish">Flat-to-down/down</button><button class="btn" data-filter="risk">High risk</button><button class="btn" data-filter="stale">Stale</button><button class="btn" data-filter="missing">Missing</button></div><div class="card-grid" id="cardGrid"></div></section>
  <section class="panel"><h2>Sortable ticker table</h2><div class="table-wrap"><table><thead><tr><th><button data-sort="ticker">Ticker</button></th><th><button data-sort="company">Company</button></th><th><button data-sort="status">Status</button></th><th><button data-sort="direction">Today</button></th><th><button data-sort="confidence">Conf</button></th><th>Ref</th><th>Current/Premarket</th><th><button data-sort="pct">% vs ref</button></th><th><button data-sort="rsi">RSI</button></th><th><button data-sort="vel5">VEL5</button></th><th>Gate</th><th>Today range</th><th>30D</th></tr></thead><tbody id="tableBody"></tbody></table></div><div class="path" style="margin-top:14px">Source: Obsidian daily-stock research notes and prediction ledgers. This page is a synthesis, not a fresh research run.</div></section>
</main>
<script>
let tg = null;
try {{ tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null; }} catch (e) {{ tg = null; console.warn('Telegram bridge detection failed in browser preview', e); }}
if (tg) {{ try {{ tg.ready(); tg.expand(); document.body.dataset.telegram = 'true'; }} catch (e) {{ console.warn('Telegram bridge unavailable in browser preview', e); }} }}

const APP_DATA = {app_json};
const cards = APP_DATA.cards.slice();
let activeFilter = 'all';
const filterButtons = Array.from(document.querySelectorAll('.btn[data-filter]'));
const sortSelect = document.getElementById('sortSelect');
const searchBox = document.getElementById('searchBox');
function fmtPrice(v){{ return typeof v === 'number' ? `$${{v.toFixed(2)}}` : 'n/a'; }}
function fmtPct(v){{ return typeof v === 'number' ? `${{v >= 0 ? '+' : ''}}${{v.toFixed(2)}}%` : 'n/a'; }}
function esc(s){{ const div = document.createElement('div'); div.textContent = (s ?? 'n/a'); return div.innerHTML; }}
function badge(direction){{ const d = String(direction || 'n/a'); const cls = d === 'up' ? 'up' : (d === 'down' ? 'down' : (d.startsWith('flat') ? 'flat' : 'neutral')); return `<span class="badge ${{cls}}">${{esc(d)}}</span>`; }}
function num(v, fallback=-999999){{ return typeof v === 'number' && !Number.isNaN(v) ? v : fallback; }}
function renderHeader(){{
  const covered = APP_DATA.coverage.generated.length; const allCount = cards.length;
  const upCount = cards.filter(c => c.status === 'generated' && ['up','flat_to_up'].includes(c.today.direction)).length;
  const hotRsi = cards.filter(c => c.status === 'generated' && num(c.mytutopia.rsi, -1) >= 70).length;
  const negVel = cards.filter(c => c.status === 'generated' && num(c.mytutopia.vel5, 1) < 0).length;
  document.getElementById('kpis').innerHTML = [
    ['Same-day coverage', `${{covered}}/${{allCount}}`],
    ['Today up / flat-up', `${{upCount}}`],
    ['Today flat-down / down', `${{cards.filter(c => c.status === 'generated' && ['flat_to_down','down'].includes(c.today.direction)).length}}`],
    ['High RSI names (≥70)', `${{hotRsi}}`],
    ['Negative VEL5 names', `${{negVel}}`],
  ].map(([k,v]) => `<div class="kpi"><div class="muted">${{k}}</div><div class="value">${{v}}</div></div>`).join('');
  document.getElementById('coverageChips').innerHTML = `<span class="chip generated">Generated: ${{esc(APP_DATA.coverage.generated.join(', ') || 'none')}}</span><span class="chip stale">Stale: ${{esc(APP_DATA.coverage.stale.join(', ') || 'none')}}</span><span class="chip missing">Missing: ${{esc(APP_DATA.coverage.missing.join(', ') || 'none')}}</span>`;
  document.getElementById('topOpps').textContent = APP_DATA.top_opportunities.slice(0,2).map(x => x.ticker).join(', ') || 'n/a';
  document.getElementById('topRisks').textContent = APP_DATA.top_risks.slice(0,2).map(x => x.ticker).join(', ') || 'n/a';
  const bulletsHtml = APP_DATA.market_bullets.map(x => `<li>${{esc(x)}}</li>`).join('');
  document.getElementById('marketBullets').innerHTML = bulletsHtml; document.getElementById('marketBullets2').innerHTML = bulletsHtml;
}}
function miniCard(card, mode){{
  if(mode === 'opp') return `<div class="mini-card"><div class="topline"><strong>${{esc(card.ticker)}}</strong>${{badge(card.today.direction)}}</div><div class="company" style="margin-top:6px">${{esc(card.company)}}</div><p>${{esc(card.today.thesis || 'n/a')}}</p><div class="mini-meta"><span>Conf ${{card.today.confidence ?? 'n/a'}}</span><span>RSI ${{card.mytutopia.rsi ?? 'n/a'}}</span><span>VEL5 ${{card.mytutopia.vel5 ?? 'n/a'}}</span></div></div>`;
  return `<div class="mini-card"><div class="topline"><strong>${{esc(card.ticker)}}</strong><span class="badge neutral">Risk ${{card._risk_score}}</span></div><div class="company" style="margin-top:6px">${{esc(card.company)}}</div><p>${{esc(card.top_risk || 'n/a')}}</p><div class="mini-meta"><span>Today ${{esc(card.today.direction)}}</span><span>${{fmtPct(card.pct_vs_ref)}}</span></div></div>`;
}}
function renderTopSections(){{ document.getElementById('oppGrid').innerHTML = APP_DATA.top_opportunities.map(c => miniCard(c, 'opp')).join(''); document.getElementById('riskGrid').innerHTML = APP_DATA.top_risks.map(c => miniCard(c, 'risk')).join(''); }}
function passesFilter(card){{ if(activeFilter === 'all') return true; if(activeFilter === 'generated') return card.status === 'generated'; if(activeFilter === 'stale') return card.status === 'stale'; if(activeFilter === 'missing') return card.status === 'missing'; if(activeFilter === 'bullish') return ['up','flat_to_up'].includes(card.today.direction); if(activeFilter === 'downish') return ['flat_to_down','down','flat'].includes(card.today.direction); if(activeFilter === 'risk') return num(card.mytutopia.rsi,-1) >= 75 || num(card.mytutopia.vel5,1) < 0 || ['flat_to_down','down'].includes(card.today.direction); return true; }}
function passesSearch(card){{ const q = searchBox.value.trim().toLowerCase(); if(!q) return true; return [card.ticker,card.company,card.unusual_signal,card.top_catalyst,card.top_risk,card.calibration_note].join(' ').toLowerCase().includes(q); }}
function sortCards(a,b){{ const key = sortSelect.value; if(key === 'ticker') return a.ticker.localeCompare(b.ticker); if(key === 'company') return a.company.localeCompare(b.company); if(key === 'confidence') return num(b.today.confidence) - num(a.today.confidence); if(key === 'rsi') return num(b.mytutopia.rsi) - num(a.mytutopia.rsi); if(key === 'vel5') return num(b.mytutopia.vel5) - num(a.mytutopia.vel5); if(key === 'pct') return num(b.pct_vs_ref) - num(a.pct_vs_ref); if(key === 'opp') return num(b._opp_score) - num(a._opp_score); if(key === 'risk') return num(b._risk_score) - num(a._risk_score); return 0; }}
function tickerCard(card){{
  const pctClass = typeof card.pct_vs_ref === 'number' && card.pct_vs_ref < 0 ? 'neg' : 'pos';
  const statusLabel = card.status === 'generated' ? 'same-day' : card.status;
  const pointItems = [
    ['Catalyst', card.top_catalyst],
    ['Unusual', card.unusual_signal],
    ['Risk', card.top_risk],
  ].map(([label, text]) => `<li><strong>${{esc(label)}}:</strong> ${{esc(text || 'n/a')}}</li>`).join('');
  const predictionLine = `${{String(card.today.direction || 'n/a').replaceAll('_', ' ')}} · conf ${{card.today.confidence ?? 'n/a'}} · today range ${{fmtPrice(card.today.low)}} - ${{fmtPrice(card.today.high)}}`;
  return `<article class="ticker-card"><div class="topline"><div><div class="ticker-line"><h3 style="margin:0">${{esc(card.ticker)}}</h3><span class="chip ${{esc(card.status)}}">${{esc(statusLabel)}}${{card.note_date ? ' · ' + esc(card.note_date) : ''}}</span></div><div class="company" style="margin-top:4px">${{esc(card.company)}}</div></div>${{badge(card.today.direction)}}</div><div class="thesis" style="margin-top:10px"><span class="label">Prediction</span><strong>${{esc(predictionLine)}}</strong></div><ul class="stock-points">${{pointItems}}</ul><details class="stock-details"><summary>Expand details</summary><div class="detail-box"><div class="price-grid"><div><span class="label">Ref close</span><strong>${{fmtPrice(card.reference_price)}}</strong></div><div><span class="label">${{esc(card.current_label)}}</span><strong>${{fmtPrice(card.current_price)}}</strong></div><div><span class="label">vs ref</span><strong class="${{pctClass}}">${{fmtPct(card.pct_vs_ref)}}</strong></div></div><div class="metric-grid" style="margin-top:10px"><div><span class="label">RSI</span><strong>${{card.mytutopia.rsi ?? 'n/a'}}</strong></div><div><span class="label">VEL5</span><strong>${{card.mytutopia.vel5 ?? 'n/a'}}</strong></div><div><span class="label">Gate</span><strong>${{esc(card.mytutopia.momentum_gate || 'n/a')}}</strong></div><div><span class="label">Today conf</span><strong>${{card.today.confidence ?? 'n/a'}}</strong></div></div><div class="horizon-grid" style="margin-top:10px"><div><span class="small">30D</span><div>${{badge(card['30d'].direction)}}</div><div>${{fmtPrice(card['30d'].low)}} - ${{fmtPrice(card['30d'].high)}}</div></div><div><span class="small">90D</span><div>${{badge(card['90d'].direction)}}</div><div>${{fmtPrice(card['90d'].low)}} - ${{fmtPrice(card['90d'].high)}}</div></div><div><span class="small">1Y</span><div>${{badge(card['1y'].direction)}}</div><div>${{fmtPrice(card['1y'].low)}} - ${{fmtPrice(card['1y'].high)}}</div></div></div><div class="signal-grid" style="margin-top:10px"><div class="signal"><span class="small">Today thesis</span><p>${{esc(card.today.thesis || 'n/a')}}</p></div><div class="signal"><span class="small">Calibration note</span><p>${{esc(card.calibration_note)}}</p></div><div class="signal"><span class="small">Google Finance access</span><p>${{esc(card.google_finance_method || 'n/a')}}</p></div><div class="signal"><span class="small">Social signal</span><p>${{esc(card.social_note || 'n/a')}}</p></div></div></div></details></article>`;
}}
function row(card){{ return `<tr><td>${{esc(card.ticker)}}</td><td>${{esc(card.company)}}</td><td>${{esc(card.status)}}</td><td>${{esc(card.today.direction)}}</td><td>${{card.today.confidence ?? 'n/a'}}</td><td>${{fmtPrice(card.reference_price)}}</td><td>${{fmtPrice(card.current_price)}}</td><td>${{fmtPct(card.pct_vs_ref)}}</td><td>${{card.mytutopia.rsi ?? 'n/a'}}</td><td>${{card.mytutopia.vel5 ?? 'n/a'}}</td><td>${{esc(card.mytutopia.momentum_gate || 'n/a')}}</td><td>${{fmtPrice(card.today.low)}} - ${{fmtPrice(card.today.high)}}</td><td>${{esc(card['30d'].direction)}} · ${{fmtPrice(card['30d'].low)}} - ${{fmtPrice(card['30d'].high)}}</td></tr>`; }}
function renderCardsAndTable(){{ const ordered = cards.filter(c => passesFilter(c) && passesSearch(c)).sort(sortCards); document.getElementById('cardGrid').innerHTML = ordered.map(tickerCard).join(''); document.getElementById('tableBody').innerHTML = ordered.map(row).join(''); }}
function renderCharts(){{ const generated = cards.filter(c => c.status === 'generated'); new Chart(document.getElementById('confidenceChart'), {{ type:'bar', data:{{ labels:generated.map(c=>c.ticker), datasets:[{{ label:'Today confidence', data:generated.map(c=>c.today.confidence ?? null), backgroundColor:generated.map(c => ['up','flat_to_up'].includes(c.today.direction) ? 'rgba(74,222,128,.75)' : (c.today.direction === 'down' ? 'rgba(248,113,113,.75)' : 'rgba(167,139,250,.75)')), borderRadius:8 }}] }}, options:{{ responsive:true, maintainAspectRatio:false, scales:{{ y:{{ beginAtZero:true,max:100,ticks:{{color:'#c8d6f0'}} }}, x:{{ticks:{{color:'#c8d6f0'}}}} }}, plugins:{{ legend:{{labels:{{color:'#e5eefb'}}}} }} }} }});
  new Chart(document.getElementById('rsiVelChart'), {{ type:'scatter', data:{{ datasets:[{{ label:'RSI vs VEL5', data:generated.filter(c => typeof c.mytutopia.rsi === 'number' && typeof c.mytutopia.vel5 === 'number').map(c => ({{x:c.mytutopia.rsi,y:c.mytutopia.vel5,ticker:c.ticker}})), backgroundColor:'rgba(34,211,238,.85)', pointRadius:7, pointHoverRadius:8 }}] }}, options:{{ responsive:true, maintainAspectRatio:false, plugins:{{ legend:{{labels:{{color:'#e5eefb'}}}}, tooltip:{{callbacks:{{label:(ctx)=>`${{ctx.raw.ticker}} · RSI ${{ctx.raw.x}} · VEL5 ${{ctx.raw.y}}`}}}} }}, scales:{{ x:{{ title:{{display:true,text:'RSI',color:'#c8d6f0'}}, ticks:{{color:'#c8d6f0'}}, grid:{{color:'rgba(255,255,255,.08)'}} }}, y:{{ title:{{display:true,text:'VEL5',color:'#c8d6f0'}}, ticks:{{color:'#c8d6f0'}}, grid:{{color:'rgba(255,255,255,.08)'}} }} }} }} }});
  if(window.Chart && typeof window.Chart.getChart === 'function') {{ window.__miniappChartsOk = !!Chart.getChart(document.getElementById('confidenceChart')) && !!Chart.getChart(document.getElementById('rsiVelChart')); }}
}}
filterButtons.forEach(btn => btn.addEventListener('click', () => {{ activeFilter = btn.dataset.filter; filterButtons.forEach(b => b.classList.toggle('active', b === btn)); renderCardsAndTable(); }}));
sortSelect.addEventListener('change', renderCardsAndTable); searchBox.addEventListener('input', renderCardsAndTable); document.querySelectorAll('th button[data-sort]').forEach(btn => btn.addEventListener('click', () => {{ sortSelect.value = btn.dataset.sort; renderCardsAndTable(); }}));
renderHeader(); renderTopSections(); renderCardsAndTable(); renderCharts();
</script>
</body>
</html>'''


def main() -> None:
    cards = [build_card(ticker, DATE) for ticker in TICKERS]
    data = {
        "date": DATE,
        "generated_at": GENERATED_AT,
        "headline": headline_from_cards(cards),
        "coverage": {
            "generated": [c["ticker"] for c in cards if c["status"] == "generated"],
            "stale": [c["ticker"] for c in cards if c["status"] == "stale"],
            "missing": [c["ticker"] for c in cards if c["status"] == "missing"],
        },
        "cards": cards,
    }
    data["market_bullets"] = market_bullets(cards)
    data["top_opportunities"] = sorted(cards, key=lambda c: (c["status"] != "generated", -c["_opp_score"], c["ticker"]))[:4]
    data["top_risks"] = sorted(cards, key=lambda c: (c["status"] != "generated", -c["_risk_score"], c["ticker"]))[:4]
    data["telegram_summary"] = telegram_summary(data)

    html_path = REPO / f"daily-stock-summary-{DATE}.html"
    json_path = REPO / f"daily-stock-summary-{DATE}.json"
    html_path.write_text(build_html(data))
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(json.dumps({"html": str(html_path), "json": str(json_path), "coverage": data["coverage"], "headline": data["headline"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
