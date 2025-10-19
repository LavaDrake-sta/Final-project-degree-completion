"""
PII Detection System - Streamlit App
קובץ הפעלה פשוט ללא בעיות imports
"""

import streamlit as st
import pandas as pd
import sys
import os
import pytesseract
from datetime import datetime
import io
import json

# הגדרת Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# הוספת src לנתיב
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# ייבוא המודולים
try:
    from detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from processors.image_processor import ImageProcessor
    from processors.pdf_processor import PDFProcessor

    st.success("✅ מודולים נטענו בהצלחה")
except ImportError as e:
    st.error(f"❌ שגיאה: {e}")
    st.stop()

# הגדרת הדף
st.set_page_config(
    page_title="זיהוי מידע אישי רגיש",
    page_icon="🔒",
    layout="wide"
)

# כותרת
st.title("🔒 מערכת זיהוי מידע אישי רגיש")
st.write("**פרויקט גמר** - זיהוי מידע רגיש בטקסט, תמונות ו-PDF")


# יצירת המזהים
@st.cache_resource
def load_processors():
    detector = BasicPIIDetector()
    image_processor = ImageProcessor()
    pdf_processor = PDFProcessor()
    return detector, image_processor, pdf_processor


detector, image_processor, pdf_processor = load_processors()

# תפריט
tab1, tab2, tab3 = st.tabs(["📝 טקסט", "🖼️ תמונה", "📄 PDF"])

