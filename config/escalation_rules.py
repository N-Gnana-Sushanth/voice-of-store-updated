"""Safety override and escalation rules for high-risk retail categories."""
import re
from typing import Tuple, Optional

# Safety categories that trigger mandatory escalation regardless of model confidence or volume
CRITICAL_SAFETY_CATEGORIES = {
    "allergen_label",
    "food_safety",
    "hygiene",
    "staff_misconduct",
    "expired_stock_on_shelf",
    "health_safety_violation",
}

# Explicit keyword patterns that immediately mandate safety escalation (English, Tamil, Telugu, Hindi, Marathi)
SAFETY_OVERRIDE_RULES = [
    ("allergen_label", [
        "allergen", "allergy", "anaphylaxis", "peanut", "nut warning", "wrong label", "ingredient label", "undeclared allergen",
        "ஒவ்வாமை", "நிலக்கடலை", "வேர்க்கடலை", "அலர்ஜி",
        "అలెర్జీ", "అలర్జీ", "వేరుశెనగ", "పల్లీలు",
        "एलर्जी", "एलर्जेन", "मूंगफली",
        "ॲलर्जी", "अलर्जी", "शेंगदाणे",
    ]),
    ("food_safety", [
        "food poisoning", "contaminated", "foreign object", "unsafe food", "raw chicken", "stomach illness", "vomit", "salmonella", "e coli",
        "வாந்தி", "உணவு விஷம்", "உணவு விஷமானது", "கோழிக்கறி சாப்பிட்ட பிறகு", "பச்சை சிக்கன்",
        "వాంతులు", "వాంతి", "ఫుడ్ పాయిజనింగ్", "కలుషితమైన", "పచ్చి చికెన్",
        "उल्टी", "उल्टियां", "फूड पॉइजनिंग", "कच्चा चिकन", "बासी खाना",
        "उलटी", "उलट्या", "अन्न विषबाधा", "कच्चे चिकन", "पोट बिघडले",
    ]),
    ("hygiene", [
        "pest", "cockroach", "rat", "mice", "rodent", "mold", "mould", "infestation", "droppings",
        "கரப்பான் பூச்சிகள்", "கரப்பான் பூச்சி", "எலி", "எலிகள்",
        "బొద్దింకలు", "బొద్దింక", "ఎలుకలు", "ఎలుక",
        "कॉकरोच", "तिलचट्टा", "चूहा", "चूहे",
        "झुरळ", "झुरळे", "उंदीर",
    ]),
    ("staff_misconduct", [
        "harassment", "abusive staff", "threatened", "discrimination", "assault", "slur", "physical violence",
        "மிரட்டினார்", "தாக்கினார்", "அநாகரீகமாக",
        "బెదిరించారు", "దాడి చేశారు",
        "धमकी दी", "गाली दी", "मारा",
        "धमकी दिली", "शिवीगाळ",
    ]),
    ("expired_stock_on_shelf", [
        "expired food", "past expiry", "outdated milk", "spoiled baby food", "best before expired",
        "காலாவதியான", "காலாவதி", "గడువు ముగిసిన", "ఎక్స్‌పైరీ", "एक्सपायर्ड", "कालबाह्य",
    ]),
    ("health_safety_violation", [
        "fire exit blocked", "electric shock", "exposed wire", "gas leak", "chemical spill", "ceiling collapse",
        "தீ விபத்து", "எலக்ட்ரிக் ஷாக்", "करंट", "गैस लीक",
    ]),
]

def check_safety_override(normalized_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Inspect text for immediate high-severity safety triggers.
    
    Returns:
        (is_override, issue_type, severity)
    """
    for issue_type, terms in SAFETY_OVERRIDE_RULES:
        for term in terms:
            # For ASCII terms, enforce word boundary to avoid false substrings (e.g., 'nut' in 'minute')
            # For non-ASCII Indic terms, direct substring matching is reliable and handles matras
            if term.isascii():
                if re.search(r"\b" + re.escape(term) + r"\b", normalized_text):
                    return True, issue_type, "Critical" if issue_type in {"expired_stock_on_shelf", "health_safety_violation"} else "High"
            else:
                if term in normalized_text:
                    return True, issue_type, "Critical" if issue_type in {"expired_stock_on_shelf", "health_safety_violation"} else "High"
    return False, None, None
