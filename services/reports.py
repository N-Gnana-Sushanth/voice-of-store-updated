"""Reporting service: weekly reports, multi-region briefs, and CSV exports."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import csv
import io
import math
from typing import List, Dict, Any, Optional

from config.taxonomy import TAXONOMY
from services.store_service import get_store

def parse_dt(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def build_weekly_report(
    records: List[Dict[str, Any]],
    days: int = 7,
    owners: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """Generate weekly executive summary report with top issues, WoD trends, and escalation metrics."""
    owners = owners or {}
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    prev_start = start - timedelta(days=days)

    # Current reporting window records
    current = [r for r in records if parse_dt(r.get("timestamp")) and start <= parse_dt(r.get("timestamp")) <= now]
    # Prior reporting window for week-over-week calculation
    prior = [r for r in records if parse_dt(r.get("timestamp")) and prev_start <= parse_dt(r.get("timestamp")) < start]

    counts = Counter(r.get("issue_type", "other") for r in current)
    prior_counts = Counter(r.get("issue_type", "other") for r in prior)

    top = []
    for issue, count in counts.most_common(5):
        prior_c = prior_counts.get(issue, 0)
        diff = count - prior_c
        if prior_c > 0:
            pct = round((diff / prior_c) * 100)
            if pct > 0:
                direction = f"+{pct}% (Trending up from {prior_c})"
            elif pct < 0:
                direction = f"{pct}% (Trending down from {prior_c})"
            else:
                direction = f"0% (Stable vs prior {days}d)"
        else:
            direction = f"+{count} (New issue category this week)"

        examples = [r for r in current if r.get("issue_type", "other") == issue][:3]
        affected_stores = sorted(set(r.get("store_id", "unknown") for r in current if r.get("issue_type", "other") == issue))

        action_recommendation = {
            "allergen_label": "Execute immediate lot quarantine and audit packaging supplier labels across affected stores.",
            "food_safety": "Inspect walk-in coolers, verify HACCP temperature logs, and review sanitation standards.",
            "freezer_failure": "Dispatch commercial HVAC contractors to inspect compressors and relocate perishable inventory.",
            "payment_failure": "Review payment terminal firmware logs and verify network failover status with Digital Ops.",
            "stockout": "Reconcile DC inventory levels and request expedited cross-dock shipments for critical SKUs.",
            "billing": "Audit checkout scanner barcode accuracy and ensure register refund policy compliance.",
            "hygiene": "Deploy emergency sanitation sweep and schedule professional pest defense audit.",
            "staff_misconduct": "Conduct confidential HR interviews with store leadership and schedule service training.",
            "pricing": "Perform 100% price tag audit on promotional endcaps and calibrate shelf POS pricing.",
            "other": "Review peak customer service staffing and manager floor presence.",
        }.get(issue, "Review original evidence, contact store manager, and record corrective actions.")

        top.append({
            "issue_type": issue,
            "count": count,
            "prior_count": prior_c,
            "direction": direction,
            "department": owners.get(issue, "Store Operations"),
            "stores": affected_stores,
            "evidence": [
                {
                    "feedback_id": r.get("id"),
                    "store_id": r.get("store_id"),
                    "channel": r.get("channel"),
                    "quote": (r.get("description_en") or r.get("original_text") or "")[:240],
                    "original_quote": (r.get("original_text") or "")[:240],
                    "is_translated": bool(r.get("is_translated", 0)),
                    "source_language": r.get("source_language", "en")
                }
                for r in examples
            ],
            "recommended_action": action_recommendation,
        })

    high = [r for r in current if str(r.get("severity", "")).lower() in {"critical", "high"}]

    # Escalation Precision Calculation
    has_gt = any("ground_truth_escalated" in r and r["ground_truth_escalated"] is not None for r in current)
    if has_gt:
        tp = sum(1 for r in current if str(r.get("ground_truth_escalated")) == "1" and str(r.get("severity", "")).lower() in {"critical", "high"})
        fp = sum(1 for r in current if str(r.get("ground_truth_escalated")) == "0" and str(r.get("severity", "")).lower() in {"critical", "high"})
        fn = sum(1 for r in current if str(r.get("ground_truth_escalated")) == "1" and str(r.get("severity", "")).lower() not in {"critical", "high"})
        prec = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        rec = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        escalation_summary = {
            "status": "evaluated",
            "precision": prec,
            "recall": rec,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "note": "Calculated against ground-truth escalation tags."
        }
    else:
        escalation_summary = {
            "status": "N/A",
            "message": "Ground truth escalation labels not provided in dataset."
        }

    return {
        "period": {
            "start": start.isoformat(),
            "end": now.isoformat(),
            "days": days,
            "prior_start": prev_start.isoformat(),
        },
        "basis": "Observed customer and staff feedback volume across retail locations. No synthetic footfall denominator is assumed.",
        "feedback_count": len(current),
        "prior_feedback_count": len(prior),
        "total_active_stores": len(set(r.get("store_id") for r in current if r.get("store_id"))),
        "top_issues": top,
        "high_severity_evidence": [
            {
                "id": r.get("id"),
                "store_id": r.get("store_id"),
                "issue_type": r.get("issue_type"),
                "severity": r.get("severity"),
                "quote": (r.get("original_text") or "")[:240],
            }
            for r in high[:15]
        ],
        "escalation_precision": escalation_summary,
        "limitations": [
            "Demo records are clearly marked. In production, connect live POS, CRM, and voice feedback streams.",
            "Week-over-week trends reflect reported complaint volume within local store operating windows.",
        ],
    }

def build_multi_region_brief(
    records: List[Dict[str, Any]],
    incidents: Optional[List[Dict[str, Any]]] = None,
    days: int = 7,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """Aggregate weekly feedback, normalized complaint rates, and top issues per region."""
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    baseline_start = start - timedelta(days=28) # 4 weeks baseline
    incidents = incidents or []

    # Map each store to its region
    store_region_map = {}
    for r in records:
        sid = str(r.get("store_id") or "").strip().upper()
        if sid and sid not in store_region_map:
            st = get_store(sid)
            store_region_map[sid] = st.get("region", "Regional Operations") if st else "Regional Operations"

    # Filter records
    current_records = [r for r in records if parse_dt(r.get("timestamp")) and start <= parse_dt(r.get("timestamp")) <= now]
    baseline_records = [r for r in records if parse_dt(r.get("timestamp")) and baseline_start <= parse_dt(r.get("timestamp")) < start]

    # Group current by region
    region_records = defaultdict(list)
    for r in current_records:
        sid = str(r.get("store_id") or "").strip().upper()
        reg = store_region_map.get(sid, "Regional Operations")
        region_records[reg].append(r)

    # Group baseline by region and issue
    region_baseline_counts = defaultdict(lambda: Counter())
    for r in baseline_records:
        sid = str(r.get("store_id") or "").strip().upper()
        reg = store_region_map.get(sid, "Regional Operations")
        issue = r.get("issue_type", "other")
        region_baseline_counts[reg][issue] += 1

    # Map incidents to region
    region_incidents = defaultdict(list)
    for inc in incidents:
        sid = str(inc.get("store_id") or "").strip().upper()
        reg = store_region_map.get(sid, "Regional Operations")
        region_incidents[reg].append(inc)

    all_regions = sorted(list(set(list(region_records.keys()) + list(region_incidents.keys()))))
    if not all_regions:
        all_regions = ["Midwest Region", "Northeast Region", "West Region", "South Region", "Pacific Northwest Region"]

    regional_summaries = []
    total_feedback = len(current_records)
    total_incidents = len(incidents)

    for reg in all_regions:
        recs = region_records.get(reg, [])
        reg_incs = region_incidents.get(reg, [])
        vol = len(recs)
        
        # Severity counts from incidents
        sev_counts = Counter(inc.get("severity", "Medium") for inc in reg_incs)
        
        # Normalized rate per 1,000 feedback records
        norm_rate = round((len(reg_incs) / vol * 1000.0), 1) if vol > 0 else 0.0
        
        # Top 5 issues with normalized rates, stores, evidence quotes, and trend indicators
        issue_counter = Counter(r.get("issue_type", "other") for r in recs)
        top_issues = []
        for issue, cnt in issue_counter.most_common(5):
            # 4-week baseline average per week
            base_total = region_baseline_counts[reg].get(issue, 0)
            weekly_base = round(base_total / 4.0, 1)
            
            if weekly_base > 0:
                pct_change = round(((cnt - weekly_base) / weekly_base) * 100)
                if pct_change >= 15:
                    trend = "↑"
                    trend_label = f"+{pct_change}%"
                elif pct_change <= -15:
                    trend = "↓"
                    trend_label = f"{pct_change}%"
                else:
                    trend = "→"
                    trend_label = "0%"
            else:
                trend = "↑"
                trend_label = "New"

            issue_recs = [r for r in recs if r.get("issue_type", "other") == issue]
            issue_stores = sorted(list(set(r.get("store_id") for r in issue_recs if r.get("store_id"))))
            issue_quotes = [str(r.get("description_en") or r.get("original_text") or r.get("text") or "").strip()[:200] for r in issue_recs if str(r.get("description_en") or r.get("original_text") or r.get("text") or "").strip()][:3]
            rate_k = round((cnt / vol) * 1000.0, 1) if vol > 0 else 0.0
            policy_desc = TAXONOMY.get(issue, {}).get("policy", "Standard operational review")

            top_issues.append({
                "issue_type": issue,
                "count": cnt,
                "rate_per_k": rate_k,
                "weekly_baseline": weekly_base,
                "trend": trend,
                "trend_label": trend_label,
                "stores": issue_stores,
                "evidence_quotes": issue_quotes,
                "evidence": [{"quote": q} for q in issue_quotes],
                "escalation_reason": policy_desc,
                "department": TAXONOMY.get(issue, {}).get("department", "Store Operations")
            })

        stores_in_region = sorted(list(set(r.get("store_id") for r in recs if r.get("store_id"))))
        
        regional_summaries.append({
            "region": reg,
            "feedback_volume": vol,
            "incident_count": len(reg_incs),
            "normalized_rate_per_k": norm_rate,
            "severity_breakdown": {
                "Critical": sev_counts.get("Critical", 0),
                "High": sev_counts.get("High", 0),
                "Medium": sev_counts.get("Medium", 0),
                "Low": sev_counts.get("Low", 0),
            },
            "top_issues": top_issues,
            "active_stores": len(stores_in_region),
            "stores": stores_in_region,
            "alerts": [
                {
                    "id": inc["id"],
                    "store_id": inc["store_id"],
                    "summary": inc["summary"],
                    "severity": inc["severity"],
                    "status": inc["status"],
                    "why_raised": inc.get("why_raised") or inc.get("description") or f"Incident at {inc['store_id']}",
                    "escalation_reason": inc.get("escalation_reason") or ("Critical zero-tolerance safety escalation" if inc.get("severity") == "Critical" else inc.get("why_raised") or "Cluster threshold exceeded")
                }
                for inc in reg_incs[:5]
            ]
        })

    return {
        "period": {
            "start": start.isoformat(),
            "end": now.isoformat(),
            "days": days,
            "baseline_weeks": 4
        },
        "total_feedback": total_feedback,
        "total_incidents": total_incidents,
        "region_count": len(regional_summaries),
        "regions": regional_summaries,
        "generated_at": now.isoformat()
    }

def report_csv(report: Dict[str, Any]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "period_start",
        "period_end",
        "basis",
        "issue_type",
        "count",
        "week_over_week_direction",
        "department",
        "affected_stores",
        "evidence_quotes",
        "recommended_action"
    ])
    for item in report.get("top_issues", []):
        writer.writerow([
            report["period"]["start"],
            report["period"]["end"],
            report["basis"],
            item["issue_type"],
            item["count"],
            item.get("direction", "N/A"),
            item["department"],
            "; ".join(item["stores"]),
            " | ".join(e["quote"] for e in item["evidence"]),
            item["recommended_action"],
        ])
    return out.getvalue()
