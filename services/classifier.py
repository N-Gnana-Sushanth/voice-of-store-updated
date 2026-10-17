"""Advanced retail feedback classifier with TF-IDF char n-grams, Logistic Regression,
safety overrides, and documented rule-based fallback.
"""
from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Dict, Any, List, Optional, Tuple

from config.taxonomy import TAXONOMY, DEPARTMENTS, get_department, get_policy_info
from config.escalation_rules import CRITICAL_SAFETY_CATEGORIES, check_safety_override
from services.model_training import DEFAULT_MODEL_PATH, load_trained_model, train_classifier
from services.multilingual import evaluate_multilingual_feedback, detect_languages

# Maintain backward compatibility for direct imports
CRITICAL = set(CRITICAL_SAFETY_CATEGORIES)

# Legacy keyword rules maintained as safety overrides and rule fallback
RULES: List[Tuple[str, List[str]]] = [
    (k, v["keywords"]) for k, v in TAXONOMY.items()
]

# Legacy policies dictionary populated directly from authoritative taxonomy
POLICIES: Dict[str, Dict[str, Any]] = {
    k: {
        "policy": v["policy"],
        "description": v["description"],
        "max_response_hours": v["max_response_hours"],
        "default_owner": (
            "Dr. Elena Rostova (Food Safety Compliance)" if k in {"allergen_label", "food_safety"}
            else "Marcus Vance (Store Ops Lead)" if k == "freezer_failure"
            else "Raj Patel (Supply Chain Lead)" if v["department"] == "Supply Chain"
            else "Priya Sharma (Digital Systems)" if v["department"] == "Digital"
            else "HR People Operations Lead" if v["department"] == "HR"
            else "Facilities & Sanitation Manager" if k == "hygiene"
            else "Sarah Jenkins (CX Lead)"
        ),
        "default_department": v["department"],
        "requires_verification": v.get("is_safety", False),
    }
    for k, v in TAXONOMY.items()
}

_MODEL_CACHE: Optional[Dict[str, Any]] = None

