# 🧠 AI-Powered PII Detection & Anonymization System
## מערכת מתקדמת לזיהוי והסתרת פרטים אישיים מבוססת בינה מלאכותית

**Final Project - Degree Completion**

### ⚖️ תואם לתיקון 13 לחוק הגנת הפרטיות, התשפ"ד-2024
**Compliant with Israeli Privacy Protection Law - Amendment No. 13 (2024)**

מערכת **חכמה ומתקדמת** לזיהוי והסתרת **פרטים אישיים (PII)** במסמכים — עם תמיכה מלאה בעברית ואנגלית, ותאימות מלאה לחוק הישראלי.

### ✨ תכונות מרכזיות:

🤖 **זיהוי מבוסס AI** - שימוש במודלי Transformers ו-NER לזיהוי מדויק
🔐 **הסתרה אוטומטית** - מסתיר פרטים אישיים באופן אוטומטי
📄 **תמיכה בפורמטים מרובים** - PDF, Word, תמונות (JPG, PNG)
🌍 **דו-לשוני** - תמיכה מלאה בעברית ואנגלית
📊 **דוחות מפורטים** - Excel (4 גליונות), CSV וטקסט
⚡ **מהיר ויעיל** - עיבוד מקבילי של קבצים מרובים
⚖️ **תאימות חוקית** - מיושם לפי תיקון 13 לחוק הגנת הפרטיות

### 🎯 מה המערכת מזהה?

#### פרטים אישיים סטנדרטיים:
✅ **שמות אנשים** - באמצעות AI NER
✅ **תעודות זהות** - עם אימות Luhn (9 ספרות)
✅ **מספרי דרכון** - פורמט ישראלי (7-8 ספרות)
✅ **רישיון נהיגה** - פורמט ישראלי
✅ **מספרי טלפון** - פורמט ישראלי (+972, 05X)
✅ **כתובות אימייל** - כל הפורמטים
✅ **כתובות מגורים** - רחוב, שדרות, וכו'
✅ **תאריך לידה** - פורמטים שונים
✅ **שמות ארגונים**
✅ **מיקומים גיאוגרפיים**

#### מידע בעל רגישות מיוחדת (תיקון 13, סעיף 7ג):
⚠️ **מידע רפואי** - מחלות, טיפולים, קופות חולים
⚠️ **מידע גנטי** - נתונים גנטיים ו-DNA
⚠️ **מזהה ביומטרי** - טביעות אצבע, זיהוי פנים
⚠️ **נטייה מינית**
⚠️ **דעות פוליטיות** - השתייכות למפלגות
⚠️ **אמונות דתיות** - דת, כשרות, תפילה
⚠️ **עבר פלילי** - הרשעות, תיקים פליליים
⚠️ **נתוני מיקום** - מעקב ונתוני GPS
⚠️ **מוצא אתני**
⚠️ **הערכת אישיות** - מבחנים פסיכומטריים
⚠️ **שכר ופעילות כלכלית** - משכורת, הכנסות
⚠️ **כרטיסי אשראי** - עם אימות Luhn
⚠️ **חשבונות בנק** - פורמט ישראלי
⚠️ **פרטיות חיי משפחה**
⚠️ **מידע חסוי מכוח דין**

---

## 📁 מבנה הפרויקט

```
Final-project-degree-completion/
├── src/
│   ├── main.py                 # קובץ הרצה ראשי
│   ├── loaders.py              # טעינת קבצים (PDF/Word/תמונות)
│   ├── pii_detector_il.py      # 🤖 מנוע זיהוי AI (תואם תיקון 13)
│   ├── israeli_privacy_law.py  # ⚖️ הגדרות חוק הגנת הפרטיות
│   ├── anonymizer.py           # 🔐 מנוע הסתרת פרטים
│   ├── report.py               # מחולל דוחות (כולל דוח תאימות)
│   └── config.py               # הגדרות מערכת
├── data/
│   ├── input/                  # 📥 קבצים לעיבוד
│   └── output/                 # 📤 תוצאות ודוחות
│       └── anonymized/         # טקסטים מוסתרים
├── models/                     # מודלי AI (נטענים אוטומטית)
├── requirements.txt            # תלויות Python
├── create_sample_files.py     # יצירת קבצי דוגמה
└── README.md
```

---

## 🚀 התקנה והפעלה

### דרישות מקדימות

- **Python 3.10 או גבוה יותר**
- **4GB RAM** (מומלץ 8GB עבור מודלי AI)
- **מקום פנוי**: ~2GB (עבור מודלי AI)

### 1️⃣ שכפול הפרויקט

