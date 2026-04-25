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
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# ─── Basic modules ────────────────────────────────────────────────
try:
    from detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from processors.image_processor import ImageProcessor
    from processors.pdf_processor import PDFProcessor
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
    "IL_ID":             "תעודת זהות ישראלית",
    "IL_PHONE":          "מספר טלפון ישראלי",
    "HEB_ADDRESS":       "כתובת בעברית",
    # כללי
    "PERSON":            "שם אדם",
    "EMAIL_ADDRESS":     "כתובת אימייל",
    "PHONE_NUMBER":      "מספר טלפון",
    "CREDIT_CARD":       "כרטיס אשראי",
    "IBAN_CODE":         "מספר IBAN (חשבון בנק)",
    "CRYPTO":            "ארנק קריפטו",
    "LOCATION":          "מיקום / כתובת",
    "DATE_TIME":         "תאריך / שעה",
    "NRP":               "לאום / דת / גזע",
    "MEDICAL_LICENSE":   "רישיון רפואי",
    "URL":               "כתובת אתר",
    "IP_ADDRESS":        "כתובת IP",
    "AGE":               "גיל",
    # אמריקאי
    "US_SSN":            "מזהה אמריקאי (SSN)",
    "US_PASSPORT":       "דרכון אמריקאי",
    "US_DRIVER_LICENSE": "רישיון נהיגה אמריקאי",
    "US_BANK_NUMBER":    "מספר חשבון בנק (US)",
    "US_ITIN":           "מזהה מס אמריקאי",
}

def translate_entity(entity_type: str) -> str:
    """מתרגם שם ישות מאנגלית לעברית"""
    return ENTITY_HEBREW.get(entity_type, entity_type)

# ─── cache: load engines once ────────────────────────────────────
@st.cache_resource(show_spinner="⏳ טוען מנועי AI... (רק בפעם הראשונה)")
def load_all_engines():
    detector       = BasicPIIDetector()
    image_proc     = ImageProcessor()
    pdf_proc       = PDFProcessor()
    ai_pipeline    = None
    ai_error       = None
    if AI_PIPELINE_AVAILABLE:
        try:
            ai_pipeline = PIIPipeline()
        except Exception as e:
            ai_error = str(e)
    return detector, image_proc, pdf_proc, ai_pipeline, ai_error

detector, image_processor, pdf_processor, ai_pipeline, _ai_error = load_all_engines()

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🔒 PII Detection")
    st.caption("פרויקט גמר 2024")
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

    st.success("✅ מנוע Regex") if True else None

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
st.write("העלה קובץ, ראה **תצוגה מקדימה** של הממצאים, ואז בחר מה להשחיר.")

if USE_AI and not ai_pipeline:
    st.warning("⚠️ מנוע AI לא זמין — עובד במצב Regex.")
    USE_AI = False

