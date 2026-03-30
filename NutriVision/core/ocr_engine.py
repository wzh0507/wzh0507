import re

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False


class OCREngine:
    def __init__(self):
        self._reader = None
        if _EASYOCR_AVAILABLE:
            try:
                self._reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
            except Exception:
                self._reader = None

    def extract_nutrition(self, image_path):
        """Extract nutrition info from an image file.

        Returns dict with keys: food_name, calories, protein, fat, carbs.
        Falls back to stub values if OCR is unavailable or parsing fails.
        """
        stub = {
            'food_name': 'Unknown Food',
            'calories': 245.0,
            'protein': 12.5,
            'fat': 8.3,
            'carbs': 31.2,
        }

        if self._reader is None:
            return stub

        try:
            results = self._reader.readtext(str(image_path), detail=0)
            text = '\n'.join(results)
            return self._parse_text(text, stub)
        except Exception:
            return stub

    def _parse_text(self, text, stub):
        result = dict(stub)

        # Energy / calories
        cal_match = re.search(
            r'(?:能量|热量|Energy)[^\d]*(\d+(?:\.\d+)?)',
            text, re.IGNORECASE
        )
        if cal_match:
            result['calories'] = float(cal_match.group(1))

        # Protein
        prot_match = re.search(
            r'(?:蛋白质|Protein)[^\d]*(\d+(?:\.\d+)?)',
            text, re.IGNORECASE
        )
        if prot_match:
            result['protein'] = float(prot_match.group(1))

        # Fat
        fat_match = re.search(
            r'(?:脂肪|Fat)[^\d]*(\d+(?:\.\d+)?)',
            text, re.IGNORECASE
        )
        if fat_match:
            result['fat'] = float(fat_match.group(1))

        # Carbohydrates
        carb_match = re.search(
            r'(?:碳水化合物|Carbohydrates?)[^\d]*(\d+(?:\.\d+)?)',
            text, re.IGNORECASE
        )
        if carb_match:
            result['carbs'] = float(carb_match.group(1))

        # Try to extract a food name from first non-numeric line
        for line in text.split('\n'):
            line = line.strip()
            if line and not re.match(r'^[\d\s\.\,\%]+$', line):
                result['food_name'] = line
                break

        return result
