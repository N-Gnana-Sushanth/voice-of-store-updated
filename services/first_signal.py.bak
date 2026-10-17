"""FIRST SIGNAL: conservative local clustering by store + issue + time window."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
from services.classifier import classify_feedback, is_mandatory_escalation

OWNERS = {
    "food_safety":"Store Ops","allergen_label":"Store Ops","hygiene":"Store Ops",
    "staff_misconduct":"HR","billing":"Digital","payment_failure":"Digital",
    "stockout":"Supply Chain","freezer_failure":"Store Ops","pricing":"Merchandising","other":"Unassigned"
}
HIGH_RISK = {"food_safety","allergen_label","hygiene","staff_misconduct"}

def dt(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def detect_signals(records, window_hours=72, min_reports=2):
    buckets = defaultdict(list)
    for r in records:
        issue = r.get("issue_type") or classify_feedback(r.get("original_text",""))["issue_type"]
        store = str(r.get("store_id") or "").strip()
        if not store: continue
        text = r.get("original_text") or r.get("text") or ""
        mandatory = is_mandatory_escalation(issue, text)
        # Safety categories can signal on a single report; ordinary issues need repeated evidence.
        if mandatory or issue in HIGH_RISK:
            buckets[(store,issue,"critical")].append(r)
        else:
            buckets[(store,issue,"cluster")].append(r)
    signals = []
    for (store,issue,kind), items in buckets.items():
        items = sorted(items,key=lambda x:dt(x.get("timestamp")))
        if kind == "cluster":
            recent = [r for r in items if dt(items[-1].get("timestamp")) - dt(r.get("timestamp")) <= timedelta(hours=window_hours)]
            if len(recent) < min_reports: continue
            items = recent
        # Stable ID per store/issue prevents duplicate incident creation across refreshes.
        sid = hashlib.sha1(f"{store}|{issue}".encode()).hexdigest()[:10].upper()
        first, latest = dt(items[0].get("timestamp")), dt(items[-1].get("timestamp"))
        sev = "High" if issue in HIGH_RISK else ("Medium" if len(items) >= min_reports else "Low")
        if any(is_mandatory_escalation(issue, r.get("original_text","")) for r in items): sev = "High"
        quotes = [str(r.get("original_text","")).strip()[:220] for r in items[:3] if str(r.get("original_text","")).strip()]
        signals.append({
            "id":f"FS-{sid}", "store_id":store, "issue_type":issue,
            "summary":f"{issue.replace('_',' ').title()} reports at {store}",
            "why_raised":("Mandatory safety/staff-risk keyword detected; escalate regardless of volume." if sev=="High" and issue in HIGH_RISK else f"{len(items)} related reports at one store within the configured {window_hours}-hour window."),
            "report_count":len(items), "first_seen":first.isoformat(), "latest_seen":latest.isoformat(),
            "severity":sev, "department":OWNERS.get(issue,"Unassigned"),
            "due_at":(latest+timedelta(hours=4 if sev=="High" else 24 if sev=="Medium" else 72)).isoformat(),
            "next_action":"Review original evidence, contact the store, and record a verification decision.",
            "feedback_ids":[str(r.get("id")) for r in items if r.get("id")],
            "quotes":quotes
        })
    return sorted(signals,key=lambda x:(x["severity"]!="High",-x["report_count"],x["store_id"]))