def get_or_load_model() -> Optional[Dict[str, Any]]:
    """Return cached scikit-learn model artifact or load from disk."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if DEFAULT_MODEL_PATH.exists():
        _MODEL_CACHE = load_trained_model(DEFAULT_MODEL_PATH)
        return _MODEL_CACHE
    # Train automatically if artifact does not exist yet
    try:
        _MODEL_CACHE = train_classifier(DEFAULT_MODEL_PATH)
        return _MODEL_CACHE
    except Exception:
        return None

def normalize_text(text: str) -> str:
    """Clean and normalize input text for classification."""
    text = str(text or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def rule_based_classify(cleaned: str) -> Dict[str, Any]:
    """Documented rule-based fallback when model is unavailable or confidence is low."""
    for issue_type, terms in RULES:
        if any(term in cleaned for term in terms):
            tax = TAXONOMY.get(issue_type, TAXONOMY["other"])
            severity = tax["default_severity"]
            return {
                "issue_type": issue_type,
                "severity": severity,
                "actionable": tax["actionable"],
                "confidence": 0.85,
                "owner_department": tax["department"],
                "department": tax["department"],
                "method": "keyword_fallback",
            }
    other_tax = TAXONOMY["other"]
    return {
        "issue_type": "other",
        "severity": "Low",
        "actionable": False,
        "confidence": 0.35,
        "owner_department": other_tax["department"],
        "department": other_tax["department"],
        "method": "keyword_fallback",
    }

def classify_feedback(text: str) -> Dict[str, Any]:
    """Classify retail customer/staff feedback text.
    
    1. Safety override check: high-risk categories take immediate precedence.
    2. ML model inference: TF-IDF char n-grams + Logistic Regression.
    3. Documented fallback: Keyword rule fallback if model absent or low margin.
    """
    cleaned = normalize_text(text)
    if not cleaned:
        other_tax = TAXONOMY["other"]
        return {
            "issue_type": "other",
            "severity": "Low",
            "actionable": False,
            "confidence": 0.0,
            "owner_department": other_tax["department"],
            "department": other_tax["department"],
            "method": "empty_input",
        }

    # Step 1: Safety keyword override check
    is_safety, safety_issue, safety_sev = check_safety_override(cleaned)
    if is_safety and safety_issue:
        tax = TAXONOMY.get(safety_issue, TAXONOMY["other"])
        return {
            "issue_type": safety_issue,
            "severity": safety_sev or tax["default_severity"],
            "actionable": True,
            "confidence": 0.99,
            "owner_department": tax["department"],
            "department": tax["department"],
            "method": "safety_override",
            "language_detected": detect_languages(text),
        }

    # Step 2: Multilingual Semantic Engine (Tamil, Telugu, Hindi, Marathi, Mixed-language)
    ml_res = evaluate_multilingual_feedback(text)
    if ml_res:
        return ml_res

    # Step 3: ML Model Inference
    model_bundle = get_or_load_model()
    if model_bundle and "pipeline" in model_bundle:
        pipeline = model_bundle["pipeline"]
        try:
            probas = pipeline.predict_proba([cleaned])[0]
            max_idx = int(probas.argmax())
            pred_class = pipeline.classes_[max_idx]
            raw_conf = float(probas[max_idx])
            
            # Confidence threshold for trusting ML prediction over fallback
            if raw_conf >= 0.08 and pred_class in TAXONOMY:
                tax = TAXONOMY[pred_class]
                return {
                    "issue_type": pred_class,
                    "severity": tax["default_severity"],
                    "actionable": tax["actionable"],
                    "confidence": round(raw_conf, 4),
                    "owner_department": tax["department"],
                    "department": tax["department"],
                    "method": "tfidf_logistic_regression",
                    "language_detected": detect_languages(text),
                }
        except Exception:
            pass

    # Step 4: Documented keyword rule fallback
    fallback_res = rule_based_classify(cleaned)
    fallback_res["language_detected"] = detect_languages(text)
    return fallback_res

def classify_batch(texts: List[str]) -> List[Dict[str, Any]]:
    """Batch classification for high-throughput processing."""
    cleaned_list = [normalize_text(t) for t in texts]
    results: List[Optional[Dict[str, Any]]] = [None] * len(texts)
    unresolved_indices = []
    unresolved_texts = []

    for i, orig_t in enumerate(texts):
        c = cleaned_list[i]
        if not c:
            other_tax = TAXONOMY["other"]
            results[i] = {
                "issue_type": "other",
                "severity": "Low",
                "actionable": False,
                "confidence": 0.0,
                "owner_department": other_tax["department"],
                "department": other_tax["department"],
                "method": "empty_input",
                "language_detected": ["en"],
            }
            continue

        is_safety, safety_issue, safety_sev = check_safety_override(c)
        if is_safety and safety_issue:
            tax = TAXONOMY.get(safety_issue, TAXONOMY["other"])
            results[i] = {
                "issue_type": safety_issue,
                "severity": safety_sev or tax["default_severity"],
                "actionable": True,
                "confidence": 0.99,
                "owner_department": tax["department"],
                "department": tax["department"],
                "method": "safety_override",
                "language_detected": detect_languages(orig_t),
            }
            continue

        # Multilingual semantic check
        ml_res = evaluate_multilingual_feedback(orig_t)
        if ml_res:
            results[i] = ml_res
            continue

        unresolved_indices.append(i)
        unresolved_texts.append(c)

    if unresolved_texts:
        model_bundle = get_or_load_model()
        if model_bundle and "pipeline" in model_bundle:
            pipeline = model_bundle["pipeline"]
            try:
                proba_matrix = pipeline.predict_proba(unresolved_texts)
                for idx_pos, orig_idx in enumerate(unresolved_indices):
                    p_row = proba_matrix[idx_pos]
                    max_idx = int(p_row.argmax())
                    pred_class = pipeline.classes_[max_idx]
                    raw_conf = float(p_row[max_idx])
                    if raw_conf >= 0.08 and pred_class in TAXONOMY:
                        tax = TAXONOMY[pred_class]
                        results[orig_idx] = {
                            "issue_type": pred_class,
                            "severity": tax["default_severity"],
                            "actionable": tax["actionable"],
                            "confidence": round(raw_conf, 4),
                            "owner_department": tax["department"],
                            "department": tax["department"],
                            "method": "tfidf_logistic_regression",
                        }
                    else:
                        results[orig_idx] = rule_based_classify(unresolved_texts[idx_pos])
            except Exception:
                for idx_pos, orig_idx in enumerate(unresolved_indices):
                    results[orig_idx] = rule_based_classify(unresolved_texts[idx_pos])
        else:
            for idx_pos, orig_idx in enumerate(unresolved_indices):
                results[orig_idx] = rule_based_classify(unresolved_texts[idx_pos])

    return [r for r in results if r is not None]

def is_mandatory_escalation(issue_type: str, text: str) -> bool:
    """Safety-oriented trigger: low volume/confidence must not suppress a matched risk."""
    cleaned = normalize_text(text)
    is_safety, _, _ = check_safety_override(cleaned)
    if is_safety or issue_type in CRITICAL_SAFETY_CATEGORIES:
        return True
    extra = ["allergen", "allergy", "food poisoning", "contaminated", "cockroach",
             "mold", "mould", "harassment", "threatened", "unsafe food", "mislabel", "expired food"]
    return any(term in cleaned for term in extra)

def get_policy(issue_type: str) -> Dict[str, Any]:
    """Retrieve operational policy for a given issue type."""
    return POLICIES.get(issue_type, POLICIES["other"])

def get_highlight_terms(issue_type: str) -> List[str]:
    """Retrieve highlight indicator terms for an issue type."""
    tax = TAXONOMY.get(issue_type)
    if tax and "keywords" in tax:
        return tax["keywords"]
    return []
