"""Cross-channel de-duplication and multi-channel evidence clustering."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import difflib
import re
from typing import List, Dict, Any, Tuple, Optional

from services.classifier import normalize_text

def parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def text_similarity(s1: str, s2: str) -> float:
    """Compute normalized text similarity using hybrid word Jaccard, char 3-grams, and sequence alignment."""
    s1_clean = normalize_text(s1)
    s2_clean = normalize_text(s2)
    if not s1_clean or not s2_clean:
        return 0.0
    if s1_clean == s2_clean:
        return 1.0

    w1 = set(s1_clean.split())
    w2 = set(s2_clean.split())
    wj = len(w1 & w2) / len(w1 | w2) if (w1 | w2) else 0.0

    sh1 = set(s1_clean[i:i+3] for i in range(max(len(s1_clean) - 2, 1)))
    sh2 = set(s2_clean[i:i+3] for i in range(max(len(s2_clean) - 2, 1)))
    cj = len(sh1 & sh2) / len(sh1 | sh2) if (sh1 | sh2) else 0.0

    seq = difflib.SequenceMatcher(None, s1_clean, s2_clean).ratio()
    return round(0.35 * wj + 0.35 * cj + 0.30 * seq, 4)

def find_cross_channel_duplicates(
    records: List[Dict[str, Any]],
    similarity_threshold: float = 0.70,
    window_hours: int = 48,
    require_different_channels: bool = True
) -> List[Dict[str, Any]]:
    """Identify duplicate or near-duplicate customer reports across channels for the same store."""
    # Group by store
    by_store = defaultdict(list)
    for r in records:
        sid = str(r.get("store_id") or "").strip().upper()
        if sid:
            by_store[sid].append(r)

    duplicate_pairs = []
    for store_id, store_recs in by_store.items():
        sorted_recs = sorted(store_recs, key=lambda x: parse_dt(x.get("timestamp")))
        n = len(sorted_recs)
        for i in range(n):
            r1 = sorted_recs[i]
            t1 = parse_dt(r1.get("timestamp"))
            ch1 = str(r1.get("channel") or "unknown").lower()
            txt1 = str(r1.get("original_text") or r1.get("text") or "")

            for j in range(i + 1, n):
                r2 = sorted_recs[j]
                t2 = parse_dt(r2.get("timestamp"))
                diff_hours = (t2 - t1).total_seconds() / 3600.0

                if diff_hours > window_hours:
                    break # Records sorted by time; further records will be outside window

                ch2 = str(r2.get("channel") or "unknown").lower()
                if require_different_channels and ch1 == ch2:
                    continue # Only cross-channel matching

                txt2 = str(r2.get("original_text") or r2.get("text") or "")
                sim = text_similarity(txt1, txt2)
                if sim >= similarity_threshold:
                    duplicate_pairs.append({
                        "store_id": store_id,
                        "canonical_id": r1.get("id"),
                        "duplicate_id": r2.get("id"),
                        "channel_1": ch1,
                        "channel_2": ch2,
                        "similarity_score": sim,
                        "time_difference_hours": round(diff_hours, 2),
                        "text_1": txt1,
                        "text_2": txt2
                    })

    return duplicate_pairs

def cluster_cross_channel_incidents(
    incidents: List[Dict[str, Any]],
    feedback_records: List[Dict[str, Any]],
    window_hours: int = 48
) -> List[Dict[str, Any]]:
    """Enrich incidents with multi-channel corroboration metrics."""
    fb_map = {str(r.get("id")): r for r in feedback_records}
    
    enriched = []
    for inc in incidents:
        fids = inc.get("feedback_ids") or []
        linked_records = [fb_map[fid] for fid in fids if fid in fb_map]
        channels = sorted(list(set(str(r.get("channel") or "staff_note").lower() for r in linked_records)))
        
        is_cross_channel = len(channels) > 1
        enriched.append({
            **inc,
            "channel_count": len(channels),
            "channels_involved": channels,
            "is_cross_channel_corroborated": is_cross_channel,
            "channel_diversity_note": (
                f"Corroborated across {len(channels)} distinct channels: {', '.join(channels)}"
                if is_cross_channel else f"Single-channel report ({channels[0] if channels else 'unknown'})"
            )
        })
    return enriched