```bash
git clone https://github.com/LavaDrake-sta/Final-project-degree-completion.git
cd Final-project-degree-completion
```

### 2️⃣ יצירת סביבה וירטואלית (מומלץ)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ התקנת ספריות Python

```bash
pip install -U pip
pip install -r requirements.txt
```

**הספריות כוללות:**
- `transformers` - מודלי AI לזיהוי NER
- `torch` - PyTorch למודלים
- `spacy` - עיבוד שפה טבעית
- `pdfplumber` - קריאת PDF
- `python-docx` - קריאת Word
- `pytesseract` - OCR לתמונות
- `pandas`, `openpyxl` - דוחות Excel
### 4️⃣ התקנת Tesseract OCR (לעיבוד תמונות)

#### 🪟 Windows:

1. הורד והתקן מ-[UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. ודא שהנתיב נוסף ל-PATH: `C:\Program Files\Tesseract-OCR\`
3. הורד [קובץ עברית heb.traineddata](https://github.com/tesseract-ocr/tessdata_best/blob/main/heb.traineddata)
4. העתק ל: `C:\Program Files\Tesseract-OCR\tessdata\`

#### 🐧 Linux (Ubuntu/Debian):

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-heb
```

#### 🍎 macOS:

```bash
brew install tesseract tesseract-lang
```

#### בדיקה:

```bash
tesseract --list-langs
# צריך להציג: eng, heb
```

### 5️⃣ התקנת מודל SpaCy (אופציונלי למדויק יותר)

```bash
python -m spacy download xx_ent_wiki_sm
```

---

## 🎮 שימוש במערכת

### שלב 1: יצירת קבצי דוגמה (אופציונלי)

```bash
python create_sample_files.py
```

הסקריפט יוצר קבצי דוגמה עם פרטים אישיים לבדיקה.

### שלב 2: הוספת קבצים לעיבוד

העתק את הקבצים שברצונך לסרוק לתיקייה:

```
data/input/
```

**פורמטים נתמכים:**
- PDF (`.pdf`)
- Word (`.docx`)
- תמונות (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`)

### שלב 3: הרצת המערכת

```bash
python -m src.main
```

### מה קורה ברקע?

1. 🔄 **טעינת מודלי AI** (בפעם הראשונה - עשוי לקחת כמה דקות)
2. 📖 **קריאת קבצים** - טעינת טקסט מכל הקבצים
3. 🔍 **זיהוי PII** - שילוב של AI + Regex לזיהוי מדויק
4. 🔐 **הסתרה אוטומטית** - יצירת גרסאות מוסתרות
5. 📊 **יצירת דוחות** - Excel, CSV, טקסט

### שלב 4: צפייה בתוצאות

**דוחות מפורטים:**
- `data/output/pii_report_[timestamp].xlsx` - דוח Excel מפורט
- `data/output/pii_report_[timestamp].txt` - דוח טקסט קריא

**קבצים מוסתרים:**
- `data/output/anonymized/[filename]_anonymized.txt` - טקסט עם פרטים מוסתרים

---

## 🛠️ תצורה מתקדמת

ערוך את `src/config.py` להתאמה אישית:

```python
# זיהוי AI או רק Regex
USE_AI = True  # False למהירות מקסימלית

# סף וודאות מינימלי
MIN_CONFIDENCE = 0.5  # 0.0-1.0

# מצב הסתרה
ANONYMIZATION_MODE = "replace"  # redact, mask, replace, hash
```

---

## 📊 דוגמת פלט

```
╔═══════════════════════════════════════════════════════════════╗
║         🧠 מערכת זיהוי והסתרת פרטים אישיים (PII)              ║
║              AI-Powered PII Detection System                  ║
╚═══════════════════════════════════════════════════════════════╝

שלב 1: טעינת קבצים
═══════════════════════════════════════════════════════════
✓ Loaded: sample_hebrew.docx (DOCX)
✓ Loaded: sample_english.docx (DOCX)
✓ נטענו 2 קבצים בהצלחה

שלב 2: אתחול מודלי AI
═══════════════════════════════════════════════════════════
🔄 Loading AI models...
✓ AI models loaded successfully

שלב 3: זיהוי פרטים אישיים
═══════════════════════════════════════════════════════════
📄 sample_hebrew.docx: נמצאו 8 פרטים אישיים
📄 sample_english.docx: נמצאו 6 פרטים אישיים

שלב 4: הסתרת פרטים אישיים
═══════════════════════════════════════════════════════════
✓ sample_hebrew.docx: הוסתר ונשמר
✓ sample_english.docx: הוסתר ונשמר

סיכום
═══════════════════════════════════════════════════════════
📊 סה"כ קבצים שעובדו: 2
🔍 קבצים עם פרטים אישיים: 2
🔐 סה"כ פרטים אישיים שזוהו: 14
```

---

## 🧪 דוגמת קוד - שימוש כספרייה

```python
from src.loaders import FileLoader
from src.pii_detector_il import IsraeliPIIDetector
from src.anonymizer import PIIAnonymizer, AnonymizationMode
from src.israeli_privacy_law import is_special_sensitivity

# טעינת קובץ
loader = FileLoader()
text, file_type = loader.load_file("document.pdf")

# זיהוי PII (תואם תיקון 13)
detector = IsraeliPIIDetector(use_ai=True)
entities = detector.detect_pii(text)

# בדיקת רגישות
for entity_type, entity_list in entities.items():
    if entity_list:
        sensitivity = "רגישות מיוחדת" if is_special_sensitivity(entity_type) else "רגיל"
        print(f"{entity_type}: {len(entity_list)} ({sensitivity})")

# הסתרה
anonymizer = PIIAnonymizer(mode=AnonymizationMode.REPLACE)
anonymized = anonymizer.anonymize(text, entities)

print(anonymized)
```

---

## ⚖️ תיקון 13 לחוק הגנת הפרטיות - פירוט

### מה זה תיקון 13?

**תיקון מס' 13 לחוק הגנת הפרטיות** אושר בכנסת באוגוסט 2024 ונכנס לתוקף ב-**14 באוגוסט 2025**.
זהו התיקון המקיף והמשמעותי ביותר לחוק הגנת הפרטיות מאז חקיקתו בשנת 1981.

### עיקרי השינויים:

#### 1. הגדרת "מידע בעל רגישות מיוחדת" (סעיף 7ג)

התיקון מגדיר 15 קטגוריות של מידע רגיש במיוחד הדורש **הגנה מוגברת**:

- 🏥 מידע רפואי
- 🧬 מידע גנטי
- 👁️ מזהה ביומטרי
- 🏳️‍🌈 נטייה מינית
- 🗳️ דעות פוליטיות
- ✡️ אמונות דתיות
- ⚖️ עבר פלילי
- 📍 נתוני מיקום
- 🌍 מוצא אתני
- 🧠 הערכת אישיות
- 💰 שכר ופעילות כלכלית
- 💳 כרטיסי אשראי
- 🏦 חשבונות בנק
- 👨‍👩‍👧‍👦 פרטיות חיי משפחה
- 🔒 מידע חסוי מכוח דין

#### 2. חובת מינוי קצין פרטיות

ארגונים שעיקר עיסוקם עיבוד מידע אישי רגיש בהיקף משמעותי **חייבים למנות קצין פרטיות**.

#### 3. דיווח למרשם

מאגרי מידע המכילים מידע רגיש על יותר מ-100,000 אנשים **חייבים לדווח לרשות** גם אם אינם טעונים רישום.

#### 4. סמכויות אכיפה מוגברות

הרשות להגנת הפרטיות קיבלה **סמכויות אכיפה משמעותיות**, כולל:
- הטלת עיצומים כספיים
- פיקוח מוגבר
- סנקציות על הפרות

### איך המערכת שלנו תואמת?

✅ **זיהוי אוטומטי** של כל 15 הקטגוריות של מידע רגיש
✅ **סיווג לפי רמת רגישות** - רגיל vs. רגישות מיוחדת
✅ **דוח תאימות מפורט** בגליון Excel נפרד
✅ **התראות על מידע רגיש** במיוחד שנמצא
✅ **אנונימיזציה מוגברת** למידע רגיש

### דוח תאימות Excel

הדוחות כוללים גליון "תיקון 13" עם:
- פירוט מלא של כל סוגי המידע שנמצאו
- הפרדה בין מידע רגיל למידע בעל רגישות מיוחדת
- המלצות לפעולה
- תאריכי תוקף ודרישות חוקיות

---

## 🤝 תרומה לפרויקט

נשמח לתרומות! אפשר:
- 🐛 לדווח על באגים
- ✨ להציע תכונות חדשות
- 🔧 לשלוח Pull Requests

---

## 📄 רישיון

MIT License - ראה [LICENSE](LICENSE) לפרטים

---

## 👨‍💻 יוצר

**Final Project - Degree Completion**
GitHub: [@LavaDrake-sta](https://github.com/LavaDrake-sta)

---

## 🙏 תודות

- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [spaCy](https://spacy.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
