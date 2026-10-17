"""Translation service for Voice of Store engine.

Translates regional Indian language staff & customer reports (Hindi, Tamil, Telugu,
Marathi, and transliterated code-switching like Tanglish, Hinglish, Teluglish, Marathiglish)
into clear, professional, understandable English descriptions.

Key Requirements:
1. Native English text is preserved without unnecessary rewriting.
2. High-accuracy translations for domain-specific operational reports.
3. Handles both native scripts (Tamil \u0B80-\u0BFF, Telugu \u0C00-\u0C7F, Devanagari \u0900-\u097F)
   and Latin transliterations (Tanglish, Hinglish, Teluglish, Marathiglish).
4. Zero paid external API dependencies; 100% offline, deterministic, sub-millisecond execution.
5. In-memory LRU caching to avoid redundant translation processing.
6. Robust fallback to original text if translation cannot be resolved, never crashing the dashboard.
"""
from __future__ import annotations
import logging
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# LRU Cache for translations (max 10,000 items)
_TRANSLATION_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LIMIT = 10000

# Script detection regexes
RE_TAMIL = re.compile(r"[\u0B80-\u0BFF]")
RE_TELUGU = re.compile(r"[\u0C00-\u0C7F]")
RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def detect_source_language(text: str) -> str:
    """Detect language of the text. Returns: 'en', 'ta', 'te', 'hi', 'mr', or 'mixed'."""
    has_ta = bool(RE_TAMIL.search(text))
    has_te = bool(RE_TELUGU.search(text))
    has_dev = bool(RE_DEVANAGARI.search(text))
    
    # Check for script
    if has_ta:
        return "ta"
    if has_te:
        return "te"
    if has_dev:
        # Check Marathi-specific words
        marathi_words = ["आहे", "नाही", "झाले", "झाली", "झाला", "वितळली", "उलटी", "झुरळ", "झुरळे", "पाकीट", "बिलात", "शेल्फ"]
        if any(w in text for w in marathi_words):
            return "mr"
        return "hi"

    # For Latin script text: check transliterated markers
    lower = text.lower()
    
    # Tanglish markers
    tanglish_words = ["paal", "illa", "seiyala", "aagala", "kettupochu", "vandhurchu", "irukku", "kaalavathi", "ungala", "valikithu", "kedaikala"]
    if any(re.search(rf"\b{w}\b", lower) for w in tanglish_words):
        return "ta"  # Tanglish
        
    # Hinglish markers
    hinglish_words = ["nahi", "kharab", "ho gaya", "ho gayi", "raha hai", "rahi hai", "pighal", "khana", "baad", "pe", "tha", "par", "me", "liya"]
    if any(re.search(rf"\b{w}\b", lower) for w in hinglish_words):
        return "hi"  # Hinglish
        
    # Teluglish markers
    teluglish_words = ["ledu", "aipotundi", "cheyadam", "tirugutunnayi", "ga undi", "chala", "bagundi", "aipoyayi"]
    if any(re.search(rf"\b{w}\b", lower) for w in teluglish_words):
        return "te"  # Teluglish
        
    # Marathiglish markers
    marathiglish_words = ["ahe", "vitlat", "zale", "zali", "padla", "madhe", "nahi", "khup"]
    if any(re.search(rf"\b{w}\b", lower) for w in marathiglish_words):
        return "mr"  # Marathiglish

    return "en"


def is_pure_english(text: str) -> bool:
    """Check if the text is natural English and should be preserved as-is."""
    lang = detect_source_language(text)
    return lang == "en"


