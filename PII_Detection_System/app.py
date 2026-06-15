"""
PII Detection System - Streamlit App
פרויקט גמר - זיהוי מידע אישי רגיש
גרסה עם תצוגה מקדימה לפני השחרה
"""

import streamlit as st


import pandas as pd
import sys
import os
import io
import json
import pytesseract
from datetime import datetime

# ─── Logging ─────────────────────────────────────────────────────
# ─── Unicode Short Path Name Support (Windows) ───────────────────
import ctypes
def get_short_path_name(long_name_str):
    try:
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(long_name_str, buf, 1024)
        return buf.value
    except Exception:
        return long_name_str

base_dir = get_short_path_name(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'src'))
try:
    from src.logger_config import get_logger, trace_execution, log_progress
except ImportError:
    try:
        from logger_config import get_logger, trace_execution, log_progress  # type: ignore
    except ImportError:
        import logging
        def get_logger(name):
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s',
                datefmt='%H:%M:%S'
            )
            return logging.getLogger(name)
        def trace_execution(func): return func
        def log_progress(c, t, n): pass
app_logger = get_logger("PII.App")

# ─── set_page_config חייב להיות ראשון ────────────────────────────
st.set_page_config(
    page_title="מערכת זיהוי PII",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Tesseract ────────────────────────────────────────────────────
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
TESSERACT_OK = os.path.exists(TESSERACT_PATH)

# ─── paths ────────────────────────────────────────────────────────
sys.path.append(os.path.join(base_dir, 'src'))

# ─── Basic modules ────────────────────────────────────────────────
try:
    from src.detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from src.processors.image_processor import ImageProcessor
    from src.processors.pdf_processor import PDFProcessor
    from src.processors.word_processor import WordProcessor
    from src.processors.Excel_Processor import ExcelProcessor
except ImportError as e:
    st.error(f"❌ שגיאת ייבוא: {e}")
    st.stop()

# ─── AI Pipeline ─────────────────────────────────────────────────
AI_PIPELINE_AVAILABLE = False
try:
    from src.pipeline import PIIPipeline
    AI_PIPELINE_AVAILABLE = True
except ImportError:
    pass

# ─── Redactors ───────────────────────────────────────────────────
REDACTORS_AVAILABLE = False
try:
    from redactors import PdfRedactor, WordRedactor, ExcelRedactor, ImageRedactor  # type: ignore
    REDACTORS_AVAILABLE = True
except ImportError:
    try:
        from src.redactors import PdfRedactor, WordRedactor, ExcelRedactor, ImageRedactor
        REDACTORS_AVAILABLE = True
    except ImportError:
        pass

# ─── תרגום סוגי ישויות לעברית ────────────────────────────────────
ENTITY_HEBREW = {
    # ישראלי
    "IL_ID":              "תעודת זהות ישראלית",
    "israeli_id":         "תעודת זהות ישראלית",
    "IL_PHONE":           "מספר טלפון ישראלי",
    "HEB_ADDRESS":        "כתובת בעברית",
    "HEB_NAME":           "שם בעברית",
    "DATE_OF_BIRTH":      "תאריך לידה",
    "IL_PERSONAL_NUMBER": "מספר אישי",
    "military_id":        "מספר אישי צבאי",
    "IL_BANK_ACCOUNT":    "חשבון בנק ישראלי",
    "IL_BANK_BRANCH":     "סניף בנק",
    # context-based (basic detector)
    "context_id":         "תעודת זהות (הקשר)",
    "context_phone":      "טלפון (הקשר)",
    "context_name":       "שם אדם (הקשר)",
    "context_birthdate":  "תאריך לידה (הקשר)",
    "context_address":    "כתובת (הקשר)",
    "context_bank":       "חשבון בנק (הקשר)",
    "context_personal_num": "מספר אישי (הקשר)",
    "context_password":   "סיסמה (הקשר)",
    "context_health_fund": "קופת חולים (הקשר)",
    "context_company_id": "ח.פ / תיק ניכויים (הקשר)",
    "context_medical_record": "תיק רפואי (הקשר)",
    "context_blood_type": "סוג דם (הקשר)",
    "context_military_profile": "פרופיל צבאי/רפואי (הקשר)",
    "context_cvv": "קוד אבטחה כרטיס (הקשר)",
    "context_auth_code": "קוד אימות/גישה (הקשר)",
    "context_username": "שם משתמש (הקשר)",
    "context_passport": "דרכון (הקשר)",
    "context_driver_license": "רישיון נהיגה (הקשר)",
    "context_license_plate": "לוחית רישוי (הקשר)",
    "context_mac_address": "כתובת MAC (הקשר)",
    "context_zipcode": "מיקוד (הקשר)",
    "keyword_medical":    "מידע רפואי",
    "keyword_financial":  "מידע פיננסי",
    "keyword_personal":   "מידע אישי",
    "keyword_identification": "מסמך זיהוי",
    # כללי
    "PERSON":             "שם אדם",
    "EMAIL_ADDRESS":      "כתובת אימייל",
    "PHONE_NUMBER":       "מספר טלפון",
    "CREDIT_CARD":        "כרטיס אשראי",
    "IBAN_CODE":          "מספר IBAN (חשבון בנק)",
    "iban":               "מספר חשבון בנק בינלאומי (IBAN)",
    "vehicle_license_plate": "לוחית רישוי (רכב)",
    "CRYPTO":             "ארנק קריפטו",
    "LOCATION":           "מיקום / כתובת",
    "DATE_TIME":          "תאריך / שעה",
    "NRP":                "לאום / דת / גזע",
    "MEDICAL_LICENSE":    "רישיון רפואי",
    "URL":                "כתובת אתר",
    "IP_ADDRESS":         "כתובת IP",
    "ip_address":         "כתובת רשת (IP)",
    "AGE":                "גיל",
    "JOB_TITLE":          "תפקיד",
    "PROFESSION":         "מקצוע",
    "PASSWORD":           "סיסמה",
    "HEALTH_FUND":        "מספר עמית קופת חולים",
    "IL_COMPANY_ID":      "ח.פ / תיק ניכויים",
    "MEDICAL_RECORD":     "מספר תיק רפואי",
    "BLOOD_TYPE":         "סוג דם",
    "MILITARY_PROFILE":   "פרופיל צבאי/רפואי",
    "CVV":                "קוד אבטחה (CVV)",
    "AUTH_CODE":          "קוד אימות / PIN",
    "USERNAME":           "שם משתמש",
    "PASSPORT":           "דרכון",
    "DRIVER_LICENSE":     "רישיון נהיגה",
    "LICENSE_PLATE":      "לוחית רישוי / רכב",
    "MAC_ADDRESS":        "כתובת MAC",
    "ZIPCODE":            "מיקוד",
    "passport":           "מספר דרכון (זר)",
    "biometric":          "מידע ביומטרי / גנטי",
    "criminal_record":    "רישום ועבר פלילי",
    "beliefs_and_views":  "דעות וצנעת אישות",
    # אמריקאי
    "US_SSN":             "מזהה אמריקאי (SSN)",
    "US_PASSPORT":        "דרכון אמריקאי",
    "US_DRIVER_LICENSE":  "רישיון נהיגה אמריקאי",
    "US_BANK_NUMBER":     "מספר חשבון בנק (US)",
    "US_ITIN":            "מזהה מס אמריקאי",
}

def translate_entity(entity_type: str) -> str:
    """מתרגם שם ישות מאנגלית לעברית"""
    if not entity_type: return ""
    if entity_type in ENTITY_HEBREW: return ENTITY_HEBREW[entity_type]
    if entity_type.upper() in ENTITY_HEBREW: return ENTITY_HEBREW[entity_type.upper()]
    
    try:
        from src.detectors.basic_detector import category_display_name
        res = category_display_name(entity_type)
        if res != entity_type: return res
    except Exception:
        pass

    fallback = {
        "email": "כתובת אימייל",
        "bank_account": "חשבון בנק",
        "postal_code": "מיקוד",
        "heb_address": "כתובת מגורים",
        "website": "אתר אינטרנט",
        "financial_amount": "סכום כספי"
    }
    return fallback.get(entity_type, entity_type)

# ─── cache: load engines once ────────────────────────────────────
@st.cache_resource(show_spinner="⏳ טוען מנועי AI... (רק בפעם הראשונה)")
@trace_execution
def load_all_engines_v3():
    detector       = BasicPIIDetector()
    image_proc     = ImageProcessor()
    pdf_proc       = PDFProcessor()
    word_proc      = WordProcessor()
    excel_proc     = ExcelProcessor()
    ai_pipeline    = None
    ai_error       = None
    if AI_PIPELINE_AVAILABLE:
        try:
            ai_pipeline = PIIPipeline()
        except Exception as e:
            ai_error = str(e)
    return detector, image_proc, pdf_proc, word_proc, excel_proc, ai_pipeline, ai_error

# load_ocr_engine removed. Tesseract is used directly.

detector, image_processor, pdf_processor, word_processor, excel_processor, ai_pipeline, _ai_error = load_all_engines_v3()

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🔒 PII Detection")
    st.caption("פרויקט גמר 2026")
    st.divider()

    st.subheader("⚙️ מנוע זיהוי")
    engine_mode = st.radio(
        "בחר מצב:",
        ["💻 מחשב רגיל (מהיר, Regex)", "🚀 מחשב חדש (AI מתקדם)"],
        index=0,
    )
    USE_AI = "חדש" in engine_mode

    st.divider()
    st.subheader("📊 סטטוס")

    st.success("✅ מנוע Regex")

    if TESSERACT_OK:
        try:
            st.success(f"✅ Tesseract {pytesseract.get_tesseract_version()}")
        except Exception:
            st.warning("⚠️ Tesseract - שגיאה")
    else:
        st.error("❌ Tesseract לא מותקן")

    if AI_PIPELINE_AVAILABLE and ai_pipeline:
        st.success("✅ Presidio AI")
    elif AI_PIPELINE_AVAILABLE:
        st.warning("⚠️ AI - כשל בטעינה")
        if st.button("🔄 טען מחדש"):
            st.cache_resource.clear()
            st.rerun()
    else:
        st.error("❌ Presidio לא מותקן")

    if REDACTORS_AVAILABLE:
        st.success("✅ מנוע השחרה")
    else:
        st.error("❌ מנוע השחרה חסר")

    st.divider()
    st.caption("🔒 כל הניתוחים מקומיים בלבד — ללא שידור לרשת")

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════
st.title("🔒 מערכת זיהוי מידע אישי רגיש")
st.write("העלה File, ראה **תצוגה מקדימה** של הfindings, ואז בחר מה להשחיר.")

if USE_AI and not ai_pipeline:
    st.warning("⚠️ מנוע AI לא זמין — עובד במצב Regex.")
    USE_AI = False

st.divider()

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def sensitivity_icon(name: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(name, "⚪")


@trace_execution
def show_preview_and_redact(entities: list, file_bytes: bytes, filename: str, original_text: str = "", unique_key: str = ""):
    """
    הצג טבלת תצוגה מקדימה של ממצאי PII עם checkbox לכל שורה.
    לאחר בחירה — לחצן השחרה שמוריד את הFile המושחר.
    """
    if not entities:
        st.success("✅ לא נמצא מידע רגיש אוטומטית. באפשרותך להוסיף טקסט להשחרה בטבלה מטה ידנית.")
        df = pd.DataFrame(columns=["השחר?", "#", "טקסט", "סוג", "ודאות", "רגישות"])
        df["השחר?"] = df["השחר?"].astype(bool)
    else:
        df = pd.DataFrame([{
            "השחר?":    True,
            "#":         i + 1,
            "טקסט":      e.get("text", ""),
            "סוג":       translate_entity(e.get("entity_type", e.get("category", ""))),
            "ודאות":     f"{e.get('score', e.get('confidence', 0)):.0%}",
            "רגישות":    e.get("sensitivity", ""),
        } for i, e in enumerate(entities)])

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # ─── כותרת ─────────────────────────────────────────────────────
    st.subheader(f"🔍 נמצאו {len(entities)} פריטים (ניתן להוסיף ידנית) — בחר מה להשחיר")
    st.caption("סמן ✅ את הfindings שברצונך להשחיר בFile הסופי, ואז לחץ 'בצע השחרה'.")

    main_col1, main_col2 = st.columns([1, 1.2])

    with main_col1:
        st.markdown("**רשימת findings (טבלה לבחירה):**")
        edited_df = st.data_editor(
            df,
            column_config={
                "השחר?": st.column_config.CheckboxColumn("השחר?", default=True),
                "#":      st.column_config.NumberColumn("#", width="small"),
                "טקסט":    st.column_config.TextColumn("טקסט", required=True),
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=f"preview_{unique_key}_{filename}"
        )

        # ─── סיכום בחירה ───────────────────────────────────────────────
        selected_texts = edited_df[edited_df["השחר?"] == True]["טקסט"].tolist()
        total_selected = len(selected_texts)

        sub_col1, sub_col2, sub_col3 = st.columns(3)
        sub_col1.metric("סה״כ", len(entities))
        sub_col2.metric("נבחרו", total_selected)
        sub_col3.metric("יישארו", len(entities) - total_selected)

    with main_col2:
        st.markdown("**תצוגת המסמך:**")
        if ext in ("docx", "xlsx"):
            cache_key_base = f"base_office_{filename}"
            if cache_key_base not in st.session_state:
                with st.spinner("מייצר תצוגה ויזואלית מקדימה (המתן מעט)..."):
                    try:
                        from src.utils.pdf_converter import convert_office_to_pdf
                        base_pdf_bytes = convert_office_to_pdf(file_bytes, ext)
                        st.session_state[cache_key_base] = base_pdf_bytes
                    except Exception as e:
                        st.error(f"שגיאה ביצירת תצוגה ויזואלית: {e}")
                        st.session_state[cache_key_base] = None
                        
            base_pdf_bytes = st.session_state.get(cache_key_base)
            if base_pdf_bytes:
                from src.utils.pdf_converter import get_highlighted_images_from_pdf
                # סמן רק את הטקסטים שנבחרו בטבלה! (ככה זה מעודכן אוטומטית כשמסירים סימון)
                selected_entities = [{"text": t} for t in selected_texts]
                
                with st.spinner("מרנדר סימונים על המסמך..."):
                    images = get_highlighted_images_from_pdf(base_pdf_bytes, selected_entities)
                
                if images:
                    for idx, img_bytes in enumerate(images):
                        st.image(img_bytes, caption=f"עמוד {idx+1}", use_column_width=True)
                else:
                    st.info("שגיאה ברינדור התמונות או שאין עמודים להצגה.")
            else:
                # Fallback to text
                if original_text:
                    st.text_area("תוכן המסמך (קריאה בלבד)", original_text, height=400, disabled=True, key=f"text_preview_{unique_key}_{filename}")
                else:
                    st.info("לא סופק טקסט לתצוגה מקדימה במצב זה.")
        else:
            if original_text:
                st.text_area("תוכן המסמך (קריאה בלבד)", original_text, height=400, disabled=True, key=f"text_preview_{unique_key}_{filename}")
            else:
                st.info("לא סופק טקסט לתצוגה מקדימה במצב זה.")

    st.markdown("---")

    if total_selected == 0:
        st.info("לא נבחרו findings להשחרה.")
        return

    # ─── כפתור השחרה ───────────────────────────────────────────────
    if not REDACTORS_AVAILABLE:
        st.error("❌ מנוע השחרה לא זמין — לא ניתן להפיק File מושחר.")
        return

    # ─── מפתח session_state ייחודי לכל קובץ ────────────────────────
    dl_key = f"redact_result_{unique_key}_{filename}"

    if st.button(f"🖊️ בצע השחרה ({total_selected} פריטים)", type="primary", key=f"do_redact_{unique_key}_{filename}"):
        with st.spinner("מבצע השחרה על הFile..."):
            redacted_bytes = None
            mime = "application/octet-stream"
            out_name = f"redacted_{filename}"
            total_redacted_count = 0

            try:
                if ext == "pdf":
                    redactor = PdfRedactor()
                    result = redactor.redact_pdf(file_bytes, selected_texts)
                    if result and len(result) == 2:
                        redacted_bytes, total_redacted_count = result
                    mime = "application/pdf"

                elif ext == "docx":
                    redactor = WordRedactor()
                    result = redactor.redact_word(file_bytes, selected_texts)
                    if result and len(result) == 2:
                        redacted_bytes, total_redacted_count = result
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                elif ext == "xlsx":
                    redactor = ExcelRedactor()
                    result = redactor.redact_excel(file_bytes, selected_texts)
                    if result and len(result) == 2:
                        redacted_bytes, total_redacted_count = result
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                elif ext in ("jpg", "jpeg", "png", "bmp"):
                    redactor = ImageRedactor()
                    result = redactor.redact_image(file_bytes, selected_texts)
                    if result and len(result) == 2:
                        redacted_bytes, total_redacted_count = result
                    mime = "image/png"
                    out_name = f"redacted_{os.path.splitext(filename)[0]}.png"

                else:
                    st.error(f"❌ פורמט לא נתמך להשחרה: {ext}")

            except Exception as ex:
                st.error(f"❌ שגיאה בהשחרה: {ex}")
                app_logger.error(f"Redaction error: {ex}", exc_info=True)

        # שמירה ב-session_state כדי שכפתור ההורדה לא ייעלם אחרי rerun
        if redacted_bytes:
            st.session_state[dl_key] = {
                "bytes": redacted_bytes,
                "mime": mime,
                "name": out_name,
                "count": total_redacted_count,
                "selected": total_selected,
            }
        else:
            st.error("❌ לא בוצעו השחרות — ייתכן שהטקסטים לא נמצאו בתוך הFile בצורה הניתנת לעריכה.")

    # ─── כפתור הורדה מחוץ לבלוק הכפתור — נשאר לאחר rerun ──────────
    if dl_key in st.session_state:
        res = st.session_state[dl_key]
        st.success(f"✅ השחרה הושלמה! {res['count']} מופעים הוסרו מהמסמך.")
        if res['count'] < res['selected']:
            st.warning(f"⚠️ שים לב: {res['selected'] - res['count']} פריטים לא נמצאו בטקסט (ייתכן שהם מופיעים כתמונה).")
        st.download_button(
            label=f"⬇️ הורד קובץ מושחר ({res['name']})",
            data=res["bytes"],
            file_name=res["name"],
            mime=res["mime"],
            key=f"dl_btn_{unique_key}_{filename}",
        )


def ai_entities_to_preview(entities_from_report: list) -> list:
    """ממיר את הפורמט של AI Pipeline לפורמט אחיד לתצוגה מקדימה"""
    return [{"text": e["text"], "entity_type": e["entity_type"],
             "score": e["score"], "sensitivity": ""} for e in entities_from_report]


def basic_matches_to_preview(matches, min_confidence: float = 0.4) -> list:
    """ממיר תוצאות BasicPIIDetector לפורמט אחיד עם סינון ביטחון"""
    return [{"text": m.text, "entity_type": m.category,
             "score": m.confidence, "sensitivity": m.sensitivity.name}
            for m in matches if m.confidence >= min_confidence]


# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab_img, tab_word, tab_excel, tab_pdf = st.tabs([
    "🖼️  תמונה",
    "📝  Word",
    "📊  Excel",
    "📄  PDF"
])

@trace_execution
def process_image_visual(image_bytes: bytes, detector_engine, use_ai: bool, ai_pipeline_engine=None):
    """
    מנתח תמונה, מחלץ קואורדינטות של PII ומייצר תצוגה מקדימה מסומנת.
    """
    import io
    import numpy as np
    from PIL import Image, ImageDraw
    
    if not TESSERACT_OK:
        return [], image_bytes
        
    img = Image.open(io.BytesIO(image_bytes))
    
    # המרה ל-RGB עם רקע לבן כדי לפתור בעיית PNG שקוף במצב Dark Mode
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.convert('RGBA').split()[3])
        img = bg
    else:
        img = img.convert('RGB')
        
    # הפעלת Tesseract וקבלת נתונים עם קואורדינטות
    data = pytesseract.image_to_data(img, lang='heb+eng', output_type=pytesseract.Output.DICT)
    
    ocr_results = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if not text:
            continue
        conf = float(data['conf'][i]) / 100.0
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]
        # יצירת קואורדינטות בסגנון easyocr: [top_left, top_right, bottom_right, bottom_left]
        bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        ocr_results.append((bbox, text, conf))
    
    findings = []
    for bbox, snippet_text, conf in ocr_results:
        if not snippet_text.strip(): continue
        
        snippet_findings = []
        if use_ai and ai_pipeline_engine:
            rep = ai_pipeline_engine.process_file(file_bytes=snippet_text.encode('utf-8', errors='ignore'), filename="dummy.txt")
            if rep.get("success") and "entities" in rep:
                snippet_findings = rep["entities"]
        # Always run basic regex
        res = detector_engine.analyze_text(snippet_text)
        for match in res.get("matches", []):
            if match.confidence >= 0.3:
                snippet_findings.append({
                    "text": match.text,
                    "entity_type": match.category,
                    "score": match.confidence,
                })
        
        if snippet_findings:
            # קואורדינטות (xmin, ymin, xmax, ymax)
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            rect = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
            
            for sf in snippet_findings:
                findings.append({
                    "rect": rect,
                    "text": sf.get("text", snippet_text),
                    "type": sf.get("entity_type", sf.get("type", "PII")),
                    "score": sf.get("score", conf),
                })
    
    # המרה חזרה ל-bytes (תמונה נקייה)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return findings, img_byte_arr.getvalue()


