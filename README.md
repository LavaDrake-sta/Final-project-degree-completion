# Final-project-degree-completion
Reads documents or images by AI and identifies whether it is important details or not
# 🧠 PII Detection System

מערכת לזיהוי **פרטים אישיים (PII)** במסמכים — כולל תמיכה מלאה בעברית.  
המערכת סורקת קבצי **PDF**, **תמונות** ו־**Word**, מזהה פרטים רגישים כמו שם, תעודת זהות, טלפון, כתובת, ודוא"ל, ומפיקה **דוח מסכם** לכל קובץ.

---

## 📁 מבנה תיקיות
PII_Detection_System/
├─ src/
│ ├─ main.py # קובץ ההרצה הראשי
│ ├─ loaders.py # קריאה מקבצים (PDF / Word / תמונה)
│ ├─ pii_rules.py # חוקים ו־Regex לזיהוי פרטים אישיים
│ └─ report.py # הפקת דוח CSV/Excel
├─ data/
│ ├─ input/ # לשים פה את הקבצים לבדיקה
│ └─ output/ # פה ייווצר הדוח
├─ requirements.txt
└─ README.md

---

## ⚙️ התקנות נדרשות

### 1️⃣ התקנת Python
ודא שהמותקנת גרסה **3.10 או 3.11**  
בדיקה:
```bash
python --version
2️⃣ יצירת סביבת עבודה (אופציונלי אך מומלץ)
python -m venv venv
venv\Scripts\activate       # ב-Windows
# או:
source venv/bin/activate    # ב-Linux / Mac
3️⃣ התקנת הספריות הדרושות
pip install -U pip
pip install -r requirements.txt

pillow
pytesseract
pdfplumber
python-docx
spacy
pandas
openpyxl
# אופציונלי (בינה מתקדמת):
transformers
torch
4️⃣ התקנת Tesseract OCR (חובה לתמיכה בתמונות ו־PDF סרוק)
🪟 Windows:

הורד את ההתקנה הרשמיים (UB Mannheim):
👉 https://github.com/UB-Mannheim/tesseract/wiki

התקן רגיל (Next → Next).

ודא שהנתיב נוסף ל־PATH (בד"כ: C:\Program Files\Tesseract-OCR\).

הורד את קובץ השפה עברית:

קובץ heb.traineddata מכאן:
👉 https://github.com/tesseract-ocr/tessdata_best/blob/main/heb.traineddata

העתק אותו לתיקייה:

C:\Program Files\Tesseract-OCR\tessdata\


בדיקה:

tesseract --list-langs


אמור להחזיר:

eng
heb

🚀 הפעלת המערכת
🗂️ צעד 1: לשים קבצים לסריקה

הוסף את הקבצים שברצונך לסרוק בתיקייה:

data/input/


ניתן לשים קבצי PDF, תמונות (JPG/PNG) או Word (.docx).

▶️ צעד 2: להריץ את המערכת

מתוך שורש הפרויקט:

python -m src.main

📊 צעד 3: צפייה בתוצאות

לאחר ההרצה יווצר דוח בתיקייה:

data/output/pii_report.xlsx


הדוח מציג עבור כל קובץ אילו פרטים אישיים נמצאו ואילו חסרים.

🧾 פקודות מהירות
# שכפול הפרויקט
git clone https://github.com/LavaDrake-sta/Final-project-degree-completion.git
cd Final-project-degree-completion

# יצירת סביבת עבודה
python -m venv venv
venv\Scripts\activate

# התקנת ספריות
pip install -r requirements.txt

# הפעלת הסורק
python -m src.main