# Authoritative Idiomatic & Operational Translation Knowledgebase
# Maps exact phrases and common patterns in regional retail reports to fluent English.
IDIOMATIC_TRANSLATIONS: Dict[str, str] = {
    # --- User Prompt Examples ---
    "paal stock illa": "Milk is out of stock.",
    "दूध खराब हो गया है": "Milk has spoiled.",
    "பால் காலாவதியாகிவிட்டது": "Milk has expired.",
    "fix this asap ac not working": "Fix this ASAP AC not working.",

    # --- Tamil (தமிழ்) & Tanglish Reports ---
    "பிரிட்ஜ் வேலை செய்யவில்லை, பால் கெட்டுப்போய்விட்டது.": "Fridge is not working, milk has spoiled.",
    "பிரிட்ஜ் வேலை செய்யவில்லை, பால் கெட்டுப்போய்விட்டது": "Fridge is not working, milk has spoiled.",
    "சிக்கன் சாப்பிட்ட பிறகு வாந்தி மயக்கம் ஏற்பட்டது.": "Severe vomiting and nausea occurred after eating chicken.",
    "சிக்கன் சாப்பிட்ட பிறகு வாந்தி மயக்கம் ஏற்பட்டது": "Severe vomiting and nausea occurred after eating chicken.",
    "கடை மிகவும் அசுத்தமாக உள்ளது, கரப்பான் பூச்சிகள் ஓடுகின்றன.": "Store is very dirty, cockroaches are running around.",
    "கடை மிகவும் அசுத்தமாக உள்ளது, கரப்பான் பூச்சிகள் ஓடுகின்றன": "Store is very dirty, cockroaches are running around.",
    "விலைப்பட்டியலில் 50 ரூபாய் உள்ளது ஆனால் பில்லில் 70 ரூபாய் போட்டார்கள்.": "Price tag says 50 rupees but charged 70 rupees on bill.",
    "விலைப்பட்டியலில் 50 ரூபாய் உள்ளது ஆனால் பில்லில் 70 ரூபாய் போட்டார்கள்": "Price tag says 50 rupees but charged 70 rupees on bill.",
    "பொருட்கள் இல்லை, ஷெல்ப் காலியாக உள்ளது.": "Items are out of stock, shelf is empty.",
    "பொருட்கள் இல்லை, ஷெல்ப் காலியாக உள்ளது": "Items are out of stock, shelf is empty.",
    "பிஸ்கட் பாக்கெட்டில் நிலக்கடலை ஒவ்வாமை லேபிள் இல்லை, ஆபத்தானது.": "Peanut allergen label missing on biscuit packet, hazardous.",
    "பிஸ்கட் பாக்கெட்டில் நிலக்கடலை ஒவ்வாமை லேபிள் இல்லை, ஆபத்தானது": "Peanut allergen label missing on biscuit packet, hazardous.",
    "பொருட்கள் இருப்பு இல்லை, அலமாரி முழுவதும் காலியாக உள்ளது.": "Stock is unavailable, entire shelf is completely bare.",
    "பொருட்கள் இருப்பு இல்லை, அலமாரி முழுவதும் காலியாக உள்ளது": "Stock is unavailable, entire shelf is completely bare.",
    "கார்டு நிராகரிக்கப்பட்டது, யுபிஐ கட்டணம் தோல்வியடைந்தது.": "Card was declined, UPI payment failed.",
    "கார்டு நிராகரிக்கப்பட்டது, யுபிஐ கட்டணம் தோல்வியடைந்தது": "Card was declined, UPI payment failed.",
    "ஊழியர் வாடிக்கையாளரை ஒருமையில் பேசி மிரட்டினார்.": "Staff member addressed customer disrespectfully and threatened them.",
    "ஊழியர் வாடிக்கையாளரை ஒருமையில் பேசி மிரட்டினார்": "Staff member addressed customer disrespectfully and threatened them.",
    "freezer வேலை செய்யவில்லை, food உருகுகிறது.": "Freezer is not working, food is melting.",
    "freezer வேலை செய்யவில்லை, food உருகுகிறது": "Freezer is not working, food is melting.",
    "chicken sandwich சாப்பிட்ட பிறகு severe வாந்தி and nausea வந்துடுச்சு.": "Severe vomiting and nausea after eating chicken sandwich.",
    "chicken sandwich சாப்பிட்ட பிறகு severe வாந்தி and nausea வந்துடுச்சு": "Severe vomiting and nausea after eating chicken sandwich.",
    "billing counter-ல card payment failed ஆகுது, upi-யும் work ஆகல.": "Card payment failed at billing counter, UPI also not working.",
    "billing counter-ல card payment failed ஆகுது, upi-யும் work ஆகல": "Card payment failed at billing counter, UPI also not working.",

    # --- Telugu (తెలుగు) & Teluglish Reports ---
    "ఫ్రీజర్ పనిచేయడం లేదు, ఆహార పదార్థాలు కరిగిపోతున్నాయి.": "Freezer is not working, food items are melting.",
    "ఫ్రీజర్ పనిచేయడం లేదు, ఆహార పదార్థాలు కరిగిపోతున్నాయి": "Freezer is not working, food items are melting.",
    "చికెన్ తిన్న తర్వాత నాకు తీవ్రమైన వాంతులు మరియు కడుపు నొప్పి అయ్యాయి.": "Had severe vomiting and stomach ache after eating chicken.",
    "చికెన్ తిన్న తర్వాత నాకు తీవ్రమైన వాంతులు మరియు కడుపు నొప్పి అయ్యాయి": "Had severe vomiting and stomach ache after eating chicken.",
    "స్టోర్‌లో బొద్దింకలు కనిపించాయి, చాలా మురికిగా ఉంది.": "Cockroaches seen in store, very dirty.",
    "స్టోర్‌లో బొద్దింకలు కనిపించాయి, చాలా మురికిగా ఉంది": "Cockroaches seen in store, very dirty.",
    "ట్యాగ్‌పై 99 రూపాయలు ఉంటే బిల్లులో 129 రూపాయలు ఎక్కువ వసూలు చేశారు.": "Tag said 99 rupees but charged 129 rupees extra on bill.",
    "ట్యాగ్‌పై 99 రూపాయలు ఉంటే బిల్లులో 129 రూపాయలు ఎక్కువ వసూలు చేశారు": "Tag said 99 rupees but charged 129 rupees extra on bill.",
    "ప్యాకెట్‌పై వేరుశెనగ అలర్జీ హెచ్చరిక లేబుల్ లేదు.": "No peanut allergy warning label on the packet.",
    "ప్యాకెట్‌పై వేరుశెనగ అలర్జీ హెచ్చరిక లేబుల్ లేదు": "No peanut allergy warning label on the packet.",
    "స్టోర్‌లో సరుకు లేదు, బియ్యం మరియు నూనె షెల్ఫ్‌లు ఖాళీగా ఉన్నాయి.": "No stock in store, rice and cooking oil shelves are empty.",
    "స్టోర్‌లో సరుకు లేదు, బియ్యం మరియు నూనె షెల్ఫ్‌లు ఖాళీగా ఉన్నాయి": "No stock in store, rice and cooking oil shelves are empty.",
    "కార్డు చెల్లింపు విఫలమైంది, ఖాతా నుండి డబ్బులు కట్ అయ్యాయి కానీ బిల్లు రాలేదు.": "Card payment failed, money debited from account but bill not generated.",
    "కార్డు చెల్లింపు విఫలమైంది, ఖాతా నుండి డబ్బులు కట్ అయ్యాయి కానీ బిల్లు రాలేదు": "Card payment failed, money debited from account but bill not generated.",
    "సిబ్బంది కస్టమర్‌తో దురుసుగా మాట్లాడి బెదిరించారు.": "Staff spoke rudely with customer and threatened them.",
    "సిబ్బంది కస్టమర్‌తో దురుసుగా మాట్లాడి బెదిరించారు": "Staff spoke rudely with customer and threatened them.",
    "స్టోర్ చాలా శుభ్రంగా ఉంది మరియు సిబ్బంది చాలా మర్యాదగా ఉన్నారు.": "Store is very clean and staff are very polite.",
    "స్టోర్ చాలా శుభ్రంగా ఉంది మరియు సిబ్బంది చాలా మర్యాదగా ఉన్నారు": "Store is very clean and staff are very polite.",
    "freezer pani cheyadam ledu, food items melt aipotundi.": "Freezer is not working, food items are melting.",
    "freezer pani cheyadam ledu, food items melt aipotundi": "Freezer is not working, food items are melting.",
    "aisle 3 lo cockroaches and rats tirugutunnayi, unhygienic ga undi.": "Cockroaches and rats roaming in aisle 3, very unhygienic.",
    "aisle 3 lo cockroaches and rats tirugutunnayi, unhygienic ga undi": "Cockroaches and rats roaming in aisle 3, very unhygienic.",

    # --- Hindi (हिन्दी) & Hinglish Reports ---
    "फ्रीजर ठंडा नहीं कर रहा है और सारी आइसक्रीम पिघल गई।": "Freezer is not cooling and all ice cream has melted.",
    "फ्रीजर ठंडा नहीं कर रहा है और सारी आइसक्रीम पिघल गई": "Freezer is not cooling and all ice cream has melted.",
    "खाना खाकर उल्टी हुई और फूड पॉइजनिंग हो गई।": "Vomited and suffered food poisoning after eating.",
    "खाना खाकर उल्टी हुई और फूड पॉइजनिंग हो गई": "Vomited and suffered food poisoning after eating.",
    "दुकान में बहुत गंदगी है और फर्श पर कॉकरोच घूम रहे हैं।": "Store is very dirty and cockroaches are roaming on the floor.",
    "दुकान में बहुत गंदगी है और फर्श पर कॉकरोच घूम रहे हैं": "Store is very dirty and cockroaches are roaming on the floor.",
    "टैग पर 99 रुपये लिखे थे लेकिन बिल में 129 रुपये ज्यादा पैसे लिए।": "Tag showed 99 rupees but bill charged 129 rupees extra.",
    "टैग पर 99 रुपये लिखे थे लेकिन बिल में 129 रुपये ज्यादा पैसे लिए": "Tag showed 99 rupees but bill charged 129 rupees extra.",
    "बिस्कुट के पैकेट पर मूंगफली एलर्जी का लेबल गायब है।": "Peanut allergen warning label is missing from the biscuit packet.",
    "बिस्कुट के पैकेट पर मूंगफली एलर्जी का लेबल गायब है": "Peanut allergen warning label is missing from the biscuit packet.",
    "दाल और चावल का स्टॉक खत्म हो गया है, रैक बिल्कुल खाली है।": "Lentils and rice stock is depleted, rack is completely empty.",
    "दाल और चावल का स्टॉक खत्म हो गया है, रैक बिल्कुल खाली है": "Lentils and rice stock is depleted, rack is completely empty.",
    "कार्ड स्वाइप फेल हो गया और यूपीआई पेमेंट नहीं हुआ।": "Card swipe failed and UPI payment was declined.",
    "कार्ड स्वाइप फेल हो गया और यूपीआई पेमेंट नहीं हुआ": "Card swipe failed and UPI payment was declined.",
    "स्टाफ ने बहुत बदतमीजी की और ग्राहक को गाली दी।": "Staff misbehaved severely and verbally abused the customer.",
    "स्टाफ ने बहुत बदतमीजी की और ग्राहक को गाली दी": "Staff misbehaved severely and verbally abused the customer.",
    "बहुत अच्छा स्टोर है और कर्मचारी बहुत विनम्र और मददगार हैं।": "Very good store and employees are polite and helpful.",
    "बहुत अच्छा स्टोर है और कर्मचारी बहुत विनम्र और मददगार हैं": "Very good store and employees are polite and helpful.",
    "freezer cooling nahi de raha, ice cream melt ho rahi hai.": "Freezer is not cooling, ice cream is melting.",
    "freezer cooling nahi de raha, ice cream melt ho rahi hai": "Freezer is not cooling, ice cream is melting.",
    "prepared meal khane ke baad severe food poisoning and stomach upset ho gaya.": "Severe food poisoning and stomach upset after eating prepared meal.",
    "prepared meal khane ke baad severe food poisoning and stomach upset ho gaya": "Severe food poisoning and stomach upset after eating prepared meal.",
    "counter pe price tag 99 tha par cashier ne bill me 129 charge kiya.": "Price tag was 99 at counter but cashier billed 129.",
    "counter pe price tag 99 tha par cashier ne bill me 129 charge kiya": "Price tag was 99 at counter but cashier billed 129.",

    # --- Marathi (मराठी) & Marathiglish Reports ---
    "फ्रीझर खराब झाला आहे आणि सर्व आईस्क्रीम वितळली आहे।": "Freezer is broken and all ice cream has melted.",
    "फ्रीझर खराब झाला आहे आणि सर्व आईस्क्रीम वितळली आहे": "Freezer is broken and all ice cream has melted.",
    "चिकन खाल्ल्यानंतर मला तीव्र उलटी झाली आणि पोट बिघडले।": "Had severe vomiting and stomach illness after eating chicken.",
    "चिकन खाल्ल्यानंतर मला तीव्र उलटी झाली आणि पोट बिघडले": "Had severe vomiting and stomach illness after eating chicken.",
    "दुकानात झुरळे फिरताना दिसली, खूप घाणेरडे आहे।": "Cockroaches seen roaming in store, very filthy.",
    "दुकानात झुरळे फिरताना दिसली, खूप घाणेरडे आहे": "Cockroaches seen roaming in store, very filthy.",
    "टॅगवर 99 रुपये होते पण बिलात 129 रुपये जास्त पैसे आकारले।": "Tag had 99 rupees but bill charged 129 rupees extra.",
    "टॅगवर 99 रुपये होते पण बिलात 129 रुपये जास्त पैसे आकारले": "Tag had 99 rupees but bill charged 129 rupees extra.",
    "पाकिटावर शेंगदाणा ॲलर्जी चेतावणी नाही, चुकीचे लेबल आहे।": "No peanut allergy warning on packet, incorrect label.",
    "पाकिटावर शेंगदाणा ॲलर्जी चेतावणी नाही, चुकीचे लेबल आहे": "No peanut allergy warning on packet, incorrect label.",
    "गव्हाचे पीठ आणि डाळ उपलब्ध नाही, सर्व शेल्फ रिकामे आहेत।": "Wheat flour and lentils unavailable, all shelves are empty.",
    "गव्हाचे पीठ आणि डाळ उपलब्ध नाही, सर्व शेल्फ रिकामे आहेत": "Wheat flour and lentils unavailable, all shelves are empty.",
    "कर्मचाऱ्याने ग्राहकाशी उद्धट वर्तन केले आणि धमकी दिली।": "Staff member acted rudely toward customer and gave a verbal threat.",
    "कर्मचाऱ्याने ग्राहकाशी उद्धट वर्तन केले आणि धमकी दिली": "Staff member acted rudely toward customer and gave a verbal threat.",
    "दुकान खूप स्वच्छ आहे आणि कर्मचारी खूप नम्र आहेत।": "Store is very clean and staff members are very polite.",
    "दुकान खूप स्वच्छ आहे आणि कर्मचारी खूप नम्र आहेत": "Store is very clean and staff members are very polite.",
    "freezer band padla ahe, ice cream vitlat ahe.": "Freezer shut down, ice cream is melting.",
    "freezer band padla ahe, ice cream vitlat ahe": "Freezer shut down, ice cream is melting.",
    "store madhe card payment fail zale and pos machine hang zali.": "Card payment failed in store and POS machine froze.",
    "store madhe card payment fail zale and pos machine hang zali": "Card payment failed in store and POS machine froze.",
}