# ────────────────────────────────────────────────────────────────────
# TAB 1 — תמונה
# ────────────────────────────────────────────────────────────────────
with tab_img:
    st.header("🖼️ ניתוח תמונה")
    st.caption("JPG, PNG, BMP — חילוץ טקסט OCR + זיהוי PII + תצוגה מקדימה ויזואלית")

    if not TESSERACT_OK:
        st.warning("⚠️ Tesseract לא מותקן.")
    else:
        uploaded = st.file_uploader("📂 בחר File תמונה", type=["jpg", "jpeg", "png", "bmp"], key="img_up")
        if uploaded:
            if st.button("🔍 Analyze Image", key="btn_img", type="primary"):
                with st.spinner("מנתח תמונה ומזהה PII..."):
                    raw = uploaded.getvalue()
                    findings, preview_bytes = process_image_visual(raw, detector, USE_AI, ai_pipeline)
                    
                    st.session_state["img_visual_findings"] = findings
                    st.session_state["img_visual_preview"] = preview_bytes
                    st.session_state["img_bytes"] = raw
                    st.session_state["img_name"] = uploaded.name

            if "img_visual_preview" in st.session_state and st.session_state.get("img_name") == uploaded.name:
                st.divider()
                
                findings = st.session_state["img_visual_findings"]
                
                st.subheader("👀 תצוגה מקדימה ובחירת השחרה")
                st.write("סמן בטבלה אילו אזורים להשחיר, או שרטט בעכבר מלבנים ישירות על התמונה.")
                
                st.markdown("### 📋 רשימת findings אוטומטיים")
                if not findings:
                    st.info("לא זוהו אוטומטית ממצאים להשחרה. באפשרותך להוסיף טקסט להשחרה ידנית או לצייר מלבנים על המסמך.")
                    df = pd.DataFrame(columns=["השחר?", "טקסט", "סוג"])
                    df["השחר?"] = df["השחר?"].astype(bool)
                else:
                    df = pd.DataFrame([{
                        "השחר?": True,
                        "טקסט": f.get("text", ""),
                        "סוג": translate_entity(f.get("type", "")),
                    } for f in findings])
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "השחר?": st.column_config.CheckboxColumn("השחר?", default=True),
                        "טקסט": st.column_config.TextColumn("טקסט", required=True),
                    },
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key=f"img_preview_{uploaded.name}"
                )
                selected_indices = edited_df[edited_df["השחר?"] == True].index.tolist()
                
                for idx in selected_indices:
                    if idx >= len(findings):
                        row = edited_df.loc[idx]
                        if row["טקסט"]:
                            findings.append({
                                "text": row["טקסט"],
                                "type": "MANUAL",
                            })
                            
                st.divider()
                st.markdown("### 🖼️ תצוגת המסמך")
                st.warning("⚠️ **שים לב:** אל תשתמש בכפתור ההורדה הקטן שבתוך התמונה. בסיום הציור, לחץ על 'בצע השחרה מדויקת' למטה!")
                
                col_draw1, col_draw2 = st.columns(2)
                with col_draw1:
                    drawing_mode_text = st.radio("מצב עכבר:", ["🖌️ ציור מלבנים שחורים", "🖱️ בחירה ומחיקת מלבנים (למה שציירת)"], horizontal=True, key=f"mode_img_{uploaded.name}")
                drawing_mode = "rect" if "ציור" in drawing_mode_text else "transform"
                
                from streamlit_drawable_canvas import st_canvas
                import io
                import base64
                
                # Caching data URL for performance
                cache_key_url = f"img_data_url_{uploaded.name}"
                if cache_key_url not in st.session_state:
                    from PIL import Image
                    bg_image = Image.open(io.BytesIO(st.session_state["img_visual_preview"]))
                    buffered = io.BytesIO()
                    bg_image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    st.session_state[cache_key_url] = f"data:image/png;base64,{img_str}"
                    st.session_state[f"img_w_{uploaded.name}"] = bg_image.width
                    st.session_state[f"img_h_{uploaded.name}"] = bg_image.height
                
                data_url = st.session_state[cache_key_url]
                bg_width = st.session_state[f"img_w_{uploaded.name}"]
                bg_height = st.session_state[f"img_h_{uploaded.name}"]
                
                init_drawing = {
                    "version": "4.4.0",
                    "objects": [{
                        "type": "image",
                        "left": 0, "top": 0,
                        "width": bg_width, "height": bg_height,
                        "src": data_url,
                        "selectable": False,
                        "evented": False,
                        "crossOrigin": None
                    }]
                }
                
                # 1. הזרקת מלבנים צהובים (אוטומטיים) רק עבור מה שמסומן בטבלה
                for idx in selected_indices:
                    if idx < len(findings):
                        f = findings[idx]
                        if "rect" in f:
                            init_drawing["objects"].append({
                                "type": "rect",
                                "left": f["rect"][0],
                                "top": f["rect"][1],
                                "width": f["rect"][2] - f["rect"][0],
                                "height": f["rect"][3] - f["rect"][1],
                                "fill": "rgba(255, 255, 0, 0.4)",
                                "stroke": "rgba(255, 165, 0, 1)",
                                "strokeWidth": 2,
                                "selectable": False,
                                "evented": False,
                                "is_auto": True
                            })
                
                # 2. שחזור מלבנים ידניים (שחורים) שהמשתמש צייר קודם
                canvas_state = st.session_state.get(f"canvas_img_{uploaded.name}")
                if canvas_state is not None and "json_data" in canvas_state and canvas_state["json_data"] is not None:
                    for obj in canvas_state["json_data"].get("objects", []):
                        if obj.get("type") == "rect" and obj.get("fill") == "rgba(0, 0, 0, 1)":
                            init_drawing["objects"].append(obj)
                
                canvas_res = st_canvas(
                    fill_color="rgba(0, 0, 0, 1)",
                    stroke_width=2,
                    stroke_color="rgba(255, 0, 0, 1)",
                    background_color="rgba(0,0,0,0)",
                    initial_drawing=init_drawing,
                    update_streamlit=True,
                    height=bg_height,
                    width=bg_width,
                    drawing_mode=drawing_mode,
                    display_toolbar=(drawing_mode == "transform"),
                    key=f"canvas_img_{uploaded.name}",
                )
                            
                st.markdown("---")
                if st.button("🖊️ בצע השחרה מדויקת", type="primary", key="btn_redact_img"):
                    if not REDACTORS_AVAILABLE:
                        st.error("❌ מנוע ההשחרה חסר, לא ניתן להשחיר.")
                    else:
                        with st.spinner("מבצע השחרה פיזית (מלבנים שחורים)..."):
                            selected_findings = []
                            if findings:
                                selected_findings.extend([findings[i] for i in selected_indices])
                            
                            if canvas_res is not None and canvas_res.json_data is not None:
                                for obj in canvas_res.json_data.get("objects", []):
                                    if obj.get("type") == "rect" and obj.get("fill") == "rgba(0, 0, 0, 1)":
                                        x0 = obj["left"]
                                        y0 = obj["top"]
                                        x1 = x0 + obj["width"] * obj["scaleX"]
                                        y1 = y0 + obj["height"] * obj["scaleY"]
                                        
                                        selected_findings.append({
                                            "rect": [x0, y0, x1, y1]
                                        })
                            
                            if not selected_findings:
                                st.warning("לא סומנו אזורים להשחרה.")
                            else:
                                redactor = ImageRedactor()
                                redacted_bytes = redactor.redact_image_by_coords(st.session_state["img_bytes"], selected_findings)
                                
                                if redacted_bytes:
                                    st.session_state["img_ready_for_download"] = True
                                    st.session_state["img_redacted_bytes"] = redacted_bytes
                                    st.session_state["img_out_name"] = f"redacted_{uploaded.name}"
                                    st.rerun()
                                else:
                                    st.error("❌ שגיאה ביצירת התמונה המושחרת.")
                
                if st.session_state.get("img_ready_for_download") and st.session_state.get("img_redacted_bytes"):
                    st.success("✅ ההשחרה הושלמה בהצלחה!")
                    import base64
                    b64 = base64.b64encode(st.session_state["img_redacted_bytes"]).decode()
                    href = f'''
                    <a href="data:application/octet-stream;base64,{b64}" download="{st.session_state["img_out_name"]}" 
                       style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #6c63ff; 
                              border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #5a52d5;">
                       ⬇️ הורד תמונה מושחרת (הורדה ישירה)
                    </a>
                    <br><br>
                    '''
                    st.markdown(href, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# TAB 2 — Word
# ────────────────────────────────────────────────────────────────────
with tab_word:
    st.header("📝 ניתוח מסמך Word")
    st.caption("DOCX — מחלץ טקסט כולל טבלאות + זיהוי PII + תצוגה מקדימה + השחרה")

    uploaded = st.file_uploader("📂 בחר File Word", type=["docx"], key="word_up")
    if uploaded:
        st.info(f"📄 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        if st.button("🔍 Analyze Word", key="btn_word", type="primary"):
            with st.spinner("Extracting and Analyzing..."):
                raw = uploaded.getvalue()
                if USE_AI and ai_pipeline:
                    rep = ai_pipeline.process_file(file_bytes=raw, filename=uploaded.name)
                    if rep["success"]:
                        entities = ai_entities_to_preview(rep["entities"])
                        text = rep.get("original_text", rep.get("anonymized_text", ""))
                    else:
                        st.error(f"❌ {rep.get('error')}")
                        entities = []
                        text = ""
                else:
                    word_res = word_processor.extract_text_from_word(raw, uploaded.name)
                    if word_res["success"]:
                        text = word_res["text"]
                        res = detector.analyze_text(text)
                        entities = basic_matches_to_preview(res["matches"])
                    else:
                        st.error(f"❌ Error: {word_res.get('error')}")
                        entities = []
                        text = ""

            st.session_state["word_entities"] = entities
            st.session_state["word_bytes"]    = raw
            st.session_state["word_name"]     = uploaded.name
            st.session_state["word_text"]     = text

        if "word_entities" in st.session_state and st.session_state.get("word_name") == uploaded.name:
            st.divider()
            show_preview_and_redact(
                st.session_state["word_entities"],
                st.session_state["word_bytes"],
                st.session_state["word_name"],
                original_text=st.session_state.get("word_text", ""),
                unique_key="word"
            )

# ────────────────────────────────────────────────────────────────────
# TAB 3 — Excel
# ────────────────────────────────────────────────────────────────────
with tab_excel:
    st.header("📊 ניתוח File Excel")
    st.caption("XLSX — סריקת כל הגיליונות + זיהוי PII + תצוגה מקדימה + השחרה")

    uploaded = st.file_uploader("📂 בחר File Excel", type=["xlsx"], key="excel_up")
    if uploaded:
        st.info(f"📊 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        if st.button("🔍 Analyze Excel", key="btn_excel", type="primary"):
            with st.spinner("Reading sheets..."):
                raw = uploaded.getvalue()
                if USE_AI and ai_pipeline:
                    rep = ai_pipeline.process_file(file_bytes=raw, filename=uploaded.name)
                    if rep["success"]:
                        entities = ai_entities_to_preview(rep["entities"])
                        text = rep.get("original_text", rep.get("anonymized_text", ""))
                    else:
                        st.error(f"❌ {rep.get('error')}")
                        entities = []
                        text = ""
                else:
                    excel_res = excel_processor.extract_text_from_excel(raw, uploaded.name)
                    if excel_res["success"]:
                        text = excel_res["text"]
                        res = detector.analyze_text(text)
                        entities = basic_matches_to_preview(res["matches"])
                    else:
                        st.error(f"❌ Error: {excel_res.get('error')}")
                        entities = []
                        text = ""

            st.session_state["excel_entities"] = entities
            st.session_state["excel_bytes"]    = raw
            st.session_state["excel_name"]     = uploaded.name
            st.session_state["excel_text"]     = text
            st.session_state["excel_bytes"]    = raw
            st.session_state["excel_name"]     = uploaded.name
            st.session_state["excel_text"]     = text

        if "excel_entities" in st.session_state and st.session_state.get("excel_name") == uploaded.name:
            st.divider()
            show_preview_and_redact(
                st.session_state["excel_entities"],
                st.session_state["excel_bytes"],
                st.session_state["excel_name"],
                original_text=st.session_state.get("excel_text", ""),
                unique_key="excel"
            )

# ────────────────────────────────────────────────────────────────────
@trace_execution
def process_pdf_visual(file_bytes: bytes, detector_engine, use_ai: bool, ai_pipeline_engine=None):
    """
    סורק PDF, מחלץ קואורדינטות של מידע רגיש, ומייצר תמונות להשחרה.
    תומך בצורה אחידה במסמכים רגילים ובמסמכים סרוקים (OCR).
    """
    import fitz
    from PIL import Image
    import io
    
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    findings = []
    page_images = []
    
    # מילות מפתח לחיפוש מרחבי
    SPATIAL_LABELS = {
        "מספר אישי": "IL_PERSONAL_NUMBER",
        "מ.א.": "IL_PERSONAL_NUMBER",
        "תעודת זהות": "IL_ID",
        "ת.ז": "IL_ID",
        "שם פרטי": "HEB_NAME",
        "שם משפחה": "HEB_NAME",
        "תאריך לידה": "DATE_OF_BIRTH",
        "חשבון בנק": "IL_BANK_ACCOUNT",
    }
    
    for page_num in range(len(doc)):
        log_progress(page_num + 1, len(doc), "Visual PDF Scan")
        page = doc[page_num]
        text = page.get_text()
        
        # האם להשתמש ב-OCR?
        # במסמכים סרוקים או עם קידוד פגום, PyMuPDF שולף אותיות באנגלית/מספרים במקום עברית.
        heb_chars = sum(1 for c in text if 0x0590 <= ord(c) <= 0x05FF)
        total_chars = len(text.strip())
        
        # אם הטקסט קצר מדי, או שאין כמעט עברית בטקסט ארוך (מה שמעיד על קידוד פגום) נפעיל OCR
        should_ocr = False
        if total_chars < 50:
            should_ocr = True
        elif heb_chars < (total_chars * 0.05):
            should_ocr = True
        
        words = [] # יכיל: (x0, y0, x1, y1, text)
        
        if should_ocr and TESSERACT_OK:
            import pytesseract
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img = Image.open(io.BytesIO(pix.tobytes()))
            data = pytesseract.image_to_data(img, lang='heb+eng', output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                txt = data['text'][i].strip()
                if txt:
                    # Tesseract רץ על פי 2 מהגודל המקורי, נחלק ב-2
                    x = data['left'][i] / 2.0
                    y = data['top'][i] / 2.0
                    w = data['width'][i] / 2.0
                    h = data['height'][i] / 2.0
                    words.append((x, y, x + w, y + h, txt))
        else:
            for w in page.get_text("words"):
                words.append((w[0], w[1], w[2], w[3], w[4]))
                
        page_findings = []
        
        # 1. לוגיקה מרחבית (Spatial) - חיפוש לפי כותרות
        for word_data in words:
            w_text = word_data[4]
            w_rect = fitz.Rect(word_data[:4])
            
            label_type = None
            for lab, l_type in SPATIAL_LABELS.items():
                if lab in w_text or lab[::-1] in w_text:
                    label_type = l_type
                    break
            
            if label_type:
                # מצאנו כותרת, נחפש מעליה או מתחתיה
                search_area = w_rect + (-50, -60, 50, 10)
                for other_word in words:
                    o_text = other_word[4]
                    o_rect = fitz.Rect(other_word[:4])
                    if o_rect.intersects(search_area) and o_text != w_text:
                        is_val = any(c.isdigit() for c in o_text) or any(0x0590 <= ord(c) <= 0x05FF for c in o_text)
                        if is_val and len(o_text) >= 2:
                            page_findings.append({
                                "page": page_num,
                                "rect": [o_rect.x0, o_rect.y0, o_rect.x1, o_rect.y1],
                                "text": o_text,
                                "type": label_type,
                                "score": 0.99,
                                "id": f"spatial_{page_num}_{o_rect.x0}_{o_rect.y0}"
                            })

        # 2. זיהוי טקסט מלא (Regex + AI)
        full_text = " ".join([w[4] for w in words])
        all_entities = []
        
        # תמיד מריצים Regex
        res = detector_engine.analyze_text(full_text)
        for match in res.get("matches", []):
            if match.confidence >= 0.3:
                all_entities.append({"text": match.text, "type": match.category, "score": match.confidence})
                
        # אם AI מופעל
        if use_ai and ai_pipeline_engine:
            rep = ai_pipeline_engine.process_file(file_bytes=full_text.encode('utf-8', errors='ignore'), filename="dummy.txt")
            if rep.get("success") and "entities" in rep:
                for e in rep["entities"]:
                    all_entities.append({"text": e.get("text", ""), "type": e.get("entity_type", "PII"), "score": e.get("score", 0.8)})
                    
        # 3. חיפוש קואורדינטות לישויות שנמצאו
        for e in all_entities:
            e_text = e["text"]
            if not e_text.strip(): continue
            
            if not should_ocr:
                # חיפוש מובנה ב-PDF מהיר ומדויק
                search_texts = [e_text]
                if any(0x0590 <= ord(c) <= 0x05FF for c in e_text):
                    search_texts.append(e_text[::-1])
                for s_text in search_texts:
                    for area in page.search_for(s_text):
                        page_findings.append({
                            "page": page_num,
                            "rect": [area.x0, area.y0, area.x1, area.y1],
                            "text": e_text,
                            "type": e["type"],
                            "score": e["score"],
                            "id": f"{page_num}_{area.x0}_{area.y0}"
                        })
            else:
                # ב-OCR מחפשים מול רשימת המילים שלנו
                for w in words:
                    if e_text in w[4] or w[4] in e_text:
                        if len(w[4]) >= 2:
                            page_findings.append({
                                "page": page_num,
                                "rect": [w[0], w[1], w[2], w[3]],
                                "text": e_text,
                                "type": e["type"],
                                "score": e["score"],
                                "id": f"ocr_match_{page_num}_{w[0]}_{w[1]}"
                            })

        # --- סינון כפילויות ---
        unique_page_findings = []
        for f in page_findings:
            is_dup = False
            f_rect = fitz.Rect(f["rect"])
            for uf in unique_page_findings:
                if f["type"] == uf["type"] and fitz.Rect(uf["rect"]).intersects(f_rect):
                    is_dup = True
                    break
            if not is_dup:
                unique_page_findings.append(f)
                
        findings.extend(unique_page_findings)
        
        # --- רינדור תמונה נקייה ---
        temp_doc = fitz.open(stream=file_bytes, filetype="pdf")
        temp_page = temp_doc[page_num]
        pix = temp_page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False) 
        page_images.append(pix.tobytes("png"))
        temp_doc.close()
        
    doc.close()
    return findings, page_images


# ────────────────────────────────────────────────────────────────────
# TAB 4 — PDF
# ────────────────────────────────────────────────────────────────────
with tab_pdf:
    st.header("📄 ניתוח File PDF (תצוגה ויזואלית חכמה)")
    st.caption("PDF רגיל וסרוק + זיהוי PII + תצוגה מקדימה אמיתית של העמודים והשחרה by coordinates")

    uploaded = st.file_uploader("📂 בחר File PDF", type=["pdf"], key="pdf_up")
    if uploaded:
        st.info(f"📄 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        
        if st.button("🔍 נתח PDF (מצב ויזואלי)", key="btn_pdf", type="primary"):
            with st.spinner("סורק מסמך, מאתר קואורדינטות ומרנדר pages..."):
                raw = uploaded.getvalue()
                findings, images = process_pdf_visual(raw, detector, USE_AI, ai_pipeline)
                
                if findings:
                    st.success(f"✅ Found {len(findings)} findings רגישים!")
                else:
                    st.success("✅ המסמך נקי ממידע רגיש.")
                    
                st.session_state["pdf_visual_findings"] = findings
                st.session_state["pdf_visual_images"] = images
                st.session_state["pdf_bytes"]    = raw
                st.session_state["pdf_name"]     = uploaded.name

        if "pdf_visual_findings" in st.session_state and st.session_state.get("pdf_name") == uploaded.name:
            st.divider()
            
            findings = st.session_state["pdf_visual_findings"]
            images = st.session_state["pdf_visual_images"]
            
            st.subheader("👀 תצוגה מקדימה ובחירת השחרה")
            st.write("סמן בטבלה אילו אזורים להשחיר, או שרטט בעכבר מלבנים ישירות על המסמך (כמו בצייר).")
            
            # --- טבלה למעלה ---
            st.markdown("### 📋 רשימת findings אוטומטיים")
            if not findings:
                st.info("לא זוהו אוטומטית ממצאים להשחרה. באפשרותך להוסיף טקסט להשחרה ידנית או לצייר מלבנים על המסמך.")
                df = pd.DataFrame(columns=["השחר?", "עמוד", "טקסט", "סוג"])
                df["השחר?"] = df["השחר?"].astype(bool)
            else:
                df = pd.DataFrame([{
                    "השחר?": True,
                    "עמוד": f.get("page", 0) + 1,
                    "טקסט": f.get("text", ""),
                    "סוג": translate_entity(f.get("type", "")),
                } for f in findings])
            
            edited_df = st.data_editor(
                df,
                column_config={
                    "השחר?": st.column_config.CheckboxColumn("השחר?", default=True),
                    "טקסט": st.column_config.TextColumn("טקסט", required=True),
                    "עמוד": st.column_config.NumberColumn("עמוד (אופציונלי)", required=False)
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key=f"pdf_preview_{uploaded.name}"
            )
            selected_indices = edited_df[edited_df["השחר?"] == True].index.tolist()  # noqa: E712
            
            # הוספת שורות ידניות למערך findings
            for idx in selected_indices:
                if idx >= len(findings):
                    row = edited_df.loc[idx]
                    if row["טקסט"]:
                        findings.append({
                            "text": row["טקסט"],
                            "type": "MANUAL",
                            "page": row.get("עמוד", 1) - 1 if pd.notna(row.get("עמוד")) else 0
                        })
            
            st.divider()
            
            # --- מסמך בגודל מלא ---
            st.markdown("### 🖼️ תצוגת המסמך")
            st.warning("⚠️ **שים לב:** אל תשתמש בכפתור ההורדה הקטן שבתוך התמונה. בסיום הציור, לחץ על 'בצע השחרה מדויקת' למטה!")
            
            col_draw1, col_draw2 = st.columns(2)
            with col_draw1:
                drawing_mode_text = st.radio("מצב עכבר (לכל העמודים):", ["🖌️ ציור מלבנים שחורים", "🖱️ בחירה ומחיקת מלבנים (למה שציירת)"], horizontal=True, key=f"mode_pdf_{uploaded.name}")
            drawing_mode = "rect" if "ציור" in drawing_mode_text else "transform"
            
            from streamlit_drawable_canvas import st_canvas
            import io
            import base64
            
            # Caching to prevent slow reruns
            cache_pdf_urls = f"pdf_data_urls_{uploaded.name}"
            if cache_pdf_urls not in st.session_state:
                st.session_state[cache_pdf_urls] = {}
            pdf_data_urls = st.session_state[cache_pdf_urls]
            
            canvas_results = []
            for page_num, img_bytes in enumerate(images):
                st.write(f"**Page {page_num + 1}**")
                
                if page_num not in pdf_data_urls:
                    from PIL import Image
                    bg_image = Image.open(io.BytesIO(img_bytes))
                    if bg_image.mode in ('RGBA', 'LA') or (bg_image.mode == 'P' and 'transparency' in bg_image.info):
                        bg = Image.new("RGB", bg_image.size, (255, 255, 255))
                        bg.paste(bg_image, mask=bg_image.convert('RGBA').split()[3])
                        bg_image = bg
                    else:
                        bg_image = bg_image.convert('RGB')
                    
                    buffered = io.BytesIO()
                    bg_image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    pdf_data_urls[page_num] = {
                        "url": f"data:image/png;base64,{img_str}",
                        "w": bg_image.width,
                        "h": bg_image.height
                    }
                
                cached_page = pdf_data_urls[page_num]
                data_url = cached_page["url"]
                bg_width = cached_page["w"]
                bg_height = cached_page["h"]
                
                init_drawing = {
                    "version": "4.4.0",
                    "objects": [{
                        "type": "image",
                        "left": 0, "top": 0,
                        "width": bg_width, "height": bg_height,
                        "src": data_url,
                        "selectable": False,
                        "evented": False,
                        "crossOrigin": None
                    }]
                }
                
                # 1. מלבנים צהובים (אוטומטיים) של העמוד הנוכחי
                # Scale by 1.2 to match PyMuPDF get_pixmap matrix!
                for idx in selected_indices:
                    if idx < len(findings):
                        f = findings[idx]
                        if f.get("page", 0) == page_num and "rect" in f:
                            init_drawing["objects"].append({
                                "type": "rect",
                                "left": f["rect"][0] * 1.2,
                                "top": f["rect"][1] * 1.2,
                                "width": (f["rect"][2] - f["rect"][0]) * 1.2,
                                "height": (f["rect"][3] - f["rect"][1]) * 1.2,
                                "fill": "rgba(255, 255, 0, 0.4)",
                                "stroke": "rgba(255, 165, 0, 1)",
                                "strokeWidth": 2,
                                "selectable": False,
                                "evented": False,
                                "is_auto": True
                            })
                
                # 2. מלבנים שחורים (ידניים) של העמוד הנוכחי
                canvas_state = st.session_state.get(f"canvas_{uploaded.name}_{page_num}")
                if canvas_state is not None and "json_data" in canvas_state and canvas_state["json_data"] is not None:
                    for obj in canvas_state["json_data"].get("objects", []):
                        if obj.get("type") == "rect" and obj.get("fill") == "rgba(0, 0, 0, 1)":
                            init_drawing["objects"].append(obj)
                
                canvas_res = st_canvas(
                    fill_color="rgba(0, 0, 0, 1)",
                    stroke_width=2,
                    stroke_color="rgba(255, 0, 0, 1)",
                    background_color="rgba(0,0,0,0)",
                    initial_drawing=init_drawing,
                    update_streamlit=True,
                    height=bg_height,
                    width=bg_width,
                    drawing_mode=drawing_mode,
                    display_toolbar=(drawing_mode == "transform"),
                    key=f"canvas_{uploaded.name}_{page_num}",
                )
                canvas_results.append((page_num, canvas_res))

            st.markdown("---")
            if st.button("🖊️ בצע השחרה מדויקת", type="primary"):
                if not REDACTORS_AVAILABLE:
                    st.error("❌ מנוע ההשחרה חסר, לא ניתן להשחיר.")
                else:
                    with st.spinner("מבצע השחרה פיזית (מלבנים שחורים)..."):
                        selected_findings = []
                        # אוסף אזורים מהטבלה
                        if findings:
                            selected_findings.extend([findings[i] for i in selected_indices])
                        
                        # אוסף מלבנים שצוירו בעכבר (שחורים בלבד)
                        for page_num, c_res in canvas_results:
                            if c_res is not None and c_res.json_data is not None:
                                for obj in c_res.json_data.get("objects", []):
                                    if obj.get("type") == "rect" and obj.get("fill") == "rgba(0, 0, 0, 1)":
                                        x0 = obj["left"]
                                        y0 = obj["top"]
                                        x1 = x0 + obj["width"] * obj["scaleX"]
                                        y1 = y0 + obj["height"] * obj["scaleY"]
                                        
                                        # התמונה רונדרה בגודל פי 1.2, אז מחלקים ב-1.2 כדי לקבל את הקואורדינטות המקוריות ב-PDF
                                        scale_factor = 1.2
                                        selected_findings.append({
                                            "page": page_num,
                                            "rect": [x0/scale_factor, y0/scale_factor, x1/scale_factor, y1/scale_factor]
                                        })
                        
                        if not selected_findings:
                            st.warning("לא סומנו אזורים להשחרה.")
                        else:
                            redactor = PdfRedactor()
                            redacted_bytes = redactor.redact_pdf_by_coords(st.session_state["pdf_bytes"], selected_findings)
                            
                            if redacted_bytes:
                                # שומר ב-Session State כדי לא לאבד ב-Rerun!
                                st.session_state["ready_for_download"] = True
                                st.session_state["redacted_bytes_to_download"] = redacted_bytes
                                st.rerun()
                            else:
                                st.error("❌ שגיאה ביצירת הFile המושחר.")
            
            # כפתור ההורדה מוצג באופן עצמאי באמצעות HTML ישיר לעקיפת הבאג של Streamlit
            if st.session_state.get("ready_for_download") and st.session_state.get("redacted_bytes_to_download"):
                st.success("✅ ההשחרה הושלמה בהצלחה!")
                
                # המרה ל-Base64 ויצירת כפתור HTML טהור כמו בתוסף הדפדפן
                import base64
                b64 = base64.b64encode(st.session_state["redacted_bytes_to_download"]).decode()
                href = f'''
                <a href="data:application/octet-stream;base64,{b64}" download="redacted_document.pdf" 
                   style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #6c63ff; 
                          border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #5a52d5;">
                   ⬇️ הורד PDF מושחר (הורדה ישירה)
                </a>
                <br><br>
                '''
                st.markdown(href, unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