st.divider()

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def sensitivity_icon(name: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(name, "⚪")


def show_preview_and_redact(entities: list, file_bytes: bytes, filename: str, original_text: str = ""):
    """
    הצג טבלת תצוגה מקדימה של ממצאי PII עם checkbox לכל שורה.
    לאחר בחירה — לחצן השחרה שמוריד את הקובץ המושחר.
    """
    if not entities:
        st.success("✅ לא נמצא מידע רגיש — המסמך נקי!")
        return

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # ─── כותרת ─────────────────────────────────────────────────────
    st.subheader(f"🔍 נמצאו {len(entities)} ממצאים — בחר מה להשחיר")
    st.caption("סמן ✅ את הממצאים שברצונך להשחיר בקובץ הסופי, ואז לחץ 'בצע השחרה'.")

    # ─── טבלת בחירה ────────────────────────────────────────────────
    # כל ממצא מקבל checkbox מובנה דרך st.data_editor
    df = pd.DataFrame([{
        "השחר?":    True,
        "#":         i + 1,
        "טקסט":      e.get("text", ""),
        "סוג":       translate_entity(e.get("entity_type", e.get("category", ""))),
        "ודאות":     f"{e.get('score', e.get('confidence', 0)):.0%}",
        "רגישות":    e.get("sensitivity", ""),
    } for i, e in enumerate(entities)])

    edited_df = st.data_editor(
        df,
        column_config={
            "השחר?": st.column_config.CheckboxColumn("השחר?", default=True),
            "#":      st.column_config.NumberColumn("#", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        key=f"preview_{filename}"
    )

    # ─── סיכום בחירה ───────────────────────────────────────────────
    selected_texts = edited_df[edited_df["השחר?"] == True]["טקסט"].tolist()
    total_selected = len(selected_texts)

    col1, col2, col3 = st.columns(3)
    col1.metric("סה״כ ממצאים", len(entities))
    col2.metric("נבחרו להשחרה", total_selected)
    col3.metric("יישארו גלויים", len(entities) - total_selected)

    if total_selected == 0:
        st.info("לא נבחרו ממצאים להשחרה.")
        return

    # ─── כפתור השחרה ───────────────────────────────────────────────
    if not REDACTORS_AVAILABLE:
        st.error("❌ מנוע השחרה לא זמין — לא ניתן להפיק קובץ מושחר.")
        return

    if st.button(f"🖊️ בצע השחרה ({total_selected} פריטים)", type="primary", key=f"do_redact_{filename}"):
        with st.spinner("מבצע השחרה על הקובץ..."):
            redacted_bytes = None
            mime = "application/octet-stream"
            out_name = f"redacted_{filename}"

            try:
                if ext == "pdf":
                    redactor = PdfRedactor()
                    redacted_bytes = redactor.redact_pdf(file_bytes, selected_texts)
                    mime = "application/pdf"

                elif ext == "docx":
                    redactor = WordRedactor()
                    redacted_bytes = redactor.redact_word(file_bytes, selected_texts)
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

                elif ext == "xlsx":
                    redactor = ExcelRedactor()
                    redacted_bytes = redactor.redact_excel(file_bytes, selected_texts)
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                elif ext in ("jpg", "jpeg", "png", "bmp"):
                    redactor = ImageRedactor()
                    redacted_bytes = redactor.redact_image(file_bytes, selected_texts)
                    mime = "image/png"
                    out_name = f"redacted_{os.path.splitext(filename)[0]}.png"

                else:
                    st.error(f"❌ פורמט לא נתמך להשחרה: {ext}")

            except Exception as ex:
                st.error(f"❌ שגיאה בהשחרה: {ex}")

        if redacted_bytes:
            st.success(f"✅ השחרה הושלמה! {total_selected} פריטים הוסרו.")
            st.download_button(
                label=f"⬇️ הורד קובץ מושחר ({out_name})",
                data=redacted_bytes,
                file_name=out_name,
                mime=mime,
                type="primary"
            )
        elif redacted_bytes is None and ext in ("pdf", "docx", "xlsx", "jpg", "jpeg", "png", "bmp"):
            st.warning("⚠️ לא בוצעו השחרות — ייתכן שהטקסטים לא נמצאו בקובץ.")


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

# ────────────────────────────────────────────────────────────────────
# TAB 1 — תמונה
# ────────────────────────────────────────────────────────────────────
with tab_img:
    st.header("🖼️ ניתוח תמונה")
    st.caption("JPG, PNG, BMP — חילוץ טקסט OCR + זיהוי PII + תצוגה מקדימה + השחרה")

    if not TESSERACT_OK:
        st.warning("⚠️ Tesseract לא מותקן. הורד מ: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        uploaded = st.file_uploader("📂 בחר קובץ תמונה", type=["jpg", "jpeg", "png", "bmp"], key="img_up")
        if uploaded:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(uploaded, caption=uploaded.name, use_container_width=True)
            with col2:
                if st.button("🔍 נתח תמונה", key="btn_img", type="primary"):
                    with st.spinner("OCR + PII..."):
                        raw = uploaded.getvalue()
                        ocr = image_processor.extract_text_from_image(raw, uploaded.name)
                    if ocr["success"] and ocr["text"].strip():
                        st.info(f"📖 ודאות OCR: {ocr.get('confidence', 0):.1f}%")
                        with st.expander("📝 טקסט שחולץ"):
                            st.text(ocr["text"])
                        if USE_AI and ai_pipeline:
                            rep = ai_pipeline.process_file(file_bytes=raw, filename=uploaded.name)
                            if rep["success"]:
                                entities = ai_entities_to_preview(rep["entities"])
                        else:
                            res = detector.analyze_text(ocr["text"])
                            entities = basic_matches_to_preview(res["matches"])
                        st.session_state["img_entities"] = entities
                        st.session_state["img_bytes"]    = raw
                        st.session_state["img_name"]     = uploaded.name
                    elif not ocr.get("text", "").strip():
                        st.warning("⚠️ לא נמצא טקסט בתמונה")
                    else:
                        st.error(f"❌ שגיאה: {ocr.get('error')}")

            # תצוגה מקדימה + השחרה
            if "img_entities" in st.session_state and st.session_state.get("img_name") == uploaded.name:
                st.divider()
                show_preview_and_redact(
                    st.session_state["img_entities"],
                    st.session_state["img_bytes"],
                    st.session_state["img_name"]
                )

# ────────────────────────────────────────────────────────────────────
# TAB 2 — Word
# ────────────────────────────────────────────────────────────────────
with tab_word:
    st.header("📝 ניתוח מסמך Word")
    st.caption("DOCX — מחלץ טקסט כולל טבלאות + זיהוי PII + תצוגה מקדימה + השחרה")

    uploaded = st.file_uploader("📂 בחר קובץ Word", type=["docx"], key="word_up")
    if uploaded:
        st.info(f"📄 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        if st.button("🔍 נתח Word", key="btn_word", type="primary"):
            with st.spinner("מחלץ וניתוח..."):
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
                    import docx as _docx
                    doc = _docx.Document(io.BytesIO(raw))
                    text = "\n".join(p.text for p in doc.paragraphs)
                    res = detector.analyze_text(text)
                    entities = basic_matches_to_preview(res["matches"])

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
    st.header("📊 ניתוח קובץ Excel")
    st.caption("XLSX — סריקת כל הגיליונות + זיהוי PII + תצוגה מקדימה + השחרה")

    uploaded = st.file_uploader("📂 בחר קובץ Excel", type=["xlsx"], key="excel_up")
    if uploaded:
        st.info(f"📊 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        if st.button("🔍 נתח Excel", key="btn_excel", type="primary"):
            with st.spinner("קורא גיליונות..."):
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
                    import openpyxl as _xl
                    wb = _xl.load_workbook(io.BytesIO(raw), data_only=True)
                    lines = []
                    for ws in wb.worksheets:
                        for row in ws.iter_rows(values_only=True):
                            t = " ".join(str(c) for c in row if c is not None)
                            if t.strip():
                                lines.append(t)
                    text = "\n".join(lines)
                    res = detector.analyze_text(text)
                    entities = basic_matches_to_preview(res["matches"])

            if text:
                with st.expander("📝 תוכן הקובץ"):
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
# TAB 4 — PDF
# ────────────────────────────────────────────────────────────────────
with tab_pdf:
    st.header("📄 ניתוח קובץ PDF")
    st.caption("PDF רגיל וסרוק + זיהוי PII + תצוגה מקדימה + השחרה")

    uploaded = st.file_uploader("📂 בחר קובץ PDF", type=["pdf"], key="pdf_up")
    if uploaded:
        st.info(f"📄 **{uploaded.name}** | {uploaded.size / 1024:.1f} KB")
        if st.button("🔍 נתח PDF", key="btn_pdf", type="primary"):
            with st.spinner("מעבד PDF..."):
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
                    pdf_result = pdf_processor.extract_text_from_pdf(raw, uploaded.name)
                    if pdf_result["success"]:
                        text = pdf_result["text"]
                        pages = pdf_result.get("pages", "?")
                        is_scanned = pdf_result.get("is_scanned", False)
                        st.success(f"✅ {pages} עמודים" + (" | OCR" if is_scanned else ""))
                        res = detector.analyze_text(text)
                        entities = basic_matches_to_preview(res["matches"])
                    else:
                        st.error(f"❌ {pdf_result.get('error')}")
                        entities = []
                        text = ""

            if text:
                with st.expander("📝 תוכן ה-PDF"):
                    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
            st.session_state["pdf_entities"] = entities
            st.session_state["pdf_bytes"]    = raw
            st.session_state["pdf_name"]     = uploaded.name

        if "pdf_entities" in st.session_state and st.session_state.get("pdf_name") == uploaded.name:
            st.divider()
            show_preview_and_redact(
                st.session_state["pdf_entities"],
                st.session_state["pdf_bytes"],
                st.session_state["pdf_name"]
            )

# ────────────────────────────────────────────────────────────────────
# TAB 5 — AI Pipeline (כל פורמט)
# ────────────────────────────────────────────────────────────────────
with tab_ai:
    st.header("🤖 ניתוח AI מלא (Presidio)")
    st.write("העלה **כל סוג קובץ** — AI מלא + תצוגה מקדימה + השחרה.")

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
            "📂 בחר קובץ לניתוח AI",
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
                        f"{icons.get(risk_level,'')} רמת סיכון: **{risk_level}** | {ev['summary']}"
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