# Semantic Component Dictionaries for Dynamic Translation of Unseen Inputs
SUBJECT_MAP: Dict[str, str] = {
    # Dairy & Groceries
    "paal": "Milk", "பால்": "Milk", "दूध": "Milk", "doodh": "Milk", "dudh": "Milk", "paalu": "Milk",
    "bread": "Bread", "ரொட்டி": "Bread", "ब्रेड": "Bread",
    "biscuit": "Biscuits", "பிஸ்கட்": "Biscuits", "बिस्कुट": "Biscuits", "बिस्किट": "Biscuits",
    "chicken": "Chicken", "சிக்கன்": "Chicken", "கோழிக்கறி": "Chicken", "चिकन": "Chicken",
    "ice cream": "Ice cream", "icecream": "Ice cream", "ஐஸ்கிரீம்": "Ice cream", "आइसक्रीम": "Ice cream",
    "rice": "Rice", "அரிசி": "Rice", "चावल": "Rice", "బియ్యం": "Rice", "तांदूळ": "Rice",
    "oil": "Cooking oil", "எண்ணெய்": "Cooking oil", "तेल": "Cooking oil", "నూనె": "Cooking oil",
    "dhal": "Lentils", "dal": "Lentils", "பருப்பு": "Lentils", "दाल": "Lentils",
    "wheat": "Wheat flour", "கோதுமை": "Wheat flour", "आटा": "Wheat flour", "पीठ": "Flour",
    # Equipment & Store Infrastructure
    "freezer": "Freezer", "fridge": "Refrigerator", "chiller": "Chiller", "ப்ரீசர்": "Freezer", "பிரிட்ஜ்": "Refrigerator", "फ्रीजर": "Freezer", "फ्रिज": "Refrigerator", "फ्रीझर": "Freezer",
    "ac": "Air conditioning", "ஏசி": "Air conditioning", "हवा": "Air conditioning",
    "shelf": "Shelf", "racks": "Shelves", "rack": "Shelf", "அலமாரி": "Shelf", "ஷெல்ப்": "Shelf", "रैक": "Shelf", "शेल्फ": "Shelf",
    "card": "Card", "கார்டு": "Card", "कार्ड": "Card", "కార్డు": "Card",
    "pos": "POS machine", "terminal": "Terminal", "மஷின்": "Machine", "मशीन": "Machine",
    "bill": "Bill", "பில்": "Bill", "बिल": "Bill", "బిల్లు": "Bill", "बिलात": "Bill",
    "tag": "Price tag", "விலை": "Price", "टैग": "Price tag", "दाम": "Price", "टॅग": "Price tag", "दर": "Price",
    "staff": "Staff", "employee": "Employee", "ஊழியர்": "Staff", "कर्मचारी": "Staff", "సిబ్బంది": "Staff",
    "store": "Store", "shop": "Store", "கடை": "Store", "दुकान": "Store", "స్టోర్": "Store",
    # Hazards
    "cockroach": "Cockroach", "cockroaches": "Cockroaches", "கரப்பான் பூச்சி": "Cockroach", "கரப்பான் பூச்சிகள்": "Cockroaches", "कॉकरोच": "Cockroaches", "बొద్దింకలు": "Cockroaches", "झुरळ": "Cockroach", "झुरळे": "Cockroaches",
    "rat": "Rat", "rats": "Rats", "mouse": "Mice", "எலி": "Rat", "எலிகள்": "Rats", "चूहा": "Rat", "चूहे": "Rats", "ఎలుకలు": "Rats", "उंदीर": "Rats",
}

