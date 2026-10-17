"""Test suite for multilingual translation service."""
import unittest
from services.translation import translate_text, detect_source_language, is_pure_english


class TranslationServiceTests(unittest.TestCase):
    def test_pure_english_preservation(self):
        """English text must be preserved verbatim without alteration."""
        samples = [
            "fix this ASAP AC not working",
            "Freezer temperature alarm is sounding and frozen items are soft.",
            "Customer reported stomach illness after eating prepared chicken; investigate urgently.",
            "Shelf says $99 but bill charged $129 for the same item.",
            "Please check store inventory immediately."
        ]
        for s in samples:
            res = translate_text(s)
            self.assertEqual(res["description_en"], s)
            self.assertEqual(res["original_text"], s)
            self.assertFalse(res["is_translated"])
            self.assertEqual(res["source_language"], "en")

    def test_user_tanglish_example(self):
        """Paal stock illa (Tamil in Latin script) must translate to Milk is out of stock."""
        res = translate_text("Paal stock illa")
        self.assertIn("Milk", res["description_en"])
        self.assertIn("out of stock", res["description_en"].lower())
        self.assertTrue(res["is_translated"])
        self.assertEqual(res["source_language"], "ta")
        self.assertEqual(res["original_text"], "Paal stock illa")

    def test_user_hindi_example(self):
        """दूध खराब हो गया है must translate to Milk has spoiled."""
        res = translate_text("दूध खराब हो गया है")
        self.assertIn("Milk", res["description_en"])
        self.assertIn("spoiled", res["description_en"].lower())
        self.assertTrue(res["is_translated"])
        self.assertEqual(res["source_language"], "hi")
        self.assertEqual(res["original_text"], "दूध खराब हो गया है")

    def test_user_tamil_example(self):
        """பால் காலாவதியாகிவிட்டது must translate to Milk has expired."""
        res = translate_text("பால் காலாவதியாகிவிட்டது")
        self.assertIn("Milk", res["description_en"])
        self.assertIn("expired", res["description_en"].lower())
        self.assertTrue(res["is_translated"])
        self.assertEqual(res["source_language"], "ta")
        self.assertEqual(res["original_text"], "பால் காலாவதியாகிவிட்டது")

    def test_regional_tamil_sentences(self):
        """Various Tamil sentences must translate to clear English."""
        cases = [
            ("பிரிட்ஜ் வேலை செய்யவில்லை, பால் கெட்டுப்போய்விட்டது.", ["Fridge", "spoiled"]),
            ("சிக்கன் சாப்பிட்ட பிறகு வாந்தி மயக்கம் ஏற்பட்டது.", ["vomiting", "chicken"]),
            ("கடை மிகவும் அசுத்தமாக உள்ளது, கரப்பான் பூச்சிகள் ஓடுகின்றன.", ["dirty", "cockroaches"]),
            ("பொருட்கள் இல்லை, ஷெல்ப் காலியாக உள்ளது.", ["shelf", "empty"]),
        ]
        for src, keywords in cases:
            res = translate_text(src)
            self.assertTrue(res["is_translated"])
            for kw in keywords:
                self.assertIn(kw.lower(), res["description_en"].lower())

    def test_regional_telugu_sentences(self):
        """Various Telugu sentences must translate to clear English."""
        cases = [
            ("ఫ్రీజర్ పనిచేయడం లేదు, ఆహార పదార్థాలు కరిగిపోతున్నాయి.", ["Freezer", "melting"]),
            ("స్టోర్‌లో బొద్దింకలు కనిపించాయి, చాలా మురికిగా ఉంది.", ["Cockroaches", "dirty"]),
        ]
        for src, keywords in cases:
            res = translate_text(src)
            self.assertTrue(res["is_translated"])
            for kw in keywords:
                self.assertIn(kw.lower(), res["description_en"].lower())

    def test_regional_marathi_sentences(self):
        """Various Marathi sentences must translate to clear English."""
        cases = [
            ("फ्रीझर खराब झाला आहे आणि सर्व आईस्क्रीम वितळली आहे.", ["Freezer", "melted"]),
            ("दुकानात झुरळे फिरताना दिसली, खूप घाणेरडे आहे.", ["Cockroaches", "filthy"]),
        ]
        for src, keywords in cases:
            res = translate_text(src)
            self.assertTrue(res["is_translated"])
            for kw in keywords:
                self.assertIn(kw.lower(), res["description_en"].lower())

    def test_fallback_safely(self):
        """Unrecognized foreign string falls back to original text without error."""
        res = translate_text("randomunrecognizedphrase 12345")
        self.assertEqual(res["description_en"], "randomunrecognizedphrase 12345")
        self.assertFalse(res["is_translated"])

    def test_caching_performance(self):
        """Subsequent translation calls must return cached dictionary immediately."""
        text = "Paal stock illa"
        r1 = translate_text(text)
        r2 = translate_text(text)
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