# טאב טקסט
with tab1:
    st.header("📝 ניתוח טקסט")

    text_input = st.text_area(
        "הזן טקסט לבדיקה:",
        height=150,
        placeholder="הקלד או הדבק טקסט כאן..."
    )

    if st.button("🔍 נתח טקסט"):
        if text_input.strip():
            with st.spinner("מנתח..."):
                results = detector.analyze_text(text_input)

            if results['matches']:
                st.error(f"⚠️ {results['summary']}")

                # הצגת ממצאים
                matches_data = []
                for i, match in enumerate(results['matches'], 1):
                    matches_data.append({
                        '#': i,
                        'מידע רגיש': match.text,
                        'סוג': match.category,
                        'רגישות': match.sensitivity.name
                    })

                df = pd.DataFrame(matches_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.success("✅ לא נמצא מידע רגיש")

# טאב תמונה
with tab2:
    st.header("🖼️ ניתוח תמונה (OCR)")

    uploaded_image = st.file_uploader(
        "העלה תמונה:",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        help="תמונה עם טקסט"
    )

    if uploaded_image:
        st.image(uploaded_image, width=400)

        if st.button("🔍 נתח תמונה"):
            with st.spinner("מבצע OCR..."):
                image_bytes = uploaded_image.read()
                ocr_result = image_processor.extract_text_from_image(image_bytes, uploaded_image.name)

            if ocr_result['success']:
                st.success(f"✅ OCR הושלם! ודאות: {ocr_result['confidence']:.1f}%")

                extracted_text = ocr_result['text']

                if extracted_text.strip():
                    with st.expander("📝 טקסט שחולץ"):
                        st.text(extracted_text)

                    # ניתוח PII
                    pii_results = detector.analyze_text(extracted_text)

                    if pii_results['matches']:
                        st.error(f"⚠️ {pii_results['summary']}")

                        for match in pii_results['matches']:
                            st.write(f"🔍 **{match.text}** ({match.category})")
                    else:
                        st.success("✅ לא נמצא מידע רגיש בתמונה")
                else:
                    st.warning("⚠️ לא נמצא טקסט בתמונה")
            else:
                st.error(f"❌ שגיאה ב-OCR: {ocr_result.get('error', 'לא ידוע')}")

# טאב PDF
with tab3:
    st.header("📄 ניתוח PDF")

    uploaded_pdf = st.file_uploader(
        "העלה PDF:",
        type=['pdf'],
        help="קובץ PDF לניתוח"
    )

    if uploaded_pdf:
        pdf_bytes = uploaded_pdf.read()

        if st.button("🔍 נתח PDF"):
            with st.spinner("מעבד PDF..."):
                pdf_result = pdf_processor.extract_text_from_pdf(pdf_bytes, uploaded_pdf.name)

            if pdf_result['success']:
                st.success(f"✅ PDF עובד! {pdf_result['pages']} עמודים")

                extracted_text = pdf_result['text']

                if extracted_text.strip():
                    with st.expander("📝 תוכן ה-PDF"):
                        preview = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
                        st.text(preview)

                    # ניתוח PII
                    pii_results = detector.analyze_text(extracted_text)

                    if pii_results['matches']:
                        st.error(f"⚠️ {pii_results['summary']}")

                        for match in pii_results['matches']:
                            st.write(f"🔍 **{match.text}** ({match.category})")
                    else:
                        st.success("✅ לא נמצא מידע רגיש ב-PDF")
                else:
                    st.warning("⚠️ לא נמצא טקסט ב-PDF")
            else:
                st.error(f"❌ שגיאה בעיבוד PDF: {pdf_result.get('error', 'לא ידוע')}")

# מידע צד
st.sidebar.header("📚 אודות")
st.sidebar.info("""
**מערכת זיהוי מידע רגיש**

**יכולות:**
• זיהוי ת.ז, טלפונים, אימיילים
• OCR לתמונות
• עיבוד PDF
• ניתוח מידע רפואי ופיננסי

**פרויקט גמר 2024**
""")

st.sidebar.header("🔧 סטטוס מערכת")
try:
    version = pytesseract.get_tesseract_version()
    st.sidebar.success(f"✅ Tesseract {version}")
except:
    st.sidebar.error("❌ Tesseract לא זמין")

st.sidebar.success("✅ מערכת מוכנה")


def add_enhanced_ui_features():
    """הוספת תכונות UI מתקדמות"""

    # 1. מחולל דוח PDF
    def generate_report(results, source_type="text"):
        """יצירת דוח מפורט"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'source_type': source_type,
            'total_matches': results['total_matches'],
            'overall_sensitivity': results['overall_sensitivity'].name,
            'summary': results['summary'],
            'matches': []
        }

        for match in results['matches']:
            report_data['matches'].append({
                'text': match.text,
                'category': match.category,
                'sensitivity': match.sensitivity.name,
                'confidence': f"{match.confidence:.0%}",
                'position': f"{match.start_pos}-{match.end_pos}"
            })

        return report_data

    # 2. הצגת סטטיסטיקות מתקדמות
    def display_advanced_stats(results):
        """הצגת סטטיסטיקות מפורטות"""
        if not results['matches']:
            return

        st.subheader("📈 ניתוח מתקדם")

        # חלוקה לעמודות
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            critical_count = sum(1 for m in results['matches'] if m.sensitivity.name == 'CRITICAL')
            st.metric("🔴 קריטי", critical_count)

        with col2:
            high_count = sum(1 for m in results['matches'] if m.sensitivity.name == 'HIGH')
            st.metric("🟠 גבוה", high_count)

        with col3:
            validated_count = sum(1 for m in results['matches'] if m.confidence > 0.9)
            st.metric("✅ מאומת", validated_count)

        with col4:
            avg_confidence = sum(m.confidence for m in results['matches']) / len(results['matches'])
            st.metric("🎯 ודאות ממוצעת", f"{avg_confidence:.0%}")

        # גרף התפלגות רגישות
        sensitivity_data = {}
        for match in results['matches']:
            sens = match.sensitivity.name
            sensitivity_data[sens] = sensitivity_data.get(sens, 0) + 1

        if sensitivity_data:
            st.subheader("📊 התפלגות רגישות")
            df_chart = pd.DataFrame(list(sensitivity_data.items()), columns=['רמת רגישות', 'כמות'])
            st.bar_chart(df_chart.set_index('רמת רגישות'))

    # 3. המלצות אבטחה חכמות
    def show_security_recommendations(results):
        """הצגת המלצות אבטחה מותאמות"""
        if not results['matches']:
            st.success("🛡️ הטקסט בטוח לשיתוף")
            return

        st.subheader("🛡️ המלצות אבטחה")

        critical_found = any(m.sensitivity.name == 'CRITICAL' for m in results['matches'])
        high_found = any(m.sensitivity.name == 'HIGH' for m in results['matches'])

        if critical_found:
            st.error("""
            🚨 **פעולות מיידיות נדרשות:**
            - הסר מיידית מספרי ת.ז וכרטיסי אשראי
            - אל תשתף טקסט זה בפלטפורמות ציבוריות
            - שקול הצפנה לאחסון מקומי
            - בדוק מי מוסמך לראות מידע זה
            """)
        elif high_found:
            st.warning("""
            ⚠️ **זהירות נדרשת:**
            - בדוק אם באמת צריך לשתף מידע אישי זה
            - שקול החלפת מספרי טלפון בXXX-XXXXXXX
            - הסתר חלק מכתובת האימייל
            - ודא שהמקבל מוסמך לקבל מידע זה
            """)
        else:
            st.info("""
            ℹ️ **שמירה על פרטיות:**
            - המידע ברמת רגישות נמוכה-בינונית
            - עדיין מומלץ לבדוק את הנמענים
            - שקול הסרת מידע אישי לא רלוונטי
            """)

        # המלצות ספציפיות לכל סוג מידע
        categories_found = set(m.category for m in results['matches'])

        if 'israeli_id' in categories_found:
            st.error("🆔 **ת.ז נמצאה:** החלף במספר דמה או הסר לחלוטין")

        if 'phone_number' in categories_found:
            st.warning("📞 **מספר טלפון:** החלף ב-05X-XXXXXXX או 'לפרטים צור קשר'")

        if 'email' in categories_found:
            st.warning("📧 **אימייל:** החלף ב-username@[DOMAIN] או הסר")

        if 'credit_card' in categories_found:
            st.error("💳 **כרטיס אשראי:** הסר מיידית או החלף ב-XXXX-XXXX-XXXX-XXXX")

    # 4. ייצוא תוצאות
    def export_results(results, source_type="text"):
        """ייצוא תוצאות בפורמטים שונים"""
        st.subheader("📤 ייצוא תוצאות")

        col1, col2, col3 = st.columns(3)

        with col1:
            # ייצוא JSON
            report_data = generate_report(results, source_type)
            json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 הורד דוח JSON",
                data=json_str,
                file_name=f"pii_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        with col2:
            # ייצוא CSV
            if results['matches']:
                matches_df = pd.DataFrame([
                    {
                        'מידע רגיש': m.text,
                        'קטגוריה': m.category,
                        'רגישות': m.sensitivity.name,
                        'ודאות': f"{m.confidence:.0%}",
                        'מיקום': f"{m.start_pos}-{m.end_pos}"
                    }
                    for m in results['matches']
                ])

                csv = matches_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 הורד טבלה CSV",
                    data=csv,
                    file_name=f"pii_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col3:
            # ייצוא סיכום טקסט
            summary_text = f"""דוח זיהוי מידע רגיש
תאריך: {datetime.now().strftime('%d/%m/%Y %H:%M')}
סוג מקור: {source_type}

סיכום: {results['summary']}
רמת רגישות כללית: {results['overall_sensitivity'].name}
סה"כ ממצאים: {results['total_matches']}

פירוט ממצאים:
"""
            for i, match in enumerate(results['matches'], 1):
                summary_text += f"{i}. {match.text} ({match.category}) - {match.sensitivity.name}\n"

            st.download_button(
                label="📝 הורד סיכום טקסט",
                data=summary_text,
                file_name=f"pii_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

    # 5. היסטוריית בדיקות
    def show_scan_history():
        """הצגת היסטוריית בדיקות (בזיכרון הסשן)"""
        if 'scan_history' not in st.session_state:
            st.session_state.scan_history = []

        if st.session_state.scan_history:
            st.subheader("📋 היסטוריית בדיקות")

            for i, scan in enumerate(reversed(st.session_state.scan_history[-5:]), 1):
                with st.expander(f"בדיקה {i} - {scan['timestamp'][:19].replace('T', ' ')}"):
                    st.write(f"**סוג:** {scan['source_type']}")
                    st.write(f"**תוצאה:** {scan['summary']}")
                    st.write(f"**ממצאים:** {scan['total_matches']}")

    # החזרת הפונקציות לשימוש
    return {
        'display_advanced_stats': display_advanced_stats,
        'show_security_recommendations': show_security_recommendations,
        'export_results': export_results,
        'show_scan_history': show_scan_history,
        'generate_report': generate_report
    }