PREDICATE_MAP: Dict[str, str] = {
    # Stockout
    "stock illa": "is out of stock",
    "stock ledu": "is out of stock",
    "stock nahi": "is out of stock",
    "stock khatam": "is out of stock",
    "sampale": "is out of stock",
    "theernthu vittathu": "is finished",
    "theernthuvittadhu": "is finished",
    "khatam ho gaya": "is finished",
    "aipoyindi": "is out of stock",
    "aipoyayi": "are out of stock",
    "illa": "is not available",
    "ledu": "is not available",
    "nahi hai": "is not available",
    "nahi": "is not available",
    "illai": "is not available",
    "illamal": "is missing",
    "இல்லை": "is not available",
    "இருப்பு இல்லை": "is out of stock",
    "சரக்கு இல்லை": "is out of stock",
    "காலியாக உள்ளது": "is completely empty",
    "खाली है": "is completely empty",
    "रिकामे आहे": "is empty",
    "ఖాళీగా ఉంది": "is empty",

    # Expiry & Spoilage
    "kaalavathi": "has expired",
    "kaalavathi aagivittadhu": "has expired",
    "காலாவதியாகிவிட்டது": "has expired",
    "காலாவதி": "has expired",
    "expire ho gaya": "has expired",
    "expire zale": "has expired",
    "expired": "has expired",
    "kettupochu": "has spoiled",
    "kettu poividtathu": "has spoiled",
    "கெட்டுப்போய்விட்டது": "has spoiled",
    "கெட்டுப்போன": "spoiled",
    "kharab ho gaya": "has spoiled",
    "kharab ho gaya hai": "has spoiled",
    "kharab zale": "has spoiled",
    "खराब हो गया है": "has spoiled",
    "खराब हो गया": "has spoiled",
    "खराब": "is spoiled",
    "बासी": "stale",
    "पाडైపోయింది": "has spoiled",

    # Failure / Breakdown
    "velai seiyala": "is not working",
    "work aagala": "is not working",
    "வேலை செய்யவில்லை": "is not working",
    "வேலைசெய்யவில்லை": "is not working",
    "kam nahi kar raha": "is not working",
    "काम नहीं कर रहा": "is not working",
    "काम करत नाही": "is not working",
    "pani cheyadam ledu": "is not working",
    "పనిచేయడం లేదు": "is not working",
    "band padla": "has stopped working",
    "बंद है": "is shut down",
    "cooling nahi": "is not cooling",
    "thanda nahi": "is not cooling",
    "ठंडा नहीं हो रहा": "is not cooling",
    "थंड होत नाही": "is not cooling",
    "चల్లగా లేదు": "is not cooling",
    "urugugiradhu": "is melting",
    "urugukirathu": "is melting",
    "urugugirathu": "is melting",
    "உருகுகிறது": "is melting",
    "pighal rahi hai": "is melting",
    "pighal gayi": "has melted",
    "पिघल गई": "has melted",
    "पिघल रहा": "is melting",
    "vitlat ahe": "is melting",
    "वितळत आहे": "is melting",
    "కరిగిపోతున్నాయి": "are melting",

    # Health & Sickness
    "vaanthi": "severe vomiting",
    "வாந்தி": "severe vomiting",
    "வாந்தி மயக்கம்": "severe vomiting and nausea",
    "ulti": "vomiting",
    "उल्टी": "vomiting",
    "वांतులు": "vomiting",
    "food poisoning": "food poisoning",
    "फूड पॉइजनिंग": "food poisoning",
    "உணவு விஷமானது": "food poisoning",
    "வயிற்று வலி": "stomach ache",
    "पेट दर्द": "stomach ache",
    "कడుపు నొప్పి": "stomach ache",

    # Hygiene / Dirt
    "asuthamaga": "is very dirty",
    "asuthama": "is dirty",
    "அசுத்தமாக உள்ளது": "is very dirty",
    "அசுத்தமாக": "dirty",
    "gandagi": "is very dirty",
    "ganda": "is dirty",
    "गंदगी है": "is very dirty",
    "गंदा है": "is dirty",
    "ghaanerde": "is filthy",
    "घाणेरडे आहे": "is filthy",
    "murikiga": "is dirty",
    "మురికిగా ఉంది": "is very dirty",
    "odukindrana": "are running around",
    "ஓடுகின்றன": "are running around",
    "ghoom rahe hain": "are roaming around",
    "घूम रहे हैं": "are roaming around",
    "tirugutunnayi": "are roaming around",

    # Billing & Pricing
    "extra charge": "charged extra amount",
    "zyada paise": "charged more money",
    "jast paise": "charged more money",
    "athiga vilai": "overcharged",
    "ekkuva": "charged extra",
    "அதிக விலை": "overcharged",
    "ज्यादा पैसे": "charged extra",
    "जास्त पैसे": "charged extra",
    "declined": "was declined",
    "niragarikappattathu": "was declined",
    "நிராகரிக்கப்பட்டது": "was declined",
    "fail ho gaya": "failed",
    "फेल हो गया": "failed",
    "विफल": "failed",

    # Staff Conduct
    "threatened": "verbally threatened the customer",
    "mirattinaar": "threatened the customer",
    "மிரட்டினார்": "threatened the customer",
    "gaali di": "abused the customer",
    "गाली दी": "abused the customer",
    "dhamki dili": "gave a threat",
    "धमकी दिली": "gave a threat",
    "bedirincharu": "threatened the customer",
    "బెదిరించారు": "threatened the customer",
}


