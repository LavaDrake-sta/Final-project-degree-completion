"""
ממשק משתמש מתקדם עם Streamlit
תמיכה בטקסט, תמונות ו-PDF
גרסה מתוקנת עם imports נכונים
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import pytesseract

# הגדרת Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# הוספת נתיב src - תיקון הבעיה
current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # חזור 3 תיקיות
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# ייבוא המודולים שלנו - עכשיו בלי relative imports
try:
    # ייבוא ישיר ללא נקודות
    from detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from processors.image_processor import ImageProcessor
    from processors.pdf_processor import PDFProcessor
    detector_available = True
    print("✅ מודולים נטענו בהצלחה")
except ImportError as e:
    st.error(f"❌ שגיאה בייבוא מודולים: {e}")
    st.info("💡 ודא שכל הקבצים נמצאים במקום הנכון")
    detector_available = False
    print(f"❌ Import error: {e}")

# הגדרת הדף
st.set_page_config(
    page_title="זיהוי מידע אישי רגיש - מתקדם",
    page_icon="🔒",
    layout="wide"
)

# CSS מותאם
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# כותרת ראשית
st.markdown("""
<div class="main-header">
    <h1>🔒 מערכת זיהוי מידע אישי רגיש - מתקדם</h1>
    <p>תמיכה בטקסט, תמונות, PDF ומסמכי Office</p>
</div>
""", unsafe_allow_html=True)

if not detector_available:
    st.stop()

# יצירת המזהים
@st.cache_resource
def load_processors():
    detector = BasicPIIDetector()
    image_processor = ImageProcessor()
    pdf_processor = PDFProcessor()
    return detector, image_processor, pdf_processor

detector, image_processor, pdf_processor = load_processors()

# תפריט צד
st.sidebar.header("🎛️ אפשרויות ניתוח")
analysis_type = st.sidebar.selectbox(
    "בחר סוג התוכן:",
    [
        "📝 טקסט חופשי",
        "🖼️ תמונה (OCR)",
        "📄 קובץ PDF",
        "📁 קובץ טקסט"
    ]
)

# פונקציות עזר
def display_pii_results(results, source_info=""):
    """הצגת תוצאות זיהוי PII"""

    if not results or not results.get('matches'):
        st.success("✅ **מצוין!** לא נמצא מידע רגיש")
        return

    # הצגת סיכום
    sensitivity_colors = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🟠',
        'CRITICAL': '🔴'
    }

    overall_sens = results['overall_sensitivity'].name
    color_icon = sensitivity_colors[overall_sens]

    if overall_sens == 'CRITICAL':
        st.error(f"""
        **🚨 {results['summary']}**
        
        רמת רגישות: {color_icon} **{overall_sens}**
        
        **מידע קריטי זוהה! מומלץ מאוד לא לשתף את התוכן הזה.**
        """)
    elif overall_sens == 'HIGH':
        st.warning(f"""
        **⚠️ {results['summary']}**
        
        רמת רגישות: {color_icon} **{overall_sens}**
        """)
    else:
        st.info(f"""
        **ℹ️ {results['summary']}**
        
        רמת רגישות: {color_icon} **{overall_sens}**
        """)

    # פירוט הממצאים
    st.subheader("🔍 פירוט הממצאים")

    matches_data = []
    for i, match in enumerate(results['matches'], 1):
        sensitivity_icon = sensitivity_colors[match.sensitivity.name]
        category_display = match.category.replace('_', ' ').replace('keyword ', '').title()

        matches_data.append({
            '#': i,
            'מידע שנמצא': f"**{match.text}**",
            'קטגוריה': category_display,
            'רמת רגישות': f"{sensitivity_icon} {match.sensitivity.name}",
            'רמת ודאות': f"{match.confidence:.0%}",
            'מיקום בטקסט': f"תווים {match.start_pos}-{match.end_pos}"
        })

    df = pd.DataFrame(matches_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # סטטיסטיקות
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 סה״כ ממצאים", len(results['matches']))

    with col2:
        # ספירת ממצאים קריטיים
        critical_count = sum(1 for m in results['matches'] if m.sensitivity == SensitivityLevel.CRITICAL)
        st.metric("🔴 ממצאים קריטיים", critical_count)

    with col3:
        # ספירת ממצאים ברמה גבוהה
        high_count = sum(1 for m in results['matches'] if m.sensitivity == SensitivityLevel.HIGH)
        st.metric("🟠 ממצאים ברמה גבוהה", high_count)

    # המלצות
    st.subheader("💡 המלצות")
    if critical_count > 0:
        st.error("""
        🚨 **פעולות מומלצות:**
        - הסר מיידית מספרי ת.ז וכרטיסי אשראי
        - אל תשתף את התוכן הזה בפלטפורמות ציבוריות
        - שקול הצפנה אם אתה חייב לשמור את המידע
        """)
    elif high_count > 0:
        st.warning("""
        ⚠️ **שים לב:**
        - בדוק אם באמת צריך לשתף מידע אישי זה
        - העסק בהסתרת או החלפת המידע הרגיש
        - ודא שמי שמקבל את המידע מוסמך לכך
        """)

def process_text_input():
    """עיבוד טקסט ישיר"""
    st.header("📝 ניתוח טקסט חופשי")

    # דוגמאות מוכנות
    examples = {
        "🆔 פרטים אישיים": """שלום, אני דוד לוי ותעודת הזהות שלי היא 123456789.
