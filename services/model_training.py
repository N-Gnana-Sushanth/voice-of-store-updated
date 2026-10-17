"""TF-IDF character n-gram + Logistic Regression training pipeline for retail feedback classification."""
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config.taxonomy import TAXONOMY, get_all_issue_types, get_department

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "classifier_model.joblib"

# Documented seed data templates representing noisy customer feedback, typos, Hinglish, emojis, and normal text
BOOTSTRAP_TEMPLATES: Dict[str, List[str]] = {
    "allergen_label": [
        "Possible allergen label is missing on the peanut cookie shelf.",
        "Ingredient label does not mention milk although product contains milk.",
        "Shopper asks whether cookie contains peanuts, label is unclear.",
        "Undeclared walnut in chocolate brownie, serious allergy risk!",
        "Allergy warning! Nut warning label missing on bakery items.",
        "Wrong allergen label on gluten-free section, contains wheat.",
        "Peanut allergy alert, ingredient list is completely missing from this batch.",
        "Allergen warning missing: packaging has no peanut warning sticker.",
        "Bhai cookie ke packet pe peanut allergen label nahi hai, dangerous hai.",
        "Paket pe nut warning missing hai, kisi ko severe allergy ho sakti hai.",
        "Allrgen lbel wrong on bscuit, no allergy wrning.",
        "Severe peanut allergy hazard, label omitted allergen statement.",
        "ஒவ்வாமை லேபிள் இல்லை, கடலை எச்சரிக்கை விடுபட்டுள்ளது.",
        "பொருளடக்கத்தில் நிலக்கடலை எச்சரிக்கை லேபிள் போடப்படவில்லை.",
        "ప్యాకెట్‌పై వేరుశెనగ అలర్జీ హెచ్చరిక లేబుల్ లేదు.",
        "అలర్జీ ఉన్నవారికి ప్రమాదం, సరైన లేబుల్ వేయలేదు.",
        "पैकेट पर मूंगफली एलर्जी का लेबल गायब है, खतरा हो सकता है।",
        "शेंगदाणा ॲलर्जी चेतावणी पाकिटावर नाही, चुकीचे लेबल आहे.",
        "Allergy warning missing on peanut butter jar.",
    ],
    "food_safety": [
        "Customer reported stomach illness after eating prepared chicken; investigate urgently.",
        "Raw chicken stored above ready-to-eat salad in the cooler.",
        "Found a piece of metal foreign object inside the prepared sandwich.",
        "Contaminated dairy products smelling rotten in the chilled case.",
        "Food poisoning symptoms after sushi bought this afternoon.",
        "Got severe food poisoning from the deli chicken sandwich.",
        "Customer vomited after drinking spoiled yoghurt.",
        "Foreign object found inside canned beans, looks like glass shard.",
        "Khana kharab tha, prepared meal khake stomach upset ho gaya.",
        "Chicken was completely raw inside, unsafe food serving.",
        "Stomch illnes aftr eatng spoiled meal.",
        "Contaminated ready-to-eat food causing extreme nausea.",
        "கோழிக்கறி சாப்பிட்ட பிறகு எனக்கு வாந்தி ஏற்பட்டது.",
        "உணவு சாப்பிட்ட பிறகு கடுமையான உணவு விஷம் மற்றும் வாந்தி.",
        "చికెన్ తిన్న తర్వాత నాకు తీవ్రమైన వాంతులు మరియు కడుపు నొప్పి అయ్యాయి.",
        "ఆహారం విషపూరితం అయింది, తిన్న వెంటనే వాంతి వచ్చింది.",
        "खाना खाकर उल्टी हुई और फूड पॉइजनिंग हो गई।",
        "बासी खाना खाकर पेट में दर्द और उल्टियां शुरू हो गईं।",
        "अन्न खाल्ल्यानंतर तीव्र मळमळ आणि उलटी झाली, विषबाधा.",
        "खराब अन्नामुळे पोट बिघडले आणि आजारी पडलो.",
        "Chicken khallyanantar ulti zali, severe food poison.",
    ],
    "hygiene": [
        "Cockroach seen near the back-room food preparation counter.",
        "Restroom and customer waiting area are dirty and smell unpleasant.",
        "Mould visible on bread display near the date labels.",
        "Pest droppings found beside the dry goods storage rack.",
        "Dead rat spotted under the produce display shelf.",
        "Floor is filthy and unhygienic with black grime in aisle 3.",
        "Cockroaches crawling near the bakery rack! Disgusting hygiene.",
        "Bohot dirty store hai, cockroaches roam kar rahe hain shelves pe.",
        "Restroom me bohot ganda smell hai aur pest dikha.",
        "Cokroach near foot cntr, unhygienic store.",
        "Rats and pest infestation observed near grain storage.",
        "கடையில் கரப்பான் பூச்சிகள் காணப்பட்டன.",
        "கடை மிகவும் அழுக்காக உள்ளது, எலிகள் மற்றும் துர்நாற்றம்.",
        "స్టోర్‌లో బొద్దింకలు కనిపించాయి, చాలా మురికిగా ఉంది.",
        "దుకాణంలో ఎలుకలు మరియు ఈగలు తిరుగుతున్నాయి, అపరిశుభ్రం.",
        "दुकान में बहुत गंदगी है और कॉकरोच घूम रहे हैं।",
        "फर्श पर चूहा दिखा और बहुत तेज बदबू आ रही है।",
        "दुकानात झुरळे फिरताना दिसली, खूप घाणेरडे आणि दुर्गंधी.",
        "उंदीर फिरत आहेत आणि परिसर अत्यंत अस्वच्छ आहे.",
        "Zural ahe store madhe, unhygienic condition.",
    ],
    "freezer_failure": [
        "Freezer temperature alarm is sounding and frozen items are soft.",
        "Chiller display reads above safe range; dairy products feel warm.",
        "Freezer still warm; several frozen packages are partly thawed.",
        "Ice cream freezer compressor making loud noise and tubs are melting.",
        "Walk-in cold storage unit shut down, meat thawing rapidly.",
        "Freezer is not cold at all, butter and cheese are dripping.",
        "Freezer completely warm! All frozen peas and ice creams melting.",
        "Freezer thanda nahi kar raha, sab frozen khana pighal gaya.",
        "Chiller warm hai, fridge cooling nahi de raha.",
        "frezer not cld, icecrem mlting in freezer cabinet.",
        "frezer is wrm and iccream is mlting",
        "Refrigeration failure in aisle 4, cold storage compressor dead.",
        "குளிர்சாதனப் பெட்டி வேலை செய்யவில்லை. அதில் உள்ள உணவுப் பொருட்கள் உருகுகின்றன.",
        "Freezer வேலை செய்யவில்லை, food உருகுகிறது.",
        "ஃபிரீசர் குளிர்ச்சியாக இல்லை, ஐஸ்கிரீம் எல்லாம் உருகிவிட்டது.",
        "ఫ్రీజర్ పనిచేయడం లేదు, ఆహార పదార్థాలు కరిగిపోతున్నాయి.",
        "Freezer pani cheyadam ledu, ice cream melt aipotundi.",
        "ఫ్రిడ్జ్ కూలింగ్ అవ్వట్లేదు, ఆహారం పాడైపోతోంది.",
        "फ्रीजर ठंडा नहीं कर रहा है और सारी आइसक्रीम पिघल गई।",
        "फ्रिज खराब पड़ा है, सारा सामान पिघलकर खराब हो रहा है।",
        "फ्रीझर खराब झाला आहे आणि सर्व आईस्क्रीम वितळली आहे.",
        "फ्रीझर थंड होत नाही, पदार्थ खराब होत आहेत.",
        "Freezer band padla ahe, ice cream vitlat ahe.",
    ],
    "spill_hazard": [
        "Large olive oil spill in aisle 4, floor is very slippery.",
        "Broken glass jar of jam shattered across the entrance walkway.",
        "Liquid leaking from cold drinks cooler creating slip hazard.",
        "Customer nearly slipped and fell on wet floor without caution sign.",
        "Wet floor hazard! Oil spilled on tiles with no barricade.",
        "Floor pe tel gir gaya hai, log slip ho rahe hain.",
        "Spll on flor, slippry tile.",
        "Slippery detergent spill on floor with serious fall risk.",
    ],
    "store_cleanliness": [
        "Messy aisle with empty cartons abandoned in the middle of path.",
        "Trash overflowing from dustbin near customer entrance.",
        "Dusty shelves and sticky spills that haven't been wiped.",
        "Litter and discarded plastic packaging scattered in aisle 6.",
        "Aisles bohot messy hain aur dustbin overflow ho raha hai.",
        "Cluttered walkways and dirty shopping area.",
        "Trash bin full to the brim and garbage scattered around.",
    ],
    "restroom_maintenance": [
        "Restroom toilet is clogged and water is overflowing on floor.",
        "No hand soap or paper towels available in customer washroom.",
        "Washroom door lock is broken and hand dryer is not working.",
        "Toilet bohot ganda hai aur soap bilkul nahi hai washroom me.",
        "No paper towel in restroom, tap is leaking badly.",
        "Customer toilet out of order and hygiene supplies exhausted.",
    ],
    "queue_management": [
        "Huge line at billing counter, only one cashier operating.",
        "Wait time exceeds 25 minutes to checkout three items.",
        "Queue is stretching all the way back to grocery aisle.",
        "Bohot lambi line hai counter pe, cashier bohot slow hai.",
        "Checkout wait time is ridiculous today, crowd everywhere.",
        "Only one register open during rush hour, lines backed up.",
    ],
    "ac_temperature": [
        "Store air conditioning is broken, suffocating heat inside.",
        "AC is not working on the ground floor, customers sweating.",
        "Store temperature is excessively hot and humid today.",
        "Store me bilkul cooling nahi hai, AC band pada hai.",
        "Too hot in store, ventilation seems faulty.",
        "HVAC cooling unit failure causing extreme heat inside.",
    ],
    "cart_basket_availability": [
        "No shopping carts or hand baskets available at store entrance.",
        "Trolley wheels are completely locked and squeaking loudly.",
        "Had to carry groceries in arms because zero baskets were left.",
        "Gate pe ek bhi cart nahi hai, sab khatam ho gaye.",
        "Broken shopping cart wheels stuck.",
        "Hand baskets empty at entrance foyer, customers waiting.",
    ],
    "stockout": [
        "Baby formula shelf empty for most of the morning.",
        "Rice and cooking oil shelves are empty again this afternoon.",
        "Popular brand oats out of stock for the third consecutive visit.",
        "Bare shelves in the cereal aisle, completely unavailable.",
        "Out of stock! Shelf is totally empty for fresh milk.",
        "Shelf bilkul empty hai, aata aur daal out of stock hai.",
        "Yeh item 3 din se unavailable chal raha hai store me.",
        "Out of stk, emty shelf.",
        "Inventory depleted, item completely unavailable across racks.",
    ],
    "fresh_produce_spoilage": [
        "Tomatoes on display are rotten, squishy, and attract fruit flies.",
        "Bags of spinach are decaying and turning black on shelf.",
        "Apples and oranges are bruised and rotten in produce rack.",
        "Fruit counter pe saare seb sad chuke hain, flies ghoom rahi hain.",
        "Produce is stale and spoiled.",
        "Rotten vegetables and decayed fruits on the fresh counter.",
    ],
    "damaged_packaging": [
        "Dented cans of soup on discount shelf with damaged rims.",
        "Torn flour bags leaking white powder across lower shelf.",
        "Cereal box torn open with seal broken on display.",
        "Dabba phata hua hai aur product bahar leak ho raha hai.",
        "Damagd box, dented can on shelf.",
        "Crushed boxes and broken seals on merchandise.",
    ],
    "expired_stock_on_shelf": [
        "Milk carton expired three days ago still being sold on shelf.",
        "Bread loaf has past best-before date from last week.",
        "Baby food jars on shelf are past expiry date by two months.",
        "Expired product! Selling expired yogurt dated last month.",
        "Doodh expired date ka rakha hua hai counter pe.",
        "Past best before date item found on shelf.",
        "Expired meat packages found in display case.",
    ],
    "warehouse_delay": [
        "Warehouse delivery truck delayed, morning replenishment missed.",
        "Inbound cross-dock delivery shipment 6 hours late.",
        "DC shipment missing, freight delivery rescheduled.",
        "Delivery late aayi warehouse se, stock replenish nahi hua.",
        "Inbound supply chain truck delayed from central warehouse.",
    ],
    "inaccurate_inventory_count": [
        "Store system says 15 items in stock but shelf is completely empty.",
        "Inventory count mismatch: app showed available but clerk found none.",
        "Ghost inventory in system, physical count does not match ERP.",
        "System me stock dikha raha hai par shelf pe zero items hain.",
        "ERP system shows inventory on hand but physical rack is bare.",
    ],
    "pricing": [
        "Shelf says ₹99 but bill charged ₹129 for the same item.",
        "Discount advertised on shelf was not applied at checkout.",
        "Price tag displayed is lower than register barcode scan price.",
        "Price mismatch: tag shows 15 dollars, billed 22 dollars.",
        "Price difference! Tag says 200 but cashier charged 280.",
        "Tag pe price alag likha hai aur bill me zyada charge kiya.",
        "Wrong price on label, register charged extra money.",
        "Prc tag mismatch, chargd extra.",
        "Shelf price does not match checkout billing price.",
        "பொருளின் விலை 99 ரூபாய் என்று இருந்தது, ஆனால் பில்லில் 129 ரூபாய் வசூலித்தார்கள்.",
        "விலை வித்தியாசம்: அலமாரியில் 99 ஆனால் பில்லில் 129 ரூபாய்.",
        "ట్యాగ్‌పై 99 రూపాయలు ఉంటే బిల్లులో 129 రూపాయలు ఎక్కువ వసూలు చేశారు.",
        "ట్యాగ్ ధర కంటే బిల్లులో ఎక్కువ మొత్తం తీసుకున్నారు.",
        "टैग पर 99 रुपये लिखे थे लेकिन बिल में 129 रुपये ज्यादा चार्ज किया।",
        "टॅगवर 99 रुपये होते पण बिलात 129 रुपये लावून जास्त पैसे घेतले.",
    ],
    "missing_price_tag": [
        "No price tag anywhere on the new shampoo display.",
        "Missing barcode label on vegetable packs, cannot check price.",
        "Cannot find price for these items, shelf edge tag missing.",
        "Item pe koi price tag nahi laga hua, rate pata nahi chal raha.",
        "Price tags missing from entire row of skincare products.",
    ],
    "promo_discount_not_applied": [
        "Buy 1 get 1 free promotional discount was not deducted on receipt.",
        "Promotional circular showed 30% off but bill shows full MSRP.",
        "Coupon code rejected at POS despite being valid.",
        "BOGO offer bill me lagaya hi nahi cashier ne.",
        "Promo not applied at register.",
        "Promotional campaign discount failed to deduct from final invoice.",
    ],
    "misleading_offer": [
        "Deceptive banner claimed 50% off storewide but excludes everything.",
        "Misleading advertisement: offer conditions not clearly stated.",
        "Store banner promises free gift but staff refuses to give it.",
        "Fake discount advertisement on storefront window.",
        "Misleading signage advertising discounts that do not exist.",
    ],
    "product_quality_dissatisfaction": [
        "Brand quality has deteriorated drastically, tastes stale.",
        "Fabric of private label t-shirt tore after single wash.",
        "Disappointed with quality of store-brand olive oil.",
        "Product ki quality bohot ghatiya nikli, bilkul bekar hai.",
        "Inferior product quality, substandard ingredients.",
    ],
    "payment_failure": [
        "Card payment failed repeatedly at checkout; queue is blocked.",
        "Repeated card declined message despite bank confirming funds.",
        "Self-checkout froze after payment and receipt did not print.",
        "UPI payment failed and timed out on register 4.",
        "POS terminal timed out during contactless tap payment.",
        "Payment failed! POS machine declined chip card twice.",
        "UPI scan kiya paise cut gaye par POS ne failure dikhaya.",
        "Card swipe machine hang ho gayi transaction ke beech me.",
        "Paymnt faled, card declined.",
        "EDC card machine declined payment transaction.",
        "கார்டு நிராகரிக்கப்பட்டது, கட்டணம் தோல்வியடைந்தது.",
        "யுபிஐ வேலை செய்யவில்லை, பணம் எடுக்கப்பட்டு பில் வரவில்லை.",
        "కార్డు చెల్లింపు విఫలమైంది, యూపీఐ లావాదేవీ రాలేదు.",
        "कार्ड पेमेंट फेल हो गया और पैसे कट गए पर रसीद नहीं आई।",
        "कार्ड नाकारले गेले आणि पेमेंट अयशस्वी झाले.",
    ],
    "billing": [
        "Two customers were charged twice after UPI timeout.",
        "Customer charged double amount on credit card statement.",
        "Wrong bill: cashier scanned milk carton four times instead of two.",
        "Duplicate charge on bank statement for single store visit.",
        "Cashier charged for extra items that were never purchased.",
        "Bill me do baar charge lag gaya same item ka, refund chahiye.",
        "Bill galat banaya, extra item add kar diya cashier ne.",
        "Doubl charg on bil, refund issue.",
        "doubl charg on crdit card statemnt, chargd twice",
        "Overcharged on invoice, scanned item multiple times.",
    ],
    "self_checkout_kiosk_down": [
        "Self-checkout terminal 2 screen is frozen on blue crash screen.",
        "Self checkout barcode scanner completely dead and not reading.",
        "Kiosk cash dispenser jammed and coin acceptor stuck.",
        "Self-checkout machine band padi hai aur restart nahi ho rahi.",
        "Self service checkout terminal unresponsive and crashed.",
    ],
    "app_ordering_bug": [
        "Online order marked ready but staff cannot find packed bag.",
        "Mobile app crashes whenever clicking checkout button.",
        "App store order disappeared from order history screen.",
        "Mobile app error: cannot add items to cart, app crashes.",
        "App se order place nahi ho raha, error aa raha hai.",
        "Mobile application bug preventing checkout confirmation.",
    ],
    "wifi_network_outage": [
        "In-store customer Wi-Fi is down and has no internet connection.",
        "Cannot connect to store guest Wi-Fi inside building.",
        "Wi-Fi signal dead in basement grocery section.",
        "Store ka guest wifi bilkul connect nahi ho raha hai.",
        "Guest wireless network completely disconnected.",
    ],
    "staff_misconduct": [
        "Staff member spoke abusively and threatened a customer.",
        "Customer says employee made discriminatory remarks.",
        "Supervisor was shouting insults at shopper in front of children.",
        "Employee threatened physical violence during argument.",
        "Cashier hurled racial slurs at family near billing counter.",
        "Staff ne badtameezi ki aur customer ko dhamki di.",
        "Employee abusive tha aur galiya de raha tha customer ko.",
        "Staff abusiv and threatnd me.",
        "Gross employee misconduct and threatening behavior.",
        "ஊழியர் தகாத முறையில் பேசி வாடிக்கையாளரை மிரட்டினார்.",
        "சிబ్బంది దురుసుగా ప్రవర్తించి బెదిరించారు.",
        "स्टाफ ने बहुत बदतमीजी की और धमकी दी।",
        "कर्मचाऱ्याने अपमानास्पद भाषा वापरली आणि धमकी दिली.",
    ],
    "staff_unhelpfulness": [
        "Floor staff refused to help locate items and walked away.",
        "Asked associate for assistance with heavy box, was ignored.",
        "Staff chatting on mobile phones instead of helping shoppers.",
        "Employee was very unhelpful and rolled eyes when asked question.",
        "Staff se pucha par koi help karne ko tayyar nahi tha.",
        "Store associates unhelpful and dismissive of customer inquiry.",
    ],
    "billing_clerk_shortage": [
        "Only one billing counter active during peak Sunday evening rush.",
        "Extreme staff shortage at registers, long lines forming.",
        "Cashiers abandoned counters leaving customers stranded.",
        "Registers pe cashiers hi nahi hain, sab band pada hai.",
        "Severe cashier shortage at front registers causing delays.",
    ],
    "health_safety_violation": [
        "Emergency fire exit is blocked by stacked wooden pallets.",
        "Exposed electrical live wires hanging from ceiling near aisle 2.",
        "Broken overhead light fitting hanging precariously above customers.",
        "Staff operating forklift in customer aisle without safety spotter.",
        "Fire exit ke aage pura carton ka dher laga rakha hai, dangerous.",
        "Dangerous occupational hazard with blocked emergency egress.",
    ],
    "other": [
        "Great store experience and polite staff today.",
        "Music volume in the background is a bit too loud.",
        "Parking lot was quite crowded this afternoon.",
        "Do you have plans to open a store in the north suburb?",
        "Store overall achha hai par parking me time laga.",
        "General inquiry about loyalty membership benefits.",
        "Pleasant shopping trip overall, thanks.",
        "கடை சுத்தமாக இருக்கிறது, ஊழியர்களும் மரியாதையாக நடந்துகொள்கிறார்கள்.",
        "ஸ்டోర్ చాలా శుభ్రంగా ఉంది మరియు సిబ్బంది చాలా మర్యాదగా ఉన్నారు.",
        "बहुत अच्छा स्टोर है और कर्मचारी बहुत विनम्र और मददगार हैं।",
        "दुकान खूप स्वच्छ आहे आणि कर्मचारी खूप नम्र आहेत.",
        "Store is very clean and staff is very polite and helpful.",
    ],
}