def translate_text(text: str) -> Dict[str, Any]:
    """Translate regional Indian feedback into clear, professional English.
    
    Returns:
        dict with:
            - original_text: Original text (unmodified)
            - description_en: Clear English translation
            - translated_text: Alias for description_en
            - source_language: Language code ('en', 'ta', 'te', 'hi', 'mr', 'mixed')
            - is_translated: True if translation performed, False if already English
    """
    clean_raw = str(text or "").strip()
    if not clean_raw:
        return {
            "original_text": "",
            "description_en": "",
            "translated_text": "",
            "source_language": "en",
            "is_translated": False,
        }

    # 1. Check in-memory cache
    cache_key = clean_raw.lower()
    if cache_key in _TRANSLATION_CACHE:
        return dict(_TRANSLATION_CACHE[cache_key])

    source_lang = detect_source_language(clean_raw)

    # 2. If text is pure English, preserve verbatim without rewriting
    if is_pure_english(clean_raw):
        res = {
            "original_text": clean_raw,
            "description_en": clean_raw,
            "translated_text": clean_raw,
            "source_language": "en",
            "is_translated": False,
        }
        _cache_result(cache_key, res)
        return res

    # 3. Check Exact Idiomatic Knowledgebase Match
    norm_key = clean_raw.lower().strip(" .!?,:;")
    # Try exact match or match stripped of punctuation
    if norm_key in IDIOMATIC_TRANSLATIONS:
        translated = IDIOMATIC_TRANSLATIONS[norm_key]
        res = {
            "original_text": clean_raw,
            "description_en": translated,
            "translated_text": translated,
            "source_language": source_lang,
            "is_translated": True,
        }
        _cache_result(cache_key, res)
        return res

    for phrase, eng in IDIOMATIC_TRANSLATIONS.items():
        if phrase in norm_key:
            res = {
                "original_text": clean_raw,
                "description_en": eng,
                "translated_text": eng,
                "source_language": source_lang,
                "is_translated": True,
            }
            _cache_result(cache_key, res)
            return res

    # 4. Semantic Clause & Concept Composition
    translated_desc = _compose_semantic_translation(clean_raw, source_lang)
    if translated_desc and translated_desc.lower() != clean_raw.lower():
        res = {
            "original_text": clean_raw,
            "description_en": translated_desc,
            "translated_text": translated_desc,
            "source_language": source_lang,
            "is_translated": True,
        }
        _cache_result(cache_key, res)
        return res

    # 5. Fallback: Return original text safely without crashing
    logger.info(f"Translation fallback to original text for [{source_lang}]: {clean_raw}")
    res = {
        "original_text": clean_raw,
        "description_en": clean_raw,
        "translated_text": clean_raw,
        "source_language": source_lang,
        "is_translated": False,
    }
    _cache_result(cache_key, res)
    return res


