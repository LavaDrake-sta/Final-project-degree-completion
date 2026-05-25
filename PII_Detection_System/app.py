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
sys.path.insert(0, os.path.join(base_dir, 'src'))
try:
    from src.logger_config import get_logger, trace_execution, log_progress
except ImportError:
    try:
        from logger_config import get_logger, trace_execution, log_progress
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
    from detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from processors.image_processor import ImageProcessor
    from processors.pdf_processor import PDFProcessor
    from processors.word_processor import WordProcessor
    from processors.Excel_Processor import ExcelProcessor
except ImportError as e:
    st.error(f"❌ שגיאת ייבוא: {e}")
    st.stop()

# ─── AI Pipeline ─────────────────────────────────────────────────
AI_PIPELINE_AVAILABLE = False
try:
    from pipeline import PIIPipeline
    AI_PIPELINE_AVAILABLE = True
except ImportError:
    pass

# ─── Redactors ───────────────────────────────────────────────────
REDACTORS_AVAILABLE = False
try:
    from redactors import PdfRedactor, WordRedactor, ExcelRedactor, ImageRedactor
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
    return ENTITY_HEBREW.get(entity_type, entity_type)

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

@st.cache_resource(show_spinner="⏳ טוען מנוע זיהוי תמונות (OCR), ייתכן שייקח מעט זמן בפעם הראשונה...")
@trace_execution
def load_ocr_engine():
    try:
        import easyocr
        # False for GPU since we are assuming standard local deployment without CUDA setup
        return easyocr.Reader(['he', 'en'], gpu=False)
    except Exception as e:
        print(f"EasyOCR Error: {e}")
        return None

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
def show_preview_and_redact(entities: list, file_bytes: bytes, filename: str, original_text: str = ""):
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
        key=f"preview_{filename}"
    )

    # ─── סיכום בחירה ───────────────────────────────────────────────
    selected_texts = edited_df[edited_df["השחר?"] == True]["טקסט"].tolist()
    total_selected = len(selected_texts)

    col1, col2, col3 = st.columns(3)
    col1.metric("סה״כ findings", len(entities))
    col2.metric("נבחרו להשחרה", total_selected)
    col3.metric("יישארו גלויים", len(entities) - total_selected)

    if total_selected == 0:
        st.info("לא נבחרו findings להשחרה.")
        return

    # ─── כפתור השחרה ───────────────────────────────────────────────
    if not REDACTORS_AVAILABLE:
        st.error("❌ מנוע השחרה לא זמין — לא ניתן להפיק File מושחר.")
        return

    # ─── מפתח session_state ייחודי לכל קובץ ────────────────────────
    dl_key = f"redact_result_{filename}"

    if st.button(f"🖊️ בצע השחרה ({total_selected} פריטים)", type="primary", key=f"do_redact_{filename}"):
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
            key=f"dl_btn_{filename}",
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
tab_img, tab_word, tab_excel, tab_pdf, tab_ai = st.tabs([
    "🖼️  תמונה",
    "📝  Word",
    "📊  Excel",
    "📄  PDF",
    "🤖  AI Pipeline"
])

