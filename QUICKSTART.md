# 🚀 התחלה מהירה - Quick Start

## אופציה 1: הרצה פשוטה (ללא תלויות)

**מומלץ למתחילים או לבדיקה מהירה**

### Windows / Mac / Linux:

```bash
python run_simple.py
```

**יתרונות:**
- ✅ לא דורש התקנת ספריות נוספות
- ✅ עובד מיד מהקופסה
- ✅ מהיר מאוד
- ✅ תואם לתיקון 13

**חסרונות:**
- ⚠️ פחות מדויק מגרסת ה-AI (בעיקר בזיהוי שמות אנשים)

---

## אופציה 2: גרסה מלאה עם AI

### שלב 1: התקן את Git

אם עדיין לא עשית, שכפל את הפרויקט:

```bash
git clone https://github.com/LavaDrake-sta/Final-project-degree-completion.git
cd Final-project-degree-completion
```

### שלב 2: עדכן את הקוד (חשוב!)

```bash
git fetch origin
git checkout claude/review-project-progress-011CUmpLKgXNR4y6JurVNGZ7
git pull origin claude/review-project-progress-011CUmpLKgXNR4y6JurVNGZ7
```

### שלב 3: התקן ספריות בסיסיות

```bash
pip install tqdm pandas openpyxl pillow pytesseract pdfplumber python-docx
```

### שלב 4 (אופציונלי): התקן AI למדויקות מקסימלית

```bash
pip install transformers torch spacy
python -m spacy download xx_ent_wiki_sm
```

### שלב 5: הרץ את המערכת

**ללא AI (מהיר):**
```bash
python test_quick.py
```

**עם AI (מדויק):**
```bash
python -m src.main
```

---

## 🐛 פתרון בעיות נפוצות

### שגיאה: `ModuleNotFoundError: No module named 'spacy'`

**פתרון 1 (מהיר):**
```bash
python run_simple.py
```

**פתרון 2 (עדכון קוד):**
```bash
git pull origin claude/review-project-progress-011CUmpLKgXNR4y6JurVNGZ7
```

**פתרון 3 (התקנת ספריות):**
```bash
pip install transformers torch spacy
python -m spacy download xx_ent_wiki_sm
```

---

### שגיאה: הקוד לא מעודכן

אם אתה רואה שורות קוד ישנות, עדכן:

```bash
git stash  # שמור שינויים זמניים אם יש
git pull origin claude/review-project-progress-011CUmpLKgXNR4y6JurVNGZ7
git stash pop  # החזר שינויים זמניים
```

---

## 📁 איפה לשים קבצים?

1. צור קובץ טקסט עם פרטים אישיים
2. שים אותו ב: `data/input/test_document.txt`
3. הרץ: `python run_simple.py`

---

## 📊 מה המערכת מזהה?

### פרטים רגילים:
- ✅ תעודות זהות
- ✅ טלפונים
- ✅ אימיילים
- ✅ תאריכים

### מידע רגיש (תיקון 13):
- ⚠️ מידע רפואי
- ⚠️ נתונים כלכליים
- ⚠️ דעות פוליטיות
- ⚠️ אמונות דתיות
- ⚠️ חשבונות בנק

---

## 💡 טיפים

1. **בדיקה מהירה:** השתמש ב-`run_simple.py`
2. **דיוק מקסימלי:** התקן AI והשתמש ב-`python -m src.main`
3. **ללא קובץ:** `run_simple.py` מאפשר להזין טקסט ידנית

---

## 🆘 עזרה נוספת

יש בעיה? פתח issue ב-GitHub:
https://github.com/LavaDrake-sta/Final-project-degree-completion/issues

או הרץ:
```bash
python run_simple.py
```

זה **תמיד** אמור לעבוד! 🚀
