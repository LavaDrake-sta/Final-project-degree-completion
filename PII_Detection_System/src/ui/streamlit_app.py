"""
ממשק משתמש - זיהוי מידע אישי רגיש
גרסה 3.1 — נושא כהה + כל האפשרויות בדף ראשי
"""

import logging
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# נתיב src
current_file = Path(__file__)
src_path = current_file.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from detectors.basic_detector import BasicPIIDetector, SensitivityLevel
    from processors.image_processor import ImageProcessor
    from processors.pdf_processor import PDFProcessor
    from processors.word_processor import WordProcessor
    from processors.Excel_Processor import ExcelProcessor
    from redactors.excel_redactor import ExcelRedactor
    from redactors.word_redactor import WordRedactor
    detector_available = True
    logging.info("Modules loaded OK")
except ImportError as e:
    detector_available = False
    logging.error(f"Import error: {e}")

st.set_page_config(
    page_title="זיהוי מידע אישי רגיש",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Rubik', sans-serif !important; }

/* ── HIDE default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1200px; }

/* ── HERO ── */
.hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #1e3a5f 100%);
    border-radius: 18px;
    padding: 2.2rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    border: 1px solid rgba(139,92,246,.35);
    box-shadow: 0 0 60px rgba(139,92,246,.12);
}
.hero h1 {
    margin: 0 0 .4rem;
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -.5px;
}
.hero p { margin: 0; color: #94a3b8; font-size: .95rem; }

/* ── CARDS ── */
.card {
    background: #1e2340;
    border-radius: 16px;
    padding: 1.4rem 1.4rem 1.6rem;
    border: 1px solid rgba(255,255,255,.07);
    margin-bottom: 1rem;
    transition: border-color .25s, box-shadow .25s;
}
.card:hover { border-color: rgba(139,92,246,.4); box-shadow: 0 6px 30px rgba(139,92,246,.12); }

.card-accent { height: 3px; border-radius: 3px; margin: -.2rem -.1rem 1.1rem; }
.acc-purple { background: linear-gradient(90deg,#8b5cf6,#a78bfa); }
.acc-cyan   { background: linear-gradient(90deg,#06b6d4,#67e8f9); }
.acc-red    { background: linear-gradient(90deg,#ef4444,#f87171); }
.acc-blue   { background: linear-gradient(90deg,#2563eb,#60a5fa); }

.card-head { display:flex; align-items:center; gap:.7rem; margin-bottom:1rem; }
.card-head .icon { font-size:1.6rem; line-height:1; }
.card-head h3 { margin:0; font-size:1rem; font-weight:600; color:#e2e8f0; }
.card-head p  { margin:0; font-size:.78rem; color:#64748b; }

/* ── DIVIDER ── */
.divider { border:none; border-top:1px solid rgba(255,255,255,.06); margin:1.2rem 0 1.6rem; }

/* ── Streamlit widget overrides ── */
div[data-testid="stFileUploader"] > div {
    border: 1.5px dashed rgba(139,92,246,.4) !important;
    border-radius: 12px !important;
    background: rgba(139,92,246,.04) !important;
}
div[data-testid="stFileUploader"] > div:hover {
    border-color: rgba(139,92,246,.75) !important;
    background: rgba(139,92,246,.08) !important;
}
textarea { border-radius: 10px !important; }
div[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 700 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg,#8b5cf6,#7c3aed) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: .9rem !important;
    padding: .5rem 1.4rem !important;
    width: 100%;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
}

/* expander */
details summary { font-size:.85rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────
if not detector_available:
    st.error("❌ שגיאה בטעינת המודולים. ודא שכל הקבצים נמצאים במקום הנכון.")
    st.stop()

# ── Processors ────────────────────────────────────────────────────────────
@st.cache_resource
def load_processors():
    return (BasicPIIDetector(), ImageProcessor(), PDFProcessor(), WordProcessor(), ExcelProcessor())

detector, image_proc, pdf_proc, word_proc, excel_proc = load_processors()
redactor_word = WordRedactor()
redactor_excel = ExcelRedactor()

# ── Helpers ───────────────────────────────────────────────────────────────
_ICONS = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'CRITICAL': '🔴'}
_HEB   = {'LOW': 'נמוכה', 'MEDIUM': 'בינונית', 'HIGH': 'גבוהה', 'CRITICAL': 'קריטית'}

def show_results(results):
    if not results or not results.get('matches'):
        st.success("✅ לא נמצא מידע רגיש")
        return

    sens  = results['overall_sensitivity'].name
    count = results['total_matches']
    icon  = _ICONS.get(sens, '⚪')

    msg = f"{icon} זוהו **{count}** פריטי מידע רגיש — חומרה: **{_HEB.get(sens, sens)}**"
    if sens == 'CRITICAL':  st.error(f"🚨 {msg}")
    elif sens == 'HIGH':    st.warning(f"⚠️ {msg}")
    else:                   st.info(f"ℹ️ {msg}")

    rows = [{'#': i,
             'מידע': m.text,
             'קטגוריה': m.category.replace('_',' ').title(),
             'חומרה': f"{_ICONS.get(m.sensitivity.name,'⚪')} {_HEB.get(m.sensitivity.name,'')}",
             'ודאות': f"{m.confidence:.0%}"}
            for i, m in enumerate(results['matches'], 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=220)

    c1, c2, c3 = st.columns(3)
    c1.metric("סה״כ ממצאים", count)
    c2.metric("קריטיים 🔴", sum(1 for m in results['matches'] if m.sensitivity==SensitivityLevel.CRITICAL))
    c3.metric("גבוהים 🟠",   sum(1 for m in results['matches'] if m.sensitivity==SensitivityLevel.HIGH))


# ══════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <h1>🔒 מערכת זיהוי מידע אישי רגיש</h1>
    <p>העלה כל קובץ — המערכת תחלץ טקסט ותזהה מידע רגיש אוטומטית</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# ROW 1 — TEXT  |  IMAGE
# ══════════════════════════════════════════════════════════════════════════
col_l, col_r = st.columns(2, gap="large")

# ────── TEXT ──────────────────────────────────────────────────────────────
with col_l:
    st.markdown("""
    <div class="card">
      <div class="card-accent acc-purple"></div>
      <div class="card-head">
        <span class="icon">📝</span>
        <div><h3>טקסט חופשי</h3><p>הכנס או הדבק טקסט לניתוח ישיר</p></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    samples = {
        "— בחר דוגמה —": "",
        "פרטים אישיים":  "שם: דוד לוי | ת.ז: 123456789 | טל: 052-1234567 | מייל: david@gmail.com",
        "מידע רפואי":    "חולה סוכרת סוג 2, מקבל טיפול פסיכולוגי שבועי, ביטוח בריאות פעיל.",
        "מידע פיננסי":   "משכורת: 12,000 ₪ | חוב: 50,000 ₪ | כרטיס: 4580-1234-5678-9012",
    }
    sel = st.selectbox("דוגמה מהירה:", list(samples.keys()), key="sel_text")
    txt = st.text_area("טקסט:", value=samples[sel], height=155,
                       placeholder="הקלד או הדבק כאן...", key="ta_text",
                       label_visibility="collapsed")
    if st.button("🔍 נתח טקסט", key="btn_text"):
        if txt.strip():
            with st.spinner("מנתח..."):
                show_results(detector.analyze_text(txt))
        else:
            st.warning("אנא הזן טקסט")

# ────── IMAGE ─────────────────────────────────────────────────────────────
with col_r:
    st.markdown("""
    <div class="card">
      <div class="card-accent acc-cyan"></div>
      <div class="card-head">
        <span class="icon">🖼️</span>
        <div><h3>תמונה / OCR</h3><p>JPG · PNG · BMP · TIFF — קריאת טקסט אוטומטית</p></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    img_file = st.file_uploader("Upload Image", type=['jpg','jpeg','png','bmp','tiff','tif'],
                                key="up_img", label_visibility="collapsed")
    if img_file:
        st.image(img_file, use_container_width=True)
        if st.button("🔍 נתח תמונה", key="btn_img"):
            with st.spinner("OCR..."):
                ocr = image_proc.extract_text_from_image(img_file.read(), img_file.name)
            if ocr['success'] and ocr['text'].strip():
                with st.expander("📝 טקסט שחולץ"):
                    st.code(ocr['text'][:600], language=None)
                with st.spinner("מזהה מידע..."):
                    show_results(detector.analyze_text(ocr['text']))
                st.caption(f"ודאות OCR: {ocr['confidence']:.1f}%  |  {len(ocr['text'])} תווים")
            else:
                st.warning("לא נמצא טקסט בתמונה")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# ROW 2 — PDF  |  WORD
# ══════════════════════════════════════════════════════════════════════════
col_p, col_w, col_e = st.columns(3, gap="large")

# ────── PDF ───────────────────────────────────────────────────────────────
with col_p:
    st.markdown("""
    <div class="card">
      <div class="card-accent acc-red"></div>
      <div class="card-head">
        <span class="icon">📄</span>
        <div><h3>קובץ PDF</h3><p>טקסט רגיל · PDF סרוק · תמונות מוטבעות</p></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    pdf_file = st.file_uploader("Upload PDF", type=['pdf'], key="up_pdf", label_visibility="collapsed")
    if pdf_file:
        st.caption(f"📁 {pdf_file.name}  |  {len(pdf_file.getvalue()):,} bytes")
        if st.button("🔍 נתח PDF", key="btn_pdf"):
            with st.spinner("מעבד PDF..."):
                res = pdf_proc.extract_text_from_pdf(pdf_file.getvalue(), pdf_file.name)
            if res['success']:
                parts = [f"{res['pages']} עמודים", f"{res['character_count']:,} תווים"]
                if res.get('ocr_pages', 0) > 0:
                    parts.append(f"OCR: {res['ocr_pages']} עמודים/תמונות")
                st.caption("  |  ".join(parts))
                if res['text'].strip():
                    with st.expander("📝 תצוגה מקדימה"):
                        st.code(res['text'][:800] + ("…" if len(res['text'])>800 else ""), language=None)
                    with st.spinner("מזהה מידע..."):
                        show_results(detector.analyze_text(res['text']))
                else:
                    st.warning("לא נמצא טקסט ב-PDF")
            else:
                st.error(f"שגיאה: {res.get('error','לא ידוע')}")

# ────── WORD ──────────────────────────────────────────────────────────────
with col_w:
    st.markdown("""
    <div class="card">
      <div class="card-accent acc-blue"></div>
      <div class="card-head">
        <span class="icon">📘</span>
        <div><h3>מסמך Word</h3><p>DOCX — פסקאות · טבלאות · כותרות</p></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    word_file = st.file_uploader("Upload Word", type=['docx'], key="up_word", label_visibility="collapsed")
    if word_file:
        st.caption(f"📁 {word_file.name}  |  {len(word_file.getvalue()):,} bytes")
        if st.button("🔍 נתח Word", key="btn_word"):
            with st.spinner("מעבד Word..."):
                res = word_proc.extract_text_from_word(word_file.getvalue(), word_file.name)
            if res['success']:
                parts = [f"{res['paragraphs']} פסקאות", f"{res['tables']} טבלאות",
                         f"{res['character_count']:,} תווים"]
                if res.get('has_images'):
                    parts.append(f"{res['image_count']} תמונות")
                st.caption("  |  ".join(parts))
                if res['text'].strip():
                    with st.expander("📝 תצוגה מקדימה"):
                        st.code(res['text'][:800] + ("…" if len(res['text'])>800 else ""), language=None)
                    with st.spinner("מזהה מידע..."):
                        pii_res = detector.analyze_text(res['text'])
                        show_results(pii_res)
                        
                    if pii_res and pii_res.get('matches'):
                        pii_texts = [m.text for m in pii_res['matches']]
                        with st.spinner("מייצר קובץ מושחר..."):
                            redacted_bytes = redactor_word.redact_word(word_file.getvalue(), pii_texts)
                            if redacted_bytes:
                                st.download_button(
                                    label="📥 הורד קובץ Word מושחר",
                                    data=redacted_bytes,
                                    file_name=f"redacted_{word_file.name}",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                else:
                    st.warning("לא נמצא טקסט במסמך")
            else:
                st.error(f"שגיאה: {res.get('error','לא ידוע')}")

# ────── EXCEL ─────────────────────────────────────────────────────────────
with col_e:
    st.markdown("""
    <div class="card">
      <div class="card-accent acc-purple"></div>
      <div class="card-head">
        <span class="icon">📊</span>
        <div><h3>קובץ Excel</h3><p>XLSX — גיליונות נתונים · טבלאות</p></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    excel_file = st.file_uploader("Upload Excel", type=['xlsx', 'xls'], key="up_excel", label_visibility="collapsed")
    if excel_file:
        st.caption(f"📁 {excel_file.name}  |  {len(excel_file.getvalue()):,} bytes")
        if st.button("🔍 נתח Excel", key="btn_excel"):
            with st.spinner("מעבד Excel..."):
                res = excel_proc.extract_text_from_excel(excel_file.getvalue(), excel_file.name)
            if res['success']:
                parts = [f"{res['sheet_count']} גיליונות", f"{res['character_count']:,} תווים"]
                st.caption("  |  ".join(parts))
                if res['text'].strip():
                    with st.expander("📝 תצוגה מקדימה"):
                        st.code(res['text'][:800] + ("…" if len(res['text'])>800 else ""), language=None)
                    with st.spinner("מזהה מידע..."):
                        pii_res = detector.analyze_text(res['text'])
                        show_results(pii_res)
                        
                    if pii_res and pii_res.get('matches'):
                        pii_texts = [m.text for m in pii_res['matches']]
                        with st.spinner("מייצר קובץ מושחר..."):
                            redacted_bytes = redactor_excel.redact_excel(excel_file.getvalue(), pii_texts)
                            if redacted_bytes:
                                st.download_button(
                                    label="📥 הורד קובץ Excel מושחר",
                                    data=redacted_bytes,
                                    file_name=f"redacted_{excel_file.name}",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                else:
                    st.warning("לא נמצא טקסט במסמך")
            else:
                st.error(f"שגיאה: {res.get('error','לא ידוע')}")


# ════════════════════ FOOTER ═══════════════════════════════════════════════
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#475569;font-size:.78rem;padding-bottom:1rem">
    🔒 מערכת זיהוי מידע אישי רגיש &nbsp;|&nbsp; פרויקט גמר &nbsp;|&nbsp; גרסה 3.1<br>
    <span style="font-size:.72rem">מיועדת לצורכי בדיקה ולמידה בלבד</span>
</div>
""", unsafe_allow_html=True)