@trace_execution
def process_image_visual(image_bytes: bytes, detector_engine, use_ai: bool, ai_pipeline_engine=None):
    """
    מנתח תמונה, מחלץ קואורדינטות של PII ומייצר תצוגה מקדימה מסומנת.
    """
    import io
    import numpy as np
    from PIL import Image, ImageDraw
    
    ocr_engine = load_ocr_engine()
    if not ocr_engine:
        return [], image_bytes
        
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    ocr_results = ocr_engine.readtext(img_array)
    
    findings = []
    # יצירת עותק לציור
    draw_img = img.convert("RGBA")
    overlay = Image.new("RGBA", draw_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    for bbox, snippet_text, conf in ocr_results:
        if not snippet_text.strip(): continue
        
        snippet_findings = []
        if use_ai and ai_pipeline_engine:
            rep = ai_pipeline_engine.process_file(file_bytes=snippet_text.encode('utf-8', errors='ignore'), filename="dummy.txt")
            if rep.get("success") and "entities" in rep:
                snippet_findings = rep["entities"]
        else:
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
            
            # ציור על ה-Overlay
            draw.rectangle(rect, fill=(255, 255, 0, 80), outline=(255, 0, 0, 200), width=2)
            
            for sf in snippet_findings:
                findings.append({
                    "rect": rect,
                    "text": sf.get("text", snippet_text),
                    "type": sf.get("entity_type", sf.get("type", "PII")),
                    "score": sf.get("score", conf),
                })
    
    # איחוד התמונה עם ה-Overlay
    final_img = Image.alpha_composite(draw_img, overlay).convert("RGB")
    
    # המרה חזרה ל-bytes
    img_byte_arr = io.BytesIO()
    final_img.save(img_byte_arr, format='PNG')
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
                col1, col2 = st.columns([1.2, 1])
                
                with col1:
                    st.subheader("👀 תצוגה מקדימה")
                    st.image(st.session_state["img_visual_preview"], use_container_width=True)
                
                with col2:
                    st.subheader("📋 findings")
                    entities = st.session_state["img_visual_findings"]
                    if entities:
                        show_preview_and_redact(
                            entities,
                            st.session_state["img_bytes"],
                            st.session_state["img_name"]
                        )
                    else:
                        st.success("✅ לא נמצא מידע רגיש בתמונה.")

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
                        text = rep.get("anonymized_text", "")
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

            if text:
                with st.expander("📝 תוכן המסמך"):
                    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
            st.session_state["word_entities"] = entities
            st.session_state["word_bytes"]    = raw
            st.session_state["word_name"]     = uploaded.name

        if "word_entities" in st.session_state and st.session_state.get("word_name") == uploaded.name:
            st.divider()
            show_preview_and_redact(
                st.session_state["word_entities"],
                st.session_state["word_bytes"],
                st.session_state["word_name"]
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
                        text = rep.get("anonymized_text", "")
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

            if text:
                with st.expander("📝 תוכן הFile"):
                    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
            st.session_state["excel_entities"] = entities
            st.session_state["excel_bytes"]    = raw
            st.session_state["excel_name"]     = uploaded.name

        if "excel_entities" in st.session_state and st.session_state.get("excel_name") == uploaded.name:
            st.divider()
            show_preview_and_redact(
                st.session_state["excel_entities"],
                st.session_state["excel_bytes"],
                st.session_state["excel_name"]
            )

# ────────────────────────────────────────────────────────────────────
@trace_execution
def process_pdf_visual(file_bytes: bytes, detector_engine, use_ai: bool, ai_pipeline_engine=None, force_ocr: bool = False):
    """
    סורק PDF Page עמוד, מחלץ קואורדינטות של מידע רגיש,
    ומייצר תמונות של העמודים עם סימוני השחרה ויזואליים.
    כולל לוגיקה מרחבית (Spatial) לקישור כותרות לערכים.
    """
    import fitz
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    findings = []
    page_images = []
    
    # מילות מפתח לחיפוש מרחבי (כותרת -> סוג ישות)
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
        words = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)
        
        page_findings = []
        
        # זיהוי אם להשתמש ב-OCR: אם המשתמש ביקש, או אם אין כמעט טקסט
        # גם אם יש טקסט, בדוק אם הוא קריא (לא mojibake עברי)
        readable_chars = sum(1 for c in text if c.isascii() and c.isprintable() or 0x0590 <= ord(c) <= 0x05FF or c.isdigit())
        text_is_readable = readable_chars > 30
        should_ocr = force_ocr or len(text.strip()) < 50 or not text_is_readable
        
        ocr_engine = load_ocr_engine() if should_ocr else None
        
        if should_ocr and ocr_engine:
            if ocr_engine:
                import io
                import numpy as np
                from PIL import Image
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                img = Image.open(io.BytesIO(pix.tobytes()))
                img_array = np.array(img)
                ocr_results = ocr_engine.readtext(img_array)
                
                for bbox, snippet_text, conf in ocr_results:
                    if not snippet_text.strip(): continue
                    
                    snippet_findings = []
                    if use_ai and ai_pipeline_engine:
                        rep = ai_pipeline_engine.process_file(file_bytes=snippet_text.encode('utf-8', errors='ignore'), filename="dummy.txt")
                        if rep.get("success") and "entities" in rep:
                            snippet_findings = rep["entities"]
                    else:
                        res = detector_engine.analyze_text(snippet_text)
                        for match in res.get("matches", []):
                            if match.confidence >= 0.3:
                                snippet_findings.append({
                                    "text": match.text,
                                    "entity_type": match.category,
                                    "score": match.confidence,
                                })
                                
                    x_coords = [p[0]/2.0 for p in bbox]
                    y_coords = [p[1]/2.0 for p in bbox]
                    rect = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    
                    for sf in snippet_findings:
                        page_findings.append({
                            "page": page_num,
                            "rect": rect,
                            "text": sf.get("text", snippet_text),
                            "type": sf.get("entity_type", sf.get("type", "PII")),
                            "score": sf.get("score", conf),
                            "id": f"ocr_{page_num}_{rect[0]}_{rect[1]}"
                        })
        else:
            # לוגיקה מרחבית (Spatial) - חיפוש כותרות וערכים קרובים
            # words כבר נטען למעלה
            
            # 1. איתור כותרות
            for word_data in words:
                w_text = word_data[4]
                w_rect = fitz.Rect(word_data[:4])
                
                label_type = None
                for lab, l_type in SPATIAL_LABELS.items():
                    if lab in w_text or lab[::-1] in w_text:
                        label_type = l_type
                        break
                
                if label_type:
                    # מצאנו כותרת! נחפש מספרים/שמות מעליה או לידה
                    # נחפש ברדיוס של 50 פיקסלים
                    search_area = w_rect + (-50, -60, 50, 10) # חיפוש בעיקר מעל
                    for other_word in words:
                        o_text = other_word[4]
                        o_rect = fitz.Rect(other_word[:4])
                        if o_rect.intersects(search_area) and o_text != w_text:
                            # אם זה נראה כמו ערך (מספר או טקסט עברי)
                            is_val = any(c.isdigit() for c in o_text) or any(0x0590 <= ord(c) <= 0x05FF for c in o_text)
                            if is_val and len(o_text) >= 2:
                                page_findings.append({
                                    "page": page_num,
                                    "rect": [o_rect.x0, o_rect.y0, o_rect.x1, o_rect.y1],
                                    "text": o_text,
                                    "type": label_type,
                                    "score": 0.99, # ודאות גבוהה בגלל ההקשר המרחבי
                                    "id": f"spatial_{page_num}_{o_rect.x0}_{o_rect.y0}"
                                })

            # 2. זיהוי רגיל (NLP/Regex) על כל הטקסט
            if use_ai and ai_pipeline_engine:
                rep = ai_pipeline_engine.process_file(file_bytes=text.encode('utf-8', errors='ignore'), filename="dummy.txt")
                if rep.get("success") and "entities" in rep:
                    for e in rep["entities"]:
                        entity_text = e.get("text", "")
                        if not entity_text.strip(): continue
                        
                        # חיפוש קואורדינטות (כולל חיפוש הפוך לעברית)
                        search_texts = [entity_text]
                        if any(0x0590 <= ord(c) <= 0x05FF for c in entity_text):
                            search_texts.append(entity_text[::-1])
                            
                        for s_text in search_texts:
                            for area in page.search_for(s_text):
                                page_findings.append({
                                    "page": page_num,
                                    "rect": [area.x0, area.y0, area.x1, area.y1],
                                    "text": entity_text,
                                    "type": e.get("entity_type", "PII"),
                                    "score": e.get("score", 0.8),
                                    "id": f"{page_num}_{area.x0}_{area.y0}"
                                })
            else:
                # --- שיטה 1: זיהוי על הטקסט המלא ---
                all_matches = []
                
                # זיהוי על הטקסט כמו שהוא (word-scan יטפל בHTF RTL)
                res = detector_engine.analyze_text(text)
                all_matches.extend(res.get("matches", []))
                
                # --- שיטה 2: זיהוי מילה-מילה (גיבוי לPDF עם encoding שבור) ---
                # מאחד מילים סמוכות לקבוצות של עד 5 מילים ומריץ detection
                word_texts_with_rects = []
                for i in range(len(words)):
                    # אוסף חלונות של מילים (1 עד 5)
                    for window in range(1, 6):
                        if i + window > len(words):
                            break
                        chunk_words = words[i:i+window]
                        chunk_text = " ".join(w[4] for w in chunk_words)
                        chunk_rect = fitz.Rect(chunk_words[0][:4])
                        for w in chunk_words[1:]:
                            chunk_rect |= fitz.Rect(w[:4])
                        word_texts_with_rects.append((chunk_text, chunk_rect))
                
                # הרצת זיהוי על כל חלון מילים
                seen_word_matches = set()
                for chunk_text, chunk_rect in word_texts_with_rects:
                    chunk_res = detector_engine.analyze_text(chunk_text)
                    for match in chunk_res.get("matches", []):
                        if match.confidence >= 0.4 and match.text not in seen_word_matches:
                            seen_word_matches.add(match.text)
                            page_findings.append({
                                "page": page_num,
                                "rect": [chunk_rect.x0, chunk_rect.y0, chunk_rect.x1, chunk_rect.y1],
                                "text": match.text,
                                "type": match.category,
                                "score": match.confidence,
                                "id": f"{page_num}_{chunk_rect.x0}_{chunk_rect.y0}_{match.category}_word"
                            })
                
                # --- עיבוד תוצאות שיטה 1 + מציאת קואורדינטות ---
                seen_fulltext = set()
                for match in all_matches:
                    if match.confidence < 0.4:
                        continue
                    entity_text = match.text
                    if entity_text in seen_fulltext:
                        continue
                    seen_fulltext.add(entity_text)
                    
                    # אם כבר נמצא דרך word scan, דלג
                    if entity_text in seen_word_matches:
                        continue
                    
                    search_texts = [entity_text]
                    if any(0x0590 <= ord(c) <= 0x05FF for c in entity_text):
                        search_texts.append(entity_text[::-1])
                        
                    found_any = False
                    for s_text in search_texts:
                        found_areas = page.search_for(s_text)
                        if found_areas:
                            found_any = True
                            for area in found_areas:
                                page_findings.append({
                                    "page": page_num,
                                    "rect": [area.x0, area.y0, area.x1, area.y1],
                                    "text": entity_text,
                                    "type": match.category,
                                    "score": match.confidence,
                                    "id": f"{page_num}_{area.x0}_{area.y0}_{match.category}"
                                })
                    
                    # Fallback: word-window search
                    if not found_any:
                        clean_target = "".join(entity_text.split())
                        for i in range(len(words)):
                            combined = ""
                            rect = None
                            for j in range(i, min(i + 8, len(words))):
                                w_text = "".join(words[j][4].split())
                                combined += w_text
                                w_rect = fitz.Rect(words[j][:4])
                                if rect is None:
                                    rect = w_rect
                                else:
                                    rect |= w_rect
                                if clean_target in combined or clean_target[::-1] in combined:
                                    if len(combined) <= len(clean_target) + 6:
                                        page_findings.append({
                                            "page": page_num,
                                            "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                                            "text": entity_text,
                                            "type": match.category,
                                            "score": match.confidence,
                                            "id": f"{page_num}_{rect.x0}_{rect.y0}_{match.category}_fb"
                                        })
                                    break
                        
        # סינון כפילויות בPage הנוכחי — לפי מיקום ולפי טקסט
        unique_page_findings = []
        seen_positions = set()
        seen_texts = set()
        for f in page_findings:
            pos_key = (round(f["rect"][0]/2)*2, round(f["rect"][1]/2)*2)
            text_key = f["text"].strip()
            # דלג אם כבר נמצא באותו מיקום, או אם אותו טקסט כבר קיים עם ציון גבוה יותר
            if pos_key not in seen_positions and text_key not in seen_texts:
                seen_positions.add(pos_key)
                seen_texts.add(text_key)
                unique_page_findings.append(f)
                
        findings.extend(unique_page_findings)
        
        # יצירת תמונה של הPage עם המלבנים מסומנים
        temp_doc = fitz.open(stream=file_bytes, filetype="pdf")
        temp_page = temp_doc[page_num]
        for f in unique_page_findings:
            # ציור מלבן צהוב בולט עם מסגרת אדומה
            temp_page.draw_rect(fitz.Rect(*f["rect"]), color=(1, 0, 0), width=1.5, fill_opacity=0.3, fill=(1, 1, 0))
            # הוספת תגית סוג מעל (אופציונלי, בדרך כלל מפריע אז נוותר)
            
        pix = temp_page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)) 
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
        
        # אפשרות ל-OCR כפוי (High Accuracy)
        force_ocr = st.checkbox("🔍 **מצב דיוק גבוה (OCR)** - השתמש בזה אם הטקסט במסמך נראה משובש", value=False)
        
        if st.button("🔍 נתח PDF (מצב ויזואלי)", key="btn_pdf", type="primary"):
            with st.spinner("סורק מסמך, מאתר קואורדינטות ומרנדר pages..."):
                raw = uploaded.getvalue()
                findings, images = process_pdf_visual(raw, detector, USE_AI, ai_pipeline, force_ocr=force_ocr)
                
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
            
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.markdown("**רשימת findings אוטומטיים:**")
                if not findings:
                    st.info("לא זוהו אוטומטית ממצאים להשחרה. באפשרותך להוסיף טקסט להשחרה ידנית או לצייר מלבנים.")
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
                selected_indices = edited_df[edited_df["השחר?"] == True].index.tolist()
                
                # אם נוספו שורות ידניות, נוסיף אותן למערך הממצאים הכולל כדי שיעברו להשחרה הפיזית
                for idx in selected_indices:
                    if idx >= len(findings):
                        # זו שורה ידנית שהמשתמש הוסיף!
                        row = edited_df.loc[idx]
                        if row["טקסט"]:
                            findings.append({
                                "text": row["טקסט"],
                                "type": "MANUAL",
                                "page": row.get("עמוד", 1) - 1 if pd.notna(row.get("עמוד")) else 0
                            })

            with col2:
                st.markdown("**תצוגת המסמך (צייר מלבנים להשחרה):**")
                st.warning("⚠️ **שים לב:** אל תשתמש בכפתור ההורדה הקטן שבתוך התמונה. בסיום הציור, לחץ על 'בצע השחרה מדויקת' למטה!")
                from streamlit_drawable_canvas import st_canvas
                from PIL import Image
                import io
                
                canvas_results = []
                for page_num, img_bytes in enumerate(images):
                    st.write(f"**Page {page_num + 1}**")
                    bg_image = Image.open(io.BytesIO(img_bytes))
                    
                    canvas_res = st_canvas(
                        fill_color="rgba(0, 0, 0, 1)",  # מילוי שחור לסימון
                        stroke_width=2,
                        stroke_color="rgba(255, 0, 0, 1)", # מסגרת אדומה
                        background_image=bg_image,
                        update_streamlit=True,
                        height=bg_image.height,
                        width=bg_image.width,
                        drawing_mode="rect",
                        display_toolbar=False,  # הסרת הסרגל כדי למנוע הורדה שגויה
                        key=f"canvas_{uploaded.name}_{page_num}",
                    )
                    canvas_results.append((page_num, canvas_res))

            st.markdown("---")
            if st.button(f"🖊️ בצע השחרה מדויקת", type="primary"):
                if not REDACTORS_AVAILABLE:
                    st.error("❌ מנוע ההשחרה חסר, לא ניתן להשחיר.")
                else:
                    with st.spinner("מבצע השחרה פיזית (מלבנים שחורים)..."):
                        selected_findings = []
                        # אוסף אזורים מהטבלה
                        if findings:
                            selected_findings.extend([findings[i] for i in selected_indices])
                        
                        # אוסף מלבנים שצוירו בעכבר
                        for page_num, c_res in canvas_results:
                            if c_res is not None and c_res.json_data is not None:
                                for obj in c_res.json_data.get("objects", []):
                                    if obj.get("type") == "rect":
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
                                st.experimental_rerun()
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
# TAB 5 — AI Pipeline (כל פורמט)
# ────────────────────────────────────────────────────────────────────
with tab_ai:
    st.header("🤖 ניתוח AI מלא (Presidio)")
    st.write("העלה **כל סוג File** — AI מלא + תצוגה מקדימה + השחרה.")

    if not AI_PIPELINE_AVAILABLE:
        st.error("❌ Presidio לא מותקן.")
    elif ai_pipeline is None:
        st.error("❌ מנוע AI לא עלה.")
        if _ai_error:
            st.code(_ai_error)
        if st.button("🔄 נסה שוב"):
            st.cache_resource.clear()
            st.rerun()
    else:
        st.success("✅ Presidio + spaCy en_core_web_lg פעיל")

        uploaded = st.file_uploader(
            "📂 בחר File לניתוח AI",
            type=["pdf", "docx", "xlsx", "jpg", "jpeg", "png", "bmp"],
            key="ai_up"
        )

        if uploaded:
            ext = uploaded.name.rsplit(".", 1)[-1].upper()
            st.info(f"📁 **{uploaded.name}** | {ext} | {uploaded.size / 1024:.1f} KB")

            if st.button("🚀 נתח עם AI", key="btn_ai", type="primary"):
                with st.spinner("🤖 Presidio + spaCy מנתחים..."):
                    raw = uploaded.getvalue()
                    rep = ai_pipeline.process_file(file_bytes=raw, filename=uploaded.name)

                if rep["success"]:
                    # הצג סיכום סיכון
                    ev = rep["risk_evaluation"]
                    risk_level = ev["risk_level"]
                    icons = {"SAFE": "🛡️", "WARNING": "⚠️", "UNSAFE": "🚨"}
                    alerts = {"SAFE": st.success, "WARNING": st.warning, "UNSAFE": st.error}
                    alerts.get(risk_level, st.info)(
                        f"{icons.get(risk_level,'')} Risk level: **{risk_level}** | {ev['summary']}"
                    )

                    with st.expander("📝 טקסט מצונזר"):
                        st.text(rep.get("anonymized_text", ""))

                    entities = ai_entities_to_preview(rep["entities"])
                    st.session_state["ai_entities"] = entities
                    st.session_state["ai_bytes"]    = raw
                    st.session_state["ai_name"]     = uploaded.name
                else:
                    st.error(f"❌ {rep.get('error')}")

            if "ai_entities" in st.session_state and st.session_state.get("ai_name") == uploaded.name:
                st.divider()
                show_preview_and_redact(
                    st.session_state["ai_entities"],
                    st.session_state["ai_bytes"],
                    st.session_state["ai_name"]
                )