אפשר להתקשר אליי ב-052-1234567 או לכתוב ל david.levi@gmail.com
אני גר ברחוב הרצל 15 בתל אביב מיקוד 62739.""",

        "🏥 מידע רפואי": """השבוע הלכתי לרופא בבית החולים איכילוב.
האבחנה שלי היא סוכרת סוג 2 ואני צריך לקחת תרופה יומית.
הביטוח בריאות מכסה את הטיפול הפסיכולוגי.""",

        "💰 מידע פיננסי": """המשכורת שלי היא 12,000 שקל בחודש.
יש לי חוב בבנק של 50,000 שקל ומשכנתא של 800,000 שקל.
מספר החשבון 1234567890 וכרטיס אשראי 4580-1234-5678-9012.""",

        "📧 מידע יצירת קשר": """ניתן ליצור קשר במספרים:
בית: 03-1234567, נייד: 052-9876543, עבודה: 02-6543210
אימיילים: work@company.co.il, personal@gmail.com"""
    }

    selected_example = st.selectbox(
        "🎯 בחר דוגמה או כתוב בעצמך:",
        ["✍️ כתוב בעצמך"] + list(examples.keys())
    )

    default_text = examples.get(selected_example, "") if selected_example != "✍️ כתוב בעצמך" else ""

    user_text = st.text_area(
        "הכנס טקסט לניתוח:",
        value=default_text,
        height=200,
        placeholder="הקלד או הדבק כאן טקסט לבדיקת מידע רגיש...",
        help="הזן כל טקסט והמערכת תזהה מידע אישי רגיש"
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("🔍 נתח טקסט", type="primary"):
            if user_text.strip():
                with st.spinner("🔍 מנתח טקסט..."):
                    results = detector.analyze_text(user_text)

                st.subheader("📊 תוצאות הניתוח")
                display_pii_results(results)

                # הצגת סטטיסטיקות נוספות
                st.sidebar.subheader("📈 סטטיסטיקות טקסט")
                st.sidebar.metric("📄 אורך טקסט", f"{len(user_text)} תווים")
                st.sidebar.metric("📝 מספר מילים", len(user_text.split()))
            else:
                st.warning("⚠️ אנא הזן טקסט לניתוח")

def process_image_input():
    """עיבוד תמונות עם OCR"""
    st.header("🖼️ ניתוח תמונה (OCR)")

    st.info("""
    💡 **הוראות שימוש:**
    - העלה תמונה עם טקסט (צילום מסמך, תמונה סרוקה וכו')
    - המערכת תקרא את הטקסט ותחפש מידע רגיש
    - פורמטים נתמכים: JPG, PNG, BMP, TIFF
    """)

    uploaded_image = st.file_uploader(
        "בחר תמונה:",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'],
        help="העלה תמונה עם טקסט לזיהוי מידע רגיש"
    )

    if uploaded_image is not None:
        # הצגת התמונה
        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(uploaded_image, caption=f"תמונה: {uploaded_image.name}", use_container_width=True)

            if st.button("🔍 נתח תמונה", type="primary"):
                with st.spinner("🖼️ מבצע OCR..."):
                    # קריאת התמונה
                    image_bytes = uploaded_image.read()

                    # OCR
                    ocr_result = image_processor.extract_text_from_image(
                        image_bytes, uploaded_image.name
                    )

                with col2:
                    if ocr_result['success']:
                        st.success(f"✅ OCR הושלם! ודאות: {ocr_result['confidence']:.1f}%")

                        extracted_text = ocr_result['text']

                        if extracted_text.strip():
                            # הצגת הטקסט שחולץ
                            with st.expander("📝 טקסט שחולץ מהתמונה"):
                                st.text_area("", extracted_text, height=150, disabled=True)

                            # ניתוח PII
                            with st.spinner("🔍 מחפש מידע רגיש..."):
                                pii_results = detector.analyze_text(extracted_text)

                            st.subheader("📊 תוצאות זיהוי מידע רגיש")
                            display_pii_results(pii_results, f"תמונה: {uploaded_image.name}")

                            # סטטיסטיקות OCR
                            st.sidebar.subheader("🖼️ סטטיסטיקות OCR")
                            st.sidebar.metric("📄 תווים שחולצו", len(extracted_text))
                            st.sidebar.metric("📝 מילים", len(extracted_text.split()))
                            st.sidebar.metric("🎯 רמת ודאות", f"{ocr_result['confidence']:.1f}%")

                        else:
                            st.warning("⚠️ לא נמצא טקסט בתמונה או שאיכות ה-OCR נמוכה")
                    else:
                        st.error(f"❌ שגיאה ב-OCR: {ocr_result.get('error', 'לא ידוע')}")

def process_pdf_input():
    """עיבוד קבצי PDF"""
    st.header("📄 ניתוח קובץ PDF")

    st.info("""
    💡 **יכולות PDF:**
    - קריאת PDF רגיל עם טקסט
    - OCR למסמכים סרוקים
    - תמיכה במסמכים רב-עמודיים
    - זיהוי אוטומטי של סוג המסמך
    """)

    uploaded_pdf = st.file_uploader(
        "בחר קובץ PDF:",
        type=['pdf'],
        help="העלה קובץ PDF לזיהוי מידע רגיש"
    )

    if uploaded_pdf is not None:
        pdf_bytes = uploaded_pdf.read()

        # מידע על הקובץ
        st.success(f"✅ קובץ {uploaded_pdf.name} נטען ({len(pdf_bytes):,} bytes)")

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🔍 נתח PDF", type="primary"):
                with st.spinner("📄 מעבד PDF..."):
                    pdf_result = pdf_processor.extract_text_from_pdf(
                        pdf_bytes, uploaded_pdf.name
                    )

                if pdf_result['success']:
                    st.success(f"""
                    ✅ PDF עובד בהצלחה!
                    - **עמודים:** {pdf_result['pages']}
                    - **שיטה:** {pdf_result['method']}
                    - **תווים:** {pdf_result['character_count']:,}
                    """)

                    if pdf_result.get('ocr_pages', 0) > 0:
                        st.info(f"🖼️ OCR בוצע על {pdf_result['ocr_pages']} עמודים")

                    extracted_text = pdf_result['text']

                    if extracted_text.strip():
                        # הצגת קטע מהטקסט
                        with st.expander("📝 דוגמה מהטקסט שחולץ"):
                            preview_text = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
                            st.text_area("", preview_text, height=200, disabled=True)

                        # ניתוח PII
                        with st.spinner("🔍 מחפש מידע רגיש..."):
                            pii_results = detector.analyze_text(extracted_text)

                        st.subheader("📊 תוצאות זיהוי מידע רגיש")
                        display_pii_results(pii_results, f"PDF: {uploaded_pdf.name}")

                        # סטטיסטיקות PDF
                        st.sidebar.subheader("📄 סטטיסטיקות PDF")
                        st.sidebar.metric("📄 עמודים", pdf_result['pages'])
                        st.sidebar.metric("📝 תווים", f"{pdf_result['character_count']:,}")
                        st.sidebar.metric("📖 מילים", f"{pdf_result['word_count']:,}")
                        if pdf_result.get('ocr_pages'):
                            st.sidebar.metric("🖼️ עמודי OCR", pdf_result['ocr_pages'])
                    else:
                        st.warning("⚠️ לא נמצא טקסט ב-PDF או שהוא מוגן")
                else:
                    st.error(f"❌ שגיאה בעיבוד PDF: {pdf_result.get('error', 'לא ידוע')}")

def process_text_file_input():
    """עיבוד קבצי טקסט"""
    st.header("📁 ניתוח קובץ טקסט")

    uploaded_file = st.file_uploader(
        "בחר קובץ טקסט:",
        type=['txt', 'rtf'],
        help="העלה קובץ טקסט לזיהוי מידע רגיש"
    )

    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8')

            st.success(f"✅ קובץ {uploaded_file.name} נטען בהצלחה")

            # תצוגה מקדימה
            with st.expander("👁️ הצג תוכן הקובץ"):
                preview = content[:2000] + "..." if len(content) > 2000 else content
                st.text_area("תוכן הקובץ:", preview, height=300, disabled=True)

            if st.button("🔍 נתח קובץ", type="primary"):
                with st.spinner("🔍 מנתח קובץ..."):
                    results = detector.analyze_text(content)

                st.subheader("📊 תוצאות הניתוח")
                display_pii_results(results, f"קובץ: {uploaded_file.name}")

                # סטטיסטיקות
                st.sidebar.subheader("📁 סטטיסטיקות קובץ")
                st.sidebar.metric("📄 גודל", f"{len(content):,} תווים")
                st.sidebar.metric("📝 מילים", f"{len(content.split()):,}")
                st.sidebar.metric("📄 שורות", len(content.split('\n')))

        except UnicodeDecodeError:
            st.error("❌ שגיאה בקריאת הקובץ. ודא שזה קובץ טקסט בקידוד UTF-8")
        except Exception as e:
            st.error(f"❌ שגיאה בעיבוד הקובץ: {str(e)}")

# הצגת התוכן לפי בחירת המשתמש
if analysis_type == "📝 טקסט חופשי":
    process_text_input()
elif analysis_type == "🖼️ תמונה (OCR)":
    process_image_input()
elif analysis_type == "📄 קובץ PDF":
    process_pdf_input()
elif analysis_type == "📁 קובץ טקסט":
    process_text_file_input()

# מידע נוסף בסיידבר
st.sidebar.markdown("---")
st.sidebar.header("📚 אודות המערכת")
st.sidebar.info("""
**גרסה:** 2.0 - מתקדם

**יכולות זיהוי:**
• 🆔 תעודות זהות ישראליות
• 📞 מספרי טלפון (כל הפורמטים)
• 📧 כתובות אימייל
• 💳 מספרי כרטיס אשראי
• 🏥 מידע רפואי רגיש
• 💰 מידע פיננסי
• 🏠 פרטים אישיים

**טכנולוגיות:**
• OCR עם Tesseract
• עיבוד PDF מתקדם
• זיהוי דפוסים ברגקסים
• ניתוח הקשר חכם
""")

st.sidebar.markdown("---")
st.sidebar.header("💻 מידע טכני")
st.sidebar.code("""
# הפעלת הממשק:
streamlit run src/ui/streamlit_app.py

# דרישות מערכת:
- Python 3.8+
- Tesseract OCR
- 2GB RAM מומלץ
""")

# כותרת תחתונה
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<small>🔒 מערכת זיהוי מידע אישי רגיש | פרויקט גמר | גרסה 2.0</small><br>
<small>💡 מערכת זו מיועדת לצורכי בדיקה ולמידה בלבד</small>
</div>
""", unsafe_allow_html=True)