def generate_bootstrap_data() -> Tuple[List[str], List[str]]:
    """Return synthetic labelled training examples covering all taxonomy classes."""
    texts = []
    labels = []
    for issue_type, examples in BOOTSTRAP_TEMPLATES.items():
        for ex in examples:
            texts.append(ex)
            labels.append(issue_type)

    # Augment with keyword frames for robust generalization
    frames = [
        "Reported store problem: {kw}",
        "Customer reported an issue regarding {kw} today",
        "Observed {kw} at this store location",
        "{kw} observed by customer during store visit",
    ]
    for cat, data in TAXONOMY.items():
        for kw in data["keywords"]:
            for f in frames[:2]:
                texts.append(f.format(kw=kw))
                labels.append(cat)

    return texts, labels

def train_classifier(output_path: Path = DEFAULT_MODEL_PATH) -> Dict[str, Any]:
    """Train TF-IDF character n-gram + Logistic Regression classifier and persist artifact."""
    texts, labels = generate_bootstrap_data()
    
    # Train/test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Build scikit-learn Pipeline with character n-grams
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1
        )),
        ("clf", LogisticRegression(
            C=5.0,
            max_iter=1000,
            random_state=42,
            class_weight="balanced"
        ))
    ])
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    
    artifact = {
        "pipeline": pipeline,
        "classes": list(pipeline.classes_),
        "taxonomy_classes": get_all_issue_types(),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "TfidfVectorizer(char_wb, 3-5) + LogisticRegression(C=5.0, balanced)",
        "metrics": {
            "test_accuracy": acc,
            "test_macro_f1": macro_f1,
            "train_size": len(X_train),
            "test_size": len(X_test)
        },
        "calibration_notice": "Classifier outputs decision function margins. Probabilities are uncalibrated softmax estimates."
    }
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)
    return artifact

def load_trained_model(model_path: Path = DEFAULT_MODEL_PATH) -> Any:
    """Load persisted model artifact from disk, or None if not found."""
    p = Path(model_path)
    if not p.exists():
        return None
    try:
        return joblib.load(p)
    except Exception:
        return None
