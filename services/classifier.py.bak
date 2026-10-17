"""Transparent baseline classifier. Replace keyword rules with the supplied taxonomy/model when available."""
import re

# Demonstration defaults only. Replace/extend using the official challenge taxonomy.
RULES = [
    ("allergen_label", ["allergen", "allergy", "wrong label", "ingredient label"]),
    ("food_safety", ["food poisoning", "contaminated", "foreign object", "unsafe food", "raw chicken"]),
    ("hygiene", ["dirty", "unhygienic", "pest", "cockroach", "rat", "mold", "mould"]),
    ("staff_misconduct", ["harassment", "abusive staff", "staff threatened", "discrimination"]),
    ("freezer_failure", ["freezer", "fridge not cold", "refrigerator", "cold storage"]),
    ("payment_failure", ["payment failed", "upi failed", "card declined", "payment error"]),
    ("billing", ["overcharged", "wrong bill", "billing error", "charged twice"]),
    ("stockout", ["out of stock", "stockout", "not available", "empty shelf"]),
    ("pricing", ["wrong price", "price mismatch", "discount missing", "price tag"]),
]
CRITICAL = {"allergen_label", "food_safety", "hygiene", "staff_misconduct"}

def normalize_text(text):
    text = str(text or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def classify_feedback(text):
    cleaned = normalize_text(text)
    for issue, terms in RULES:
        if any(term in cleaned for term in terms):
            severity = "High" if issue in CRITICAL else "Medium"
            return {"issue_type":issue,"severity":severity,"actionable":True,"confidence":0.72,
                    "method":"keyword_baseline"}
    return {"issue_type":"other","severity":"Low","actionable":False,"confidence":0.30,
            "method":"keyword_baseline"}

def is_mandatory_escalation(issue_type, text):
    """Safety-oriented trigger: low volume/confidence must not suppress a matched risk."""
    cleaned = normalize_text(text)
    extra = ["allergen", "allergy", "food poisoning", "contaminated", "cockroach",
             "mold", "mould", "harassment", "threatened", "unsafe food"]
    return issue_type in CRITICAL or any(term in cleaned for term in extra)