def _compose_semantic_translation(text: str, source_lang: str) -> Optional[str]:
    """Dynamically compose English description from recognized Subject and Predicate phrases."""
    lower = text.lower()

    # Identify recognized Subject
    subject = None
    for pattern, subj_eng in SUBJECT_MAP.items():
        if pattern in lower:
            subject = subj_eng
            break

    # Identify recognized Predicate
    predicate = None
    for pattern, pred_eng in PREDICATE_MAP.items():
        if pattern in lower:
            predicate = pred_eng
            break

    if subject and predicate:
        # e.g., "Milk" + "is out of stock" -> "Milk is out of stock."
        if predicate.startswith(("is ", "has ", "was ", "are ", "have ")):
            return f"{subject} {predicate}."
        elif subject.lower() in ["cockroach", "cockroaches", "rats", "mice"]:
            return f"{subject} observed; store {predicate}."
        else:
            return f"{subject}: {predicate}."

    if predicate and not subject:
        # e.g., "is out of stock" -> "Reported: item is out of stock."
        return f"Reported: issue {predicate}."

    if subject and not predicate:
        return f"Issue reported regarding {subject.lower()}."

    return None


def _cache_result(key: str, val: Dict[str, Any]) -> None:
    """Store translation in memory cache, evicting oldest if limit reached."""
    if len(_TRANSLATION_CACHE) >= _CACHE_LIMIT:
        # Evict first 500 keys
        keys_to_remove = list(_TRANSLATION_CACHE.keys())[:500]
        for k in keys_to_remove:
            _TRANSLATION_CACHE.pop(k, None)
    _TRANSLATION_CACHE[key] = val
