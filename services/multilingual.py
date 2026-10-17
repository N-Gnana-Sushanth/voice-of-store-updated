"""Multilingual intelligence and classification service for Indian retail operations.

Supports:
- English
- Telugu (తెలుగు)
- Hindi (हिन्दी)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Mixed-language code-switching (e.g., Tanglish, Hinglish, Teluglish, Marathiglish)

Architecture designed for easy extension to additional Indic languages (e.g., Kannada, Malayalam, Bengali).
Operates locally with zero external API dependencies, sub-millisecond execution, and 100% offline support.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple

# Supported Language Scripts & Codes
SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "Telugu (తెలుగు)",
    "hi": "Hindi (हिन्दी)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "mixed": "Mixed-Language Code-Switching",
}

# Unicode Script Ranges
SCRIPT_RANGES = {
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "devanagari": (0x0900, 0x097F),  # Hindi / Marathi
}

def detect_languages(text: str) -> List[str]:
    """Detect presence of scripts and languages in input text."""
    langs = []
    has_tamil = any(0x0B80 <= ord(c) <= 0x0BFF for c in text)
    has_telugu = any(0x0C00 <= ord(c) <= 0x0C7F for c in text)
    has_devanagari = any(0x0900 <= ord(c) <= 0x097F for c in text)
    has_latin = any(('a' <= c <= 'z') or ('A' <= c <= 'Z') for c in text)

    if has_tamil:
        langs.append("ta")
    if has_telugu:
        langs.append("te")
    if has_devanagari:
        # Check Marathi-specific characters/markers if applicable, else both hi/mr
        langs.append("hi")
        langs.append("mr")
    if has_latin:
        langs.append("en")

    return langs or ["en"]

# Category Definitions & Multilingual Lexicons
# Maps each category to domain patterns in Tamil, Telugu, Hindi, Marathi, and Romanized/Mixed.
MULTILINGUAL_LEXICON: Dict[str, Dict[str, List[str]]] = {
    "freezer_failure": {
        "ta": [
            "குளிர்சாதனப் பெட்டி", "குளிர்சாதனப்பெட்டி", "ப்ரீசர்", "பிரீசர்",
            "வேலை செய்யவில்லை", "வேலைசெய்யவில்லை", "உருகுகின்றன", "உருகுகிறது",
            "உருகிவிட்டது", "குளிர்ச்சியாக இல்லை", "குளிர்ச்சி இல்லை",
            "பனிக்கட்டி உருகுகிறது", "ஐஸ்கிரீம் உருகுகிறது", "கெட்டுப்போகிறது",
        ],
        "te": [
            "ఫ్రీజర్", "ఫ్రిడ్జ్", "పనిచేయడం లేదు", "పనిచేయట్లేదు", "చల్లగా లేదు",
            "కరిగిపోతున్నాయి", "కరిగిపోతుంది", "ఐస్ క్రీమ్ కరిగిపోతోంది", "పాడైపోతున్నాయి",
            "కూలింగ్ లేదు", "చల్లదనం లేదు",
        ],
        "hi": [
            "फ्रीजर", "फ्रिज", "ठंडा नहीं", "ठंडा नहीं हो रहा", "पिघल रहा", "पिघल रही",
            "पिघल गई", "कूलिंग नहीं", "आइसक्रीम पिघल", "चिलर खराब", "काम नहीं कर रहा",
        ],
        "mr": [
            "फ्रीझर", "फ्रिज", "थंड होत नाही", "थंड नाही", "काम करत नाही",
            "बंद पडला", "बंद पडले", "वितळत आहे", "वितळले", "वितळत आहेत",
            "आईस्क्रीम वितळली", "खराब होत आहे", "कूलिंग होत नाही",
        ],
        "romanized": [
            "freezer", "fridge", "chiller", "cold storage", "refrigerator",
            "not cold", "not cooling", "melting", "melted", "thawing", "thawed",
            "ice cream melt", "icecream melt", "compressor dead",
            "thanda nahi", "pighal", "pani cheyadam ledu", "vitlat", "urugugirathu",
            "urugukirathu", "urugugindrana", "pani cheyatledu", "band padla",
        ],
    },
    "food_safety": {
        "ta": [
            "உணவு விஷம்", "உணவு விஷமானது", "வாந்தி", "வாந்தி ஏற்பட்டது", "வாந்தியெடுத்தேன்",
            "கோழிக்கறி சாப்பிட்ட பிறகு", "சாப்பிட்ட பிறகு உடல்நிலை சரியில்லை",
            "வயிற்றுப்போக்கு", "வயிற்று வலி", "கெட்டுப்போன உணவு", "கெட்டுப்போன சிக்கன்",
            "புழு", "பூச்சி", "பச்சை சிக்கன்", "வேகாத கோழிக்கறி",
        ],
        "te": [
            "ఫుడ్ పాయిజనింగ్", "ఫుడ్ పాయిజన్", "వాంతులు", "వాంతి", "వాంతులు అయ్యాయి",
            "కడుపు నొప్పి", "వికారం", "విరేచనాలు", "తిన్న తర్వాత అనారోగ్యం",
            "పాడైన ఆహారం", "కుళ్ళిన ఆహారం", "కలుషితమైన", "పచ్చి చికెన్", "కీటకం",
        ],
        "hi": [
            "फूड पॉइजनिंग", "उल्टी", "उल्टियां", "उल्टी हुई", "पेट खराब", "पेट दर्द",
            "बीमार पड़ गया", "बीमार हो गया", "कच्चा चिकन", "बासी खाना", "खराब खाना",
            "सड़ा हुआ", "कीड़ा निकला", "खाने में कीड़ा", "खाने में बाल", "कंटेमिनेटेड",
        ],
        "mr": [
            "अन्न विषबाधा", "उलटी", "उलट्या", "उलटी झाली", "पोट बिघडले", "पोटात दुखत",
            "खाल्ल्यानंतर आजारी", "कच्चे चिकन", "खराब अन्न", "शिळे अन्न",
            "अन्नामध्ये किडा", "अन्नामध्ये केस", "मळमळत आहे",
        ],
        "romanized": [
            "food poisoning", "vomit", "vomiting", "nausea", "stomach illness",
            "stomach ache", "stomach upset", "diarrhea", "diarrhoea", "raw chicken",
            "contaminated food", "spoiled food", "sick after eating", "food bug",
            "foreign object in food", "ulti", "pet kharab", "vaanthi", "vomits",
            "anna vishabada", "pot bighadle", "khana kharab",
        ],
    },
    "hygiene": {
        "ta": [
            "கரப்பான் பூச்சிகள்", "கரப்பான் பூச்சி", "கரப்பான்பூச்சி", "எலி", "எலிகள்",
            "அழுக்கு", "அழுக்காக", "அசுத்தம்", "அசுத்தமாக", "துர்நாற்றம்",
            "ஈக்கள்", "பூச்சிகள்", "பூஞ்சை", "கழிவறை நாற்றம்", "அசிங்கமாக",
        ],
        "te": [
            "బొద్దింకలు", "బొద్దింక", "ఎలుకలు", "ఎలుక", "మురికిగా", "మురికి",
            "దుర్వాసన", "కంపు", "అపరిశుభ్రం", "అపరిశుభ్రమైన", "బూజు", "ఈగలు",
            "చెత్త", "పురుగులు",
        ],
        "hi": [
            "कॉकरोच", "तिलचट्टा", "चूहा", "चूहे", "गंदगी", "गंदा", "गंदी",
            "बदबू", "दुर्गंध", "अस्वच्छ", "मक्खियां", "कीड़े मकोड़े", "फफूंद",
        ],
        "mr": [
            "झुरळ", "झुरळे", "उंदीर", "उंदीर फिरताना", "घाण", "घाणेरडे",
            "अस्वच्छ", "दुर्गंधी", "घाणेरडा वास", "माशा", "बुरशी", "कचरा",
        ],
        "romanized": [
            "cockroach", "cockroaches", "rat", "rats", "mouse", "mice", "rodent",
            "dirty", "filthy", "unhygienic", "pest", "pests", "infestation",
            "mold", "mould", "bad smell", "stink", "stinking", "flies",
            "karappan poochigal", "karappan poochi", "boddinkalu", "chooha",
            "zural", "zhural", "durgandhi", "ganda store",
        ],
    },
    "allergen_label": {
        "ta": [
            "ஒவ்வாமை", "ஒவ்வாமை லேபிள்", "நிலக்கடலை", "வேர்க்கடலை", "கடலை எச்சரிக்கை",
            "தவறான லேபிள்", "லேபிள் இல்லை", "பொருளடக்கம் குறிப்பிடப்படவில்லை",
            "அலர்ஜி", "அலர்ஜி எச்சரிக்கை இல்லை",
        ],
        "te": [
            "అలెర్జీ", "అలర్జీ", "వేరుశెనగ", "పల్లీలు", "తప్పుడు లేబుల్",
            "లేబుల్ లేదు", "పదార్థాల వివరాలు లేవు", "అలెర్జీ హెచ్చరిక లేదు",
        ],
        "hi": [
            "एलर्जी", "एलर्जेन", "मूंगफली", "नट वॉर्निंग", "गलत लेबल",
            "इंग्रीडिएंट लेबल नहीं", "एलर्जी चेतावनी गायब", "लेबल पर नहीं लिखा",
        ],
        "mr": [
            "ॲलर्जी", "अलर्जी", "शेंगदाणे", "चुकीचे लेबल", "लेबल नाही",
            "घटकांची यादी नाही", "ॲलर्जी चेतावणी नाही", "शेंगदाणा चेतावणी",
        ],
        "romanized": [
            "allergen", "allergy", "peanut", "nut warning", "ingredient label",
            "wrong label", "missing label", "undeclared allergen", "gluten label",
            "milk warning", "anaphylaxis", "moongphali", "shengdana", "verusenaga",
            "nilakkadalai", "ovvaamai",
        ],
    },
    "pricing": {
        "ta": [
            "பொருளின் விலை", "ரூபாய் என்று இருந்தது", "பில்லில் வசூலித்தார்கள்",
            "விலை வித்தியாசம்", "அதிக விலை வசூலித்தார்கள்", "விலை அதிகம்",
            "தவறான விலை", "லேபிளில் உள்ள விலை இல்லை", "விலை ஏமாற்று",
            "99 ரூபாய்", "129 ரூபாய்",
        ],
        "te": [
            "ధర తేడా", "ట్యాగ్‌పై ధర", "బిల్లులో ఎక్కువ", "ఎక్కువ వసూలు చేశారు",
            "తప్పుడు ధర", "ధర ఎక్కువగా ఉంది", "డిస్కౌంట్ ఇవ్వలేదు",
            "99 రూపాయలు", "129 రూపాయలు",
        ],
        "hi": [
            "गलत दाम", "कीमत में अंतर", "टैग पर कुछ और बिल में कुछ और",
            "ज्यादा पैसे लिए", "ज्यादा चार्ज किया", "एमआरपी से ज्यादा",
            "गलत रेट लगाया", "99 रुपये", "129 रुपये",
        ],
        "mr": [
            "किंमत तफावत", "जास्त पैसे आकारले", "बिलात जास्त लावले",
            "टॅगवर वेगळी किंमत", "चुकीचा दर", "जास्त पैसे घेतले",
            "दर फरक", "99 रुपये", "129 रुपये",
        ],
        "romanized": [
            "price mismatch", "wrong price", "shelf price", "charged extra",
            "billed more", "tag says", "bill says", "overpriced", "overcharged on item",
            "price tag missing", "99", "129", "discount not given",
            "zyada paise", "jast paise", "ekkuva charge", "athika vilai",
        ],
    },
    "payment_failure": {
        "ta": [
            "கட்டணம் தோல்வி", "பணம் செலுத்த முடியவில்லை", "கார்டு நிராகரிக்கப்பட்டது",
            "யுபிஐ வேலை செய்யவில்லை", "பணம் எடுக்கப்பட்டது பில் வரவில்லை",
            "ஸ்வைப் மெஷின் வேலை செய்யவில்லை",
        ],
        "te": [
            "చెల్లింపు విఫలమైంది", "కార్డు పని చేయలేదు", "కార్డు తిరస్కరించబడింది",
            "యూపీఐ ఫెయిల్", "డబ్బులు కట్ అయ్యాయి రసీదు రాలేదు",
            "పేమెంట్ కాలేదు",
        ],
        "hi": [
            "पेमेंट फेल", "भुगतान विफल", "कार्ड काम नहीं कर रहा",
            "कार्ड डिक्लाइन", "यूपीआई फेल", "पैसे कट गए रसीद नहीं मिली",
            "मशीन खराब है",
        ],
        "mr": [
            "पेमेंट अयशस्वी", "कार्ड चालत नाही", "कार्ड नाकारले",
            "युपीआय अयशस्वी", "पैसे कट झाले पावती मिळाली नाही",
            "स्वाइप मशीन बंद",
        ],
        "romanized": [
            "payment failed", "card declined", "upi failed", "pos declined",
            "transaction failed", "payment error", "card swipe failed",
            "money debited no receipt", "paise cut gaye", "payment fail",
        ],
    },
    "stockout": {
        "ta": [
            "பொருட்கள் இல்லை", "இருப்பு இல்லை", "சரக்கு இல்லை", "தீர்ந்துவிட்டது",
            "அலமாரி காலியாக உள்ளது", "எப்போது கிடைக்கும்", "கிடைக்கவில்லை",
        ],
        "te": [
            "స్టాక్ లేదు", "సరుకు లేదు", "అయిపోయింది", "ఖాళీగా ఉంది",
            "అందుబాటులో లేదు", "దొరకడం లేదు",
        ],
        "hi": [
            "स्टॉक नहीं है", "सामान खत्म", "खाली शेल्फ", "उपलब्ध नहीं है",
            "माल नहीं है", "खत्म हो गया",
        ],
        "mr": [
            "माल संपला", "स्टॉक नाही", "सामान उपलब्ध नाही", "शेल्फ रिकामे",
            "मिळत नाही", "संपले आहे",
        ],
        "romanized": [
            "out of stock", "stockout", "empty shelf", "not available", "sold out",
            "bare shelf", "unavailable", "shelf empty", "khatam ho gaya", "stock ledu",
            "saaman nahi hai", "stock illai",
        ],
    },
    "staff_misconduct": {
        "ta": [
            "ஊழியர் தகாத நடத்தை", "மரியாதைக் குறைவாக பேசினார்", "திட்டினார்",
            "மிரட்டினார்", "மோசமான நடத்தை", "அநாகரீகமாக நடந்துகொண்டார்",
        ],
        "te": [
            "సిబ్బంది దురుసు ప్రవర్తన", "దురుసుగా మాట్లాడారు", "తిట్టారు",
            "బెదిరించారు", "అసభ్యకరంగా ప్రవర్తించారు", "గౌరవం లేకుండా మాట్లాడారు",
        ],
        "hi": [
            "कर्मचारी का बुरा व्यवहार", "बदतमीजी की", "गाली दी",
            "धमकी दी", "चिल्लाया", "अपमान किया", "रूड स्टाफ",
        ],
        "mr": [
            "कर्मचाऱ्याचे गैरवर्तन", "उद्धट वर्तन", "अपमान केला",
            "धमकी दिली", "शिवीगाळ केली", "गैरवर्तन केले",
        ],
        "romanized": [
            "staff misconduct", "rude staff", "abusive staff", "threatened",
            "shouted", "insulted", "harassment", "badtameezi", "shivi dili",
            "threaten", "rude behavior",
        ],
    },
    "billing": {
        "ta": [
            "இரண்டு முறை பில் போட்டார்கள்", "தவறான பில்", "கூடுதல் பில்",
            "வாங்காத பொருளுக்கு பில்", "டபுள் சார்ஜ்",
        ],
        "te": [
            "రెండుసార్లు బిల్లు వేశారు", "తప్పుడు బిల్లు", "డబుల్ చార్జ్",
            "తీసుకోని వస్తువుకి బిల్లు", "డబ్బులు ఎక్కువ తీసుకున్నారు",
        ],
        "hi": [
            "दो बार बिल कर दिया", "गलत बिल", "डबल चार्ज", "एक्स्ट्रा आइटम जोड़ दिया",
        ],
        "mr": [
            "दोनदा बिल आकारले", "चुकीचे बिल", "डबल चार्ज", "न घेतलेल्या सामानाचे बिल",
        ],
        "romanized": [
            "charged twice", "double charge", "wrong bill", "duplicate charge",
            "billed twice", "overcharged invoice", "do baar charge",
        ],
    },
}

# Positive Feedback / Compliments Lexicon (should map to 'other', severity 'Low', actionable False)
POSITIVE_FEEDBACK_LEXICON: Dict[str, List[str]] = {
    "ta": [
        "கடை சுத்தமாக இருக்கிறது", "ஊழியர்களும் மரியாதையாக", "மரியாதையாக நடந்துகொள்கிறார்கள்",
        "நல்ல அனுபவம்", "சிறந்த சேவை", "மிகவும் பிடித்திருக்கிறது", "வாழ்த்துகள்",
        "சுத்தமாக உள்ளது", "நன்றாக இருக்கிறது", "மரியாதையாக",
    ],
    "te": [
        "స్టోర్ చాలా శుభ్రంగా ఉంది", "సిబ్బంది మర్యాదగా ఉన్నారు", "మంచి అనుభవం",
        "చాలా బాగుంది", "గొప్ప సేవ", "సహాయం చేశారు", "అభినందనలు",
    ],
    "hi": [
        "बहुत अच्छा स्टोर", "साफ-सुथरा", "कर्मचारी विनम्र हैं", "कर्मचारी मददगार हैं",
        "अच्छा अनुभव", "बहुत बढ़िया सर्विस", "धन्यवाद", "शानदार व्यवस्था",
    ],
    "mr": [
        "दुकान खूप स्वच्छ आहे", "कर्मचारी खूप नम्र आहेत", "छान अनुभव",
        "उत्कृष्ट सेवा", "खूप आवडले", "धन्यवाद", "मदत केली",
    ],
    "romanized": [
        "great store experience", "clean store", "polite staff", "helpful staff",
        "pleasant shopping", "good service", "thank you", "nice shopping",
        "bahut accha", "khup chaan", "chala bagundi", "superb store",
    ],
}

# High / Critical Severity Determinants
CRITICAL_SEVERITY_INDICATORS = [
    # Food Safety / Illness
    "வாந்தி", "வாந்தியெடுத்தேன்", "உணவு விஷம்", "மருத்துவமனை",
    "వాంతులు", "వాంతి", "ఫుడ్ పాయిజనింగ్", "ఆసుపత్రి",
    "उल्टी", "उल्टियां", "फूड पॉइजनिंग", "अस्पताल", "बीमार",
    "उलटी", "उलट्या", "अन्न विषबाधा", "दवाखाना", "रुग्णालय",
    "vomit", "vomiting", "food poisoning", "hospital", "severe illness",
    
    # Hygiene Infestation
    "கரப்பான் பூச்சிகள்", "கரப்பான் பூச்சி", "எலி", "எலிகள்",
    "బొద్దింకలు", "బొద్దింక", "ఎలుకలు", "ఎలుక",
    "कॉकरोच", "चूहा", "चूहे", "कीड़े मकोड़े",
    "झुरळ", "झुरळे", "उंदीर",
    "cockroach", "cockroaches", "rat", "rats", "rodent", "pest infestation",

    # Allergen
    "ஒவ்வாமை", "நிலக்கடலை", "வேர்க்கடலை", "அலர்ஜி",
    "అలెర్జీ", "అలర్జీ", "వేరుశెనగ", "పల్లీలు",
    "एलर्जी", "एलर्जेन", "मूंगफली",
    "ॲलर्जी", "अलर्जी", "शेंगदाणे",
    "allergen", "allergy", "peanut", "anaphylaxis",

    # Freezer Breakdown with melting food
    "உருகுகின்றன", "உருகுகிறது", "உருகிவிட்டது",
    "కరిగిపోతున్నాయి", "కరిగిపోతుంది",
    "पिघल रहा", "पिघल रही", "पिघल गई",
    "वितळत आहे", "वितळले", "वितळत आहेत",
    "melting", "melted", "thawed", "spoiling in freezer",

    # Staff Physical Danger / Threats
    "மிரட்டினார்", "அடித்தார்", "தாக்கினார்",
    "బెదిరించారు", "దాడి చేశారు",
    "धमकी दी", "मारा", "हमला",
    "धमकी दिली", "मारहाण",
    "threatened", "physical violence", "assault",
]

def is_positive_feedback(text: str) -> bool:
    """Check if feedback is predominantly positive/complimentary."""
    lower = text.lower()
    for lang, phrases in POSITIVE_FEEDBACK_LEXICON.items():
        for p in phrases:
            if p.lower() in lower:
                # Ensure no conflict with serious complaints
                has_crit = any(c in lower for c in ["வாந்தி", "உலटी", "వాంతులు", "उलटी", "vomit", "cockroach", "கரப்பான்", "झुरळ", "బొద్దింక", "தவறான", "fraud", "scam"])
                if not has_crit:
                    return True
    return False

def evaluate_multilingual_feedback(text: str) -> Optional[Dict[str, Any]]:
    """Semantically analyze feedback text across Indic and English languages.
    
    Returns structured classification dict or None if text requires statistical fallback.
    """
    clean = text.strip()
    if not clean:
        return None

    clean_lower = clean.lower()

    # 1. Check for genuine positive feedback / compliment
    if is_positive_feedback(clean):
        return {
            "issue_type": "other",
            "severity": "Low",
            "actionable": False,
            "confidence": 0.95,
            "owner_department": "Customer Experience",
            "department": "Customer Experience",
            "method": "multilingual_positive_feedback",
            "language_detected": detect_languages(clean),
        }

    # 2. Score across categories using multilingual lexicons
    scores: Dict[str, float] = {cat: 0.0 for cat in MULTILINGUAL_LEXICON}

    for cat, lang_dict in MULTILINGUAL_LEXICON.items():
        for lang_code, terms in lang_dict.items():
            for term in terms:
                term_lower = term.lower()
                if term_lower in clean_lower:
                    # Give higher weight to multi-word phrases and native scripts
                    weight = 2.0 if len(term.split()) > 1 else 1.2
                    if lang_code in ("ta", "te", "hi", "mr"):
                        weight += 0.5
                    scores[cat] += weight

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    if best_score <= 0.0:
        return None

    # 3. Contextual Severity Evaluation
    severity = "Medium" # Default operational severity

    # Check for Critical/High severity signals
    has_critical_signal = any(c.lower() in clean_lower for c in CRITICAL_SEVERITY_INDICATORS)

    if best_cat in {"food_safety", "allergen_label", "freezer_failure", "hygiene", "payment_failure"}:
        severity = "High"
    elif best_cat == "staff_misconduct":
        severity = "High" if has_critical_signal or "threat" in clean_lower or "மிரட்டல்" in clean or "धमकी" in clean else "Medium"
    elif best_cat in {"pricing", "stockout", "billing"}:
        severity = "Medium"
    else:
        from config.taxonomy import TAXONOMY
        severity = TAXONOMY.get(best_cat, {}).get("default_severity", "Medium")

    # Actionable flag
    actionable = (best_cat != "other")

    # Map department
    from config.taxonomy import TAXONOMY
    tax = TAXONOMY.get(best_cat, TAXONOMY.get("other", {}))
    department = tax.get("department", "Store Operations")

    return {
        "issue_type": best_cat,
        "severity": severity,
        "actionable": actionable,
        "confidence": min(0.85 + (best_score * 0.04), 0.99),
        "owner_department": department,
        "department": department,
        "method": "multilingual_semantic_engine",
        "language_detected": detect_languages(clean),
    }
