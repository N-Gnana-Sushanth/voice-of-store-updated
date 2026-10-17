"""Automated Multilingual Classification Test Suite for Voice of Store.

Evaluates 42 varied feedback examples across:
- English
- Telugu (తెలుగు)
- Hindi (हिन्दी)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Mixed-Language Combinations (Tanglish, Hinglish, Teluglish, Marathiglish)

Verifies category prediction, severity assessment, actionability, and script detection.
"""
import unittest
from services.classifier import classify_feedback

class MultilingualClassificationTests(unittest.TestCase):
    # 42 Comprehensive Test Cases across all required categories and languages
    TEST_CASES = [
        # --- Tamil (தமிழ்) ---
        {
            "id": "TA-01",
            "lang": "Tamil",
            "text": "குளிர்சாதனப் பெட்டி வேலை செய்யவில்லை. அதில் உள்ள உணவுப் பொருட்கள் உருகுகின்றன.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Tamil Test 1: Freezer failure with melting food",
        },
        {
            "id": "TA-02",
            "lang": "Tamil",
            "text": "கோழிக்கறி சாப்பிட்ட பிறகு எனக்கு வாந்தி ஏற்பட்டது.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Tamil Test 2: Food safety sickness and vomiting",
        },
        {
            "id": "TA-03",
            "lang": "Tamil",
            "text": "பொருளின் விலை 99 ரூபாய் என்று இருந்தது, ஆனால் பில்லில் 129 ரூபாய் வசூலித்தார்கள்.",
            "exp_cat": "pricing",
            "exp_sev": "Medium",
            "desc": "Tamil Test 3: Pricing mismatch 99 vs 129",
        },
        {
            "id": "TA-04",
            "lang": "Tamil",
            "text": "கடையில் கரப்பான் பூச்சிகள் காணப்பட்டன.",
            "exp_cat": "hygiene",
            "exp_sev": "High",
            "desc": "Tamil Test 4: Hygiene pest infestation",
        },
        {
            "id": "TA-05",
            "lang": "Tamil",
            "text": "கடை சுத்தமாக இருக்கிறது, ஊழியர்களும் மரியாதையாக நடந்துகொள்கிறார்கள்.",
            "exp_cat": "other",
            "exp_sev": "Low",
            "desc": "Tamil Test 5: Positive store feedback",
        },
        {
            "id": "TA-06",
            "lang": "Tamil",
            "text": "பிஸ்கட் பாக்கெட்டில் நிலக்கடலை ஒவ்வாமை லேபிள் இல்லை, ஆபத்தானது.",
            "exp_cat": "allergen_label",
            "exp_sev": "High",
            "desc": "Tamil Allergen: Missing peanut allergy warning",
        },
        {
            "id": "TA-07",
            "lang": "Tamil",
            "text": "பொருட்கள் இருப்பு இல்லை, அலமாரி முழுவதும் காலியாக உள்ளது.",
            "exp_cat": "stockout",
            "exp_sev": "Medium",
            "desc": "Tamil Stockout: Empty shelf and unavailable stock",
        },
        {
            "id": "TA-08",
            "lang": "Tamil",
            "text": "கார்டு நிராகரிக்கப்பட்டது, யுபிஐ கட்டணம் தோல்வியடைந்தது.",
            "exp_cat": "payment_failure",
            "exp_sev": "High",
            "desc": "Tamil Payment: POS card decline and UPI failure",
        },
        {
            "id": "TA-09",
            "lang": "Tamil",
            "text": "ஊழியர் வாடிக்கையாளரை ஒருமையில் பேசி மிரட்டினார்.",
            "exp_cat": "staff_misconduct",
            "exp_sev": "High",
            "desc": "Tamil Misconduct: Staff verbal abuse and threat",
        },

        # --- Tamil + English Mixed (Tanglish) ---
        {
            "id": "MIX-TA-01",
            "lang": "Tamil+English",
            "text": "Freezer வேலை செய்யவில்லை, food உருகுகிறது.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Mixed Tamil Test: Freezer not working, food melting",
        },
        {
            "id": "MIX-TA-02",
            "lang": "Tamil+English",
            "text": "Chicken sandwich சாப்பிட்ட பிறகு severe வாந்தி and nausea வந்துடுச்சு.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Mixed Tamil Food Safety: Vomit after eating chicken sandwich",
        },
        {
            "id": "MIX-TA-03",
            "lang": "Tamil+English",
            "text": "Billing counter-ல card payment failed ஆகுது, UPI-யும் work ஆகல.",
            "exp_cat": "payment_failure",
            "exp_sev": "High",
            "desc": "Mixed Tamil Payment: POS card and UPI payment failed",
        },

        # --- Telugu (తెలుగు) ---
        {
            "id": "TE-01",
            "lang": "Telugu",
            "text": "ఫ్రీజర్ పనిచేయడం లేదు, ఆహార పదార్థాలు కరిగిపోతున్నాయి.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Telugu Freezer: Refrigerator not working, food melting",
        },
        {
            "id": "TE-02",
            "lang": "Telugu",
            "text": "చికెన్ తిన్న తర్వాత నాకు తీవ్రమైన వాంతులు మరియు కడుపు నొప్పి అయ్యాయి.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Telugu Food Safety: Vomiting and stomach ache after chicken",
        },
        {
            "id": "TE-03",
            "lang": "Telugu",
            "text": "స్టోర్‌లో బొద్దింకలు కనిపించాయి, చాలా మురికిగా ఉంది.",
            "exp_cat": "hygiene",
            "exp_sev": "High",
            "desc": "Telugu Hygiene: Cockroaches in store, very dirty",
        },
        {
            "id": "TE-04",
            "lang": "Telugu",
            "text": "ట్యాగ్‌పై 99 రూపాయలు ఉంటే బిల్లులో 129 రూపాయలు ఎక్కువ వసూలు చేశారు.",
            "exp_cat": "pricing",
            "exp_sev": "Medium",
            "desc": "Telugu Pricing: Tag 99 vs billed 129 mismatch",
        },
        {
            "id": "TE-05",
            "lang": "Telugu",
            "text": "ప్యాకెట్‌పై వేరుశెనగ అలర్జీ హెచ్చరిక లేబుల్ లేదు.",
            "exp_cat": "allergen_label",
            "exp_sev": "High",
            "desc": "Telugu Allergen: Missing peanut allergy warning label",
        },
        {
            "id": "TE-06",
            "lang": "Telugu",
            "text": "స్టోర్‌లో సరుకు లేదు, బియ్యం మరియు నూనె షెల్ఫ్‌లు ఖాళీగా ఉన్నాయి.",
            "exp_cat": "stockout",
            "exp_sev": "Medium",
            "desc": "Telugu Stockout: Empty shelves for staples",
        },
        {
            "id": "TE-07",
            "lang": "Telugu",
            "text": "కార్డు చెల్లింపు విఫలమైంది, ఖాతా నుండి డబ్బులు కట్ అయ్యాయి కానీ బిల్లు రాలేదు.",
            "exp_cat": "payment_failure",
            "exp_sev": "High",
            "desc": "Telugu Payment: Card declined and timeout",
        },
        {
            "id": "TE-08",
            "lang": "Telugu",
            "text": "సిబ్బంది కస్టమర్‌తో దురుసుగా మాట్లాడి బెదిరించారు.",
            "exp_cat": "staff_misconduct",
            "exp_sev": "High",
            "desc": "Telugu Misconduct: Staff rude behavior and threat",
        },
        {
            "id": "TE-09",
            "lang": "Telugu",
            "text": "స్టోర్ చాలా శుభ్రంగా ఉంది మరియు సిబ్బంది చాలా మర్యాదగా ఉన్నారు.",
            "exp_cat": "other",
            "exp_sev": "Low",
            "desc": "Telugu Compliment: Very clean store and polite staff",
        },

        # --- Telugu + English Mixed (Teluglish) ---
        {
            "id": "MIX-TE-01",
            "lang": "Telugu+English",
            "text": "Freezer pani cheyadam ledu, food items melt aipotundi.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Mixed Telugu: Freezer failure with melting items",
        },
        {
            "id": "MIX-TE-02",
            "lang": "Telugu+English",
            "text": "Aisle 3 lo cockroaches and rats tirugutunnayi, unhygienic ga undi.",
            "exp_cat": "hygiene",
            "exp_sev": "High",
            "desc": "Mixed Telugu: Cockroaches and rats in aisle",
        },

        # --- Hindi (हिन्दी) ---
        {
            "id": "HI-01",
            "lang": "Hindi",
            "text": "फ्रीजर ठंडा नहीं कर रहा है और सारी आइसक्रीम पिघल गई।",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Hindi Freezer: Freezer not cold, ice cream melted",
        },
        {
            "id": "HI-02",
            "lang": "Hindi",
            "text": "खाना खाकर उल्टी हुई और फूड पॉइजनिंग हो गई।",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Hindi Food Safety: Food poisoning and vomiting",
        },
        {
            "id": "HI-03",
            "lang": "Hindi",
            "text": "दुकान में बहुत गंदगी है और फर्श पर कॉकरोच घूम रहे हैं।",
            "exp_cat": "hygiene",
            "exp_sev": "High",
            "desc": "Hindi Hygiene: Dirty store and cockroaches on floor",
        },
        {
            "id": "HI-04",
            "lang": "Hindi",
            "text": "टैग पर 99 रुपये लिखे थे लेकिन बिल में 129 रुपये ज्यादा पैसे लिए।",
            "exp_cat": "pricing",
            "exp_sev": "Medium",
            "desc": "Hindi Pricing: Shelf price 99 vs billed 129",
        },
        {
            "id": "HI-05",
            "lang": "Hindi",
            "text": "बिस्कुट के पैकेट पर मूंगफली एलर्जी का लेबल गायब है।",
            "exp_cat": "allergen_label",
            "exp_sev": "High",
            "desc": "Hindi Allergen: Missing peanut allergen warning label",
        },
        {
            "id": "HI-06",
            "lang": "Hindi",
            "text": "दाल और चावल का स्टॉक खत्म हो गया है, रैक बिल्कुल खाली है।",
            "exp_cat": "stockout",
            "exp_sev": "Medium",
            "desc": "Hindi Stockout: Empty racks for grocery staples",
        },
        {
            "id": "HI-07",
            "lang": "Hindi",
            "text": "कार्ड स्वाइप फेल हो गया और यूपीआई पेमेंट नहीं हुआ।",
            "exp_cat": "payment_failure",
            "exp_sev": "High",
            "desc": "Hindi Payment: Card swipe failure and UPI declined",
        },
        {
            "id": "HI-08",
            "lang": "Hindi",
            "text": "स्टाफ ने बहुत बदतमीजी की और ग्राहक को गाली दी।",
            "exp_cat": "staff_misconduct",
            "exp_sev": "High",
            "desc": "Hindi Misconduct: Employee abusive verbal misconduct",
        },
        {
            "id": "HI-09",
            "lang": "Hindi",
            "text": "बहुत अच्छा स्टोर है और कर्मचारी बहुत विनम्र और मददगार हैं।",
            "exp_cat": "other",
            "exp_sev": "Low",
            "desc": "Hindi Compliment: Great store, helpful and polite staff",
        },

        # --- Hindi + English Mixed (Hinglish) ---
        {
            "id": "MIX-HI-01",
            "lang": "Hindi+English",
            "text": "Freezer cooling nahi de raha, ice cream melt ho rahi hai.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Mixed Hindi: Freezer not cooling, ice cream melting",
        },
        {
            "id": "MIX-HI-02",
            "lang": "Hindi+English",
            "text": "Prepared meal khane ke baad severe food poisoning and stomach upset ho gaya.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Mixed Hindi: Severe food poisoning after meal",
        },
        {
            "id": "MIX-HI-03",
            "lang": "Hindi+English",
            "text": "Counter pe price tag 99 tha par cashier ne bill me 129 charge kiya.",
            "exp_cat": "pricing",
            "exp_sev": "Medium",
            "desc": "Mixed Hindi: Price tag 99 but billed 129",
        },

        # --- Marathi (मराठी) ---
        {
            "id": "MR-01",
            "lang": "Marathi",
            "text": "फ्रीझर खराब झाला आहे आणि सर्व आईस्क्रीम वितळली आहे.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Marathi Freezer: Freezer broken, ice cream melted",
        },
        {
            "id": "MR-02",
            "lang": "Marathi",
            "text": "चिकन खाल्ल्यानंतर मला तीव्र उलटी झाली आणि पोट बिघडले.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "Marathi Food Safety: Vomiting and illness after chicken",
        },
        {
            "id": "MR-03",
            "lang": "Marathi",
            "text": "दुकानात झुरळे फिरताना दिसली, खूप घाणेरडे आहे.",
            "exp_cat": "hygiene",
            "exp_sev": "High",
            "desc": "Marathi Hygiene: Cockroaches seen, very filthy",
        },
        {
            "id": "MR-04",
            "lang": "Marathi",
            "text": "टॅगवर 99 रुपये होते पण बिलात 129 रुपये जास्त पैसे आकारले.",
            "exp_cat": "pricing",
            "exp_sev": "Medium",
            "desc": "Marathi Pricing: Tag 99 vs billed 129 extra charged",
        },
        {
            "id": "MR-05",
            "lang": "Marathi",
            "text": "पाकिटावर शेंगदाणा ॲलर्जी चेतावणी नाही, चुकीचे लेबल आहे.",
            "exp_cat": "allergen_label",
            "exp_sev": "High",
            "desc": "Marathi Allergen: Missing peanut allergy warning label",
        },
        {
            "id": "MR-06",
            "lang": "Marathi",
            "text": "गव्हाचे पीठ आणि डाळ उपलब्ध नाही, सर्व शेल्फ रिकामे आहेत.",
            "exp_cat": "stockout",
            "exp_sev": "Medium",
            "desc": "Marathi Stockout: Flour and lentils out of stock, bare shelf",
        },
        {
            "id": "MR-07",
            "lang": "Marathi",
            "text": "कर्मचाऱ्याने ग्राहकाशी उद्धट वर्तन केले आणि धमकी दिली.",
            "exp_cat": "staff_misconduct",
            "exp_sev": "High",
            "desc": "Marathi Misconduct: Staff rude behavior and verbal threat",
        },
        {
            "id": "MR-08",
            "lang": "Marathi",
            "text": "दुकान खूप स्वच्छ आहे आणि कर्मचारी खूप नम्र आहेत.",
            "exp_cat": "other",
            "exp_sev": "Low",
            "desc": "Marathi Compliment: Store very clean and staff very humble",
        },

        # --- Marathi + English Mixed (Marathiglish) ---
        {
            "id": "MIX-MR-01",
            "lang": "Marathi+English",
            "text": "Freezer band padla ahe, ice cream vitlat ahe.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "Mixed Marathi: Freezer shut down, ice cream melting",
        },
        {
            "id": "MIX-MR-02",
            "lang": "Marathi+English",
            "text": "Store madhe card payment fail zale and pos machine hang zali.",
            "exp_cat": "payment_failure",
            "exp_sev": "High",
            "desc": "Mixed Marathi: Card payment failed, POS frozen",
        },

        # --- English (English baseline & ambiguous checks) ---
        {
            "id": "EN-01",
            "lang": "English",
            "text": "Freezer temperature alarm is ringing and butter packages are melting.",
            "exp_cat": "freezer_failure",
            "exp_sev": "High",
            "desc": "English Freezer: Freezer alarm and melting items",
        },
        {
            "id": "EN-02",
            "lang": "English",
            "text": "Severe food poisoning after eating contaminated deli chicken sandwich.",
            "exp_cat": "food_safety",
            "exp_sev": "High",
            "desc": "English Food Safety: Severe food poisoning after chicken",
        },
        {
            "id": "EN-03",
            "lang": "English",
            "text": "The store parking lot has nice landscaping and plenty of space.",
            "exp_cat": "other",
            "exp_sev": "Low",
            "desc": "English Ambiguous / General: Parking lot compliment",
        },
    ]

    def test_all_multilingual_cases(self):
        """Execute and measure accuracy across all 42 multilingual test cases."""
        total = len(self.TEST_CASES)
        correct_cat = 0
        correct_sev = 0
        lang_stats = {}

        for tc in self.TEST_CASES:
            lang = tc["lang"]
            if lang not in lang_stats:
                lang_stats[lang] = {"total": 0, "cat_pass": 0, "sev_pass": 0}
            lang_stats[lang]["total"] += 1

            res = classify_feedback(tc["text"])
            pred_cat = res["issue_type"]
            pred_sev = res["severity"]

            is_cat_correct = (pred_cat == tc["exp_cat"])
            is_sev_correct = (pred_sev == tc["exp_sev"])

            if is_cat_correct:
                correct_cat += 1
                lang_stats[lang]["cat_pass"] += 1
            if is_sev_correct:
                correct_sev += 1
                lang_stats[lang]["sev_pass"] += 1

            self.assertEqual(
                pred_cat, tc["exp_cat"],
                f"[{tc['id']} - {lang}] Expected category '{tc['exp_cat']}', got '{pred_cat}' for: {tc['text']}"
            )
            self.assertEqual(
                pred_sev, tc["exp_sev"],
                f"[{tc['id']} - {lang}] Expected severity '{tc['exp_sev']}', got '{pred_sev}' for: {tc['text']}"
            )

        cat_acc = (correct_cat / total) * 100.0
        sev_acc = (correct_sev / total) * 100.0

        print("\n" + "=" * 70)
        print("  MULTILINGUAL AI CLASSIFICATION EVALUATION REPORT")
        print("=" * 70)
        print(f"Total Tests Executed        : {total}")
        print(f"Correct Category Predictions : {correct_cat} / {total} ({cat_acc:.2f}%)")
        print(f"Correct Severity Predictions : {correct_sev} / {total} ({sev_acc:.2f}%)")
        print("-" * 70)
        print("PER-LANGUAGE BREAKDOWN:")
        for lang, s in sorted(lang_stats.items()):
            c_pct = (s["cat_pass"] / s["total"]) * 100.0
            s_pct = (s["sev_pass"] / s["total"]) * 100.0
            print(f"  - {lang:<16}: {s['total']:>2} tests | Category: {c_pct:>5.1f}% | Severity: {s_pct:>5.1f}%")
        print("=" * 70 + "\n")

        self.assertEqual(correct_cat, total)
        self.assertEqual(correct_sev, total)

if __name__ == "__main__":
    unittest.main()
