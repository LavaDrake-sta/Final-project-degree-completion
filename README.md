# 🧠 PII Detection System

מערכת לזיהוי **פרטים אישיים רגישים (PII)** במסמכים ובתמונות — עם תמיכה מלאה בעברית.
המערכת סורקת קבצי **PDF / תמונות / Word / Excel**, מזהה פרטים כמו שם, תעודת זהות, טלפון, כתובת ודוא"ל,
מאפשרת **תצוגה מקדימה** לכל סוג קובץ, ומפיקה **דוח מסכם** עם הערכת סיכון לכל קובץ.

המערכת רצה דרך ממשק **Streamlit**, ומשתמשת ב-**Microsoft Presidio** יחד עם מודל **AI (Transformers)**
לזיהוי מבוסס-הקשר.

---

## ✨ שני מצבי זיהוי

| מצב | מבוסס על | תופס היטב | מגבלות |
|-----|----------|-----------|--------|
| **Regex / חוקים** | דפוסים ידניים + `PatternRecognizer` | מידע **מבני**: ת"ז, טלפון, אימייל, כרטיס אשראי, IBAN, תאריכים | לא מזהה שמות/כתובות (אין להם צורה קבועה) |
| **AI** | Presidio + מודל NER (Transformers / spaCy) | מידע **מבוסס-הקשר**: שמות, כתובות, ארגונים | דורש התקנת `torch`/`transformers` ומודל מתאים |

> שמות וכתובות הם טקסט חופשי, ולכן מצב ה-Regex תמיד יזהה אותם פחות טוב ממצב ה-AI — זה תכנוני.
> כדי לזהות עברית כראוי יש לוודא שהניתוח רץ עם מנוע NLP עברי ועם `language="he"`.

---

## 📁 מבנה תיקיות

```
PII_Detection_System/
├─ src/
│  ├─ ui/
│  │  ├─ streamlit_app.py   # הממשק הראשי (Streamlit) – הרצה מכאן
│  │  └─ preview.py         # תצוגה מקדימה: PDF / תמונה / Word / Excel
│  ├─ pipeline.py           # PIIPipeline – מקשר detector + decision_engine
│  ├─ detector.py           # עטיפת Presidio AnalyzerEngine + anonymize
│  ├─ pii_rules.py          # חוקים ו-Regex (recognizers) לזיהוי PII
│  └─ report.py             # הפקת דוח CSV/Excel
├─ data/
│  ├─ input/                # קבצים לבדיקה
│  └─ output/               # פה ייווצר הדוח
└─ ...
requirements.txt
README.md
test_new_pipeline.py
```

> המבנה לעיל מתאר את הארכיטקטורה החדשה; התאם שמות קבצים אם שונה אצלך.

---

## ⚙️ התקנה

### 1. Python
מומלץ **Python 3.10 / 3.11**.
```bash
python --version
```

### 2. סביבת עבודה (מומלץ)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac
```

### 3. ספריות Python
```bash
pip install -U pip
pip install -r requirements.txt
```
כולל: `streamlit`, `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `transformers`, `torch`,
`python-docx`, `openpyxl`, `xlrd`, `pymupdf`, `pdfplumber`, `pytesseract`, `Pillow`, `opencv-python`, `pandas`.

### 4. Tesseract OCR (חובה לתמונות ו-PDF סרוק)
- **Windows:** הורד מ-[UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki), ודא ש-`C:\Program Files\Tesseract-OCR\` נמצא ב-PATH.
- **Ubuntu:** `sudo apt install tesseract-ocr tesseract-ocr-heb`
- **macOS:** `brew install tesseract tesseract-lang`

הורד את שפת העברית `heb.traineddata` מ-[tessdata_best](https://github.com/tesseract-ocr/tessdata_best/blob/main/heb.traineddata)
ושים אותה ב-`tessdata` של Tesseract. בדיקה:
```bash
tesseract --list-langs   # אמור להציג eng + heb
```

### 5. מודל NLP עברי (למצב AI)
ודא שטעון מודל שמבין עברית (למשל מודל NER עברי מבוסס Transformers, או pipeline עברי).
הקפד להעביר `language="he"` בקריאות הניתוח.

---

## 🚀 הפעלה

```bash
cd PII_Detection_System
streamlit run src/ui/streamlit_app.py
```

בממשק:
1. **העלאת קובץ** — PDF / תמונה (JPG/PNG) / Word (.docx) / Excel (.xlsx/.xls).
2. **תצוגה מקדימה** — לחיצה מציגה את תוכן הקובץ בדפדפן.
3. **בחירת מצב זיהוי** — Regex או AI.
4. **סריקה** — המערכת מזהה PII, מציגה ישויות שנמצאו, הערכת סיכון וטקסט אנונימי.
5. **דוח** — נשמר תחת `data/output/`.

---

## 🧪 בדיקה מהירה
```bash
python test_new_pipeline.py
```
הטסט טוען את `PIIPipeline`, מריץ זיהוי על משפט עברי לדוגמה, ומדפיס את הישויות, הערכת הסיכון והטקסט האנונימי.

> שים לב: ודא שהבדיקה מריצה את הניתוח עם `language="he"` ולא `"en"`, אחרת שמות/כתובות בעברית לא יזוהו.

---

## 📄 פורמטים נתמכים

| פורמט | קריאה | תצוגה מקדימה |
|-------|-------|--------------|
| PDF | `pymupdf` / `pdfplumber` (+OCR לסרוק) | ✅ |
| תמונה (JPG/PNG) | `pytesseract` (OCR) | ✅ |
| Word (.docx) | `python-docx` | ✅ |
| Excel (.xlsx/.xls) | `pandas` + `openpyxl`/`xlrd` | ✅ |

---

## 🔒 פרטיות
המערכת מתוכננת לריצה **מקומית** — הקבצים הרגישים אינם נשלחים לשרת חיצוני.
