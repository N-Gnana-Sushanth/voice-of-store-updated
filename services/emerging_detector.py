"""Statistical Emerging-Issue Detector for Voice of Store Engine.

Replaces static thresholds with a statistical detector:
- Normalizes incident rates per 1,000 feedback records.
- Maintains trailing 4-week baselines per store and per issue type.
- Performs Poisson / Z-score significance testing.
- Enforces configurable minimum count floors (e.g. 3 reports) for non-safety issues.
- Provides zero-tolerance safety bypass for mandatory safety categories (single occurrence).
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import math
from typing import Dict, Any, List, Tuple, Optional

from scipy.stats import poisson

from config.taxonomy import TAXONOMY, get_all_issue_types
from config.escalation_rules import CRITICAL_SAFETY_CATEGORIES
from services.classifier import classify_feedback, is_mandatory_escalation

def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def calculate_rate_per_thousand(count: int, total_records: int) -> float:
    """Compute normalized rate per 1,000 records."""
    if total_records <= 0:
        return float(count * 1000)
    return round((float(count) / float(total_records)) * 1000.0, 2)

def is_statistical_anomaly(
    current_count: int,
    total_current_store_records: int,
    baseline_count: int,
    total_baseline_store_records: int,
    baseline_weeks: int = 4,
    min_count_floor: int = 3,
    alpha: float = 0.05
) -> Tuple[bool, float, float, str]:
    """Test whether current week's count is statistically significantly higher than baseline.
    
    Returns:
        (is_anomaly, p_value, z_score, explanation)
    """
    # Small-store noise suppression floor
    if current_count < min_count_floor:
        return False, 1.0, 0.0, f"Below minimum count floor ({current_count} < {min_count_floor})"

    # Calculate expected mean per week from baseline
    expected_mean = max(float(baseline_count) / max(baseline_weeks, 1), 0.2)
    
    # Scale expected mean if store traffic changed significantly
    if total_baseline_store_records > 0 and total_current_store_records > 0:
        baseline_avg_vol = float(total_baseline_store_records) / max(baseline_weeks, 1)
        scale_factor = float(total_current_store_records) / max(baseline_avg_vol, 1.0)
        expected_mean = max(expected_mean * scale_factor, 0.2)

    # Poisson survival function: P(X >= current_count | lambda = expected_mean)
    p_value = float(poisson.sf(current_count - 1, expected_mean))
    
    # Z-score approximation
    variance = expected_mean
    std_dev = math.sqrt(variance)
    z_score = round((current_count - expected_mean) / std_dev, 2) if std_dev > 0 else 0.0

    is_spike = (p_value <= alpha) and (current_count > expected_mean)
    if is_spike:
        explanation = (
            f"Statistically significant spike (p={p_value:.4f} <= {alpha}, z={z_score:+.2f}). "
            f"Observed {current_count} vs expected weekly baseline {expected_mean:.1f}."
        )
    else:
        explanation = (
            f"Within normal statistical variance (p={p_value:.4f} > {alpha}, z={z_score:+.2f}). "
            f"Expected {expected_mean:.1f}, observed {current_count}."
        )

    return is_spike, p_value, z_score, explanation

def detect_emerging_issues(
    records: List[Dict[str, Any]],
    current_window_days: int = 7,
    baseline_weeks: int = 4,
    min_count_floor: int = 3,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """Scan feedback records and identify emerging issues and safety alerts."""
    if not records:
        return []

    # Sort records by timestamp
    valid_records = []
    for r in records:
        ts = parse_dt(r.get("timestamp") or r.get("created_at"))
        store = str(r.get("store_id") or "").strip().upper()
        if not store:
            continue
        text = str(r.get("original_text") or r.get("text") or "")
        issue = r.get("issue_type")
        if not issue or issue not in TAXONOMY:
            issue = classify_feedback(text)["issue_type"]
        valid_records.append({**r, "parsed_ts": ts, "store_id": store, "issue_type": issue, "text": text})

    if not valid_records:
        return []

    latest_time = max(r["parsed_ts"] for r in valid_records)
    window_cutoff = latest_time - timedelta(days=current_window_days)
    baseline_cutoff = window_cutoff - timedelta(weeks=baseline_weeks)

    current_records = [r for r in valid_records if r["parsed_ts"] >= window_cutoff]
    baseline_records = [r for r in valid_records if baseline_cutoff <= r["parsed_ts"] < window_cutoff]

    # Store-level total volumes
    current_store_vols = defaultdict(int)
    for r in current_records:
        current_store_vols[r["store_id"]] += 1

    baseline_store_vols = defaultdict(int)
    for r in baseline_records:
        baseline_store_vols[r["store_id"]] += 1

    # Issue buckets: (store_id, issue_type) -> list of items
    current_buckets = defaultdict(list)
    for r in current_records:
        current_buckets[(r["store_id"], r["issue_type"])].append(r)

    baseline_buckets = defaultdict(list)
    for r in baseline_records:
        baseline_buckets[(r["store_id"], r["issue_type"])].append(r)

    alerts = []
    for (store, issue), items in current_buckets.items():
        k_curr = len(items)
        n_curr = current_store_vols[store]
        curr_rate = calculate_rate_per_thousand(k_curr, n_curr)

        k_base = len(baseline_buckets.get((store, issue), []))
        n_base = baseline_store_vols[store]
        base_rate = calculate_rate_per_thousand(k_base, n_base)

        # Check mandatory safety bypass
        has_safety_trigger = (
            issue in CRITICAL_SAFETY_CATEGORIES or
            any(is_mandatory_escalation(issue, r["text"]) for r in items)
        )

        if has_safety_trigger:
            # Mandatory safety bypass: single occurrence triggers immediately
            alerts.append({
                "store_id": store,
                "issue_type": issue,
                "is_emerging": True,
                "detection_type": "safety_bypass",
                "current_count": k_curr,
                "current_rate_per_thousand": curr_rate,
                "baseline_count": k_base,
                "baseline_rate_per_thousand": base_rate,
                "p_value": 0.0,
                "z_score": 99.0,
                "min_floor_met": True,
                "reason": f"Mandatory safety policy bypass: immediate incident raised on {k_curr} critical report(s).",
                "records": items
            })
            continue

        # Non-safety issues: run statistical anomaly detection
        is_spike, p_val, z_sc, reason = is_statistical_anomaly(
            current_count=k_curr,
            total_current_store_records=n_curr,
            baseline_count=k_base,
            total_baseline_store_records=n_base,
            baseline_weeks=baseline_weeks,
            min_count_floor=min_count_floor,
            alpha=alpha
        )

        if is_spike:
            alerts.append({
                "store_id": store,
                "issue_type": issue,
                "is_emerging": True,
                "detection_type": "statistical_spike",
                "current_count": k_curr,
                "current_rate_per_thousand": curr_rate,
                "baseline_count": k_base,
                "baseline_rate_per_thousand": base_rate,
                "p_value": round(p_val, 4),
                "z_score": z_sc,
                "min_floor_met": True,
                "reason": reason,
                "records": items
            })

    return alerts
