# coding=utf-8
import sys

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

start_marker = '@trace_execution\ndef process_image_visual'
start_idx = code.find(start_marker)

end_marker = '# ────────────────────────────────────────────────────────────────────\n# TAB 1 — IMAGE'
end_idx = code.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Failed to find markers")
    sys.exit(1)

new_func = """@trace_execution
def process_image_visual(image_bytes: bytes, detector_engine, use_ai: bool, ai_pipeline_engine=None):
    \"\"\"
    מנתח תמונה, מחלץ קואורדינטות של PII ומייצר תצוגה מקדימה מסומנת.
    \"\"\"
    import io
    import numpy as np
    from PIL import Image, ImageDraw
    import fitz
    
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
        
    # הפעלת Tesseract
    data = pytesseract.image_to_data(img, lang='heb+eng', output_type=pytesseract.Output.DICT)
    
    words = []
    for i in range(len(data['text'])):
        txt = data['text'][i].strip()
        if txt:
            x = float(data['left'][i])
            y = float(data['top'][i])
            w = float(data['width'][i])
            h = float(data['height'][i])
            words.append((x, y, x + w, y + h, txt))
            
    findings = []
    
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

    # 1. SPATIAL LOGIC
    for word_data in words:
        w_text = word_data[4]
        w_rect = fitz.Rect(word_data[:4])
        
        label_type = None
        for lab, l_type in SPATIAL_LABELS.items():
            if lab in w_text or lab[::-1] in w_text:
                label_type = l_type
                break
        
        if label_type:
            search_area = w_rect + (-50, -60, 50, 10)
            for other_word in words:
                o_text = other_word[4]
                o_rect = fitz.Rect(other_word[:4])
                if o_rect.intersects(search_area) and o_text != w_text:
                    is_val = any(c.isdigit() for c in o_text) or any(0x0590 <= ord(c) <= 0x05FF for c in o_text)
                    if is_val and len(o_text) >= 2:
                        findings.append({
                            "rect": [o_rect.x0, o_rect.y0, o_rect.x1, o_rect.y1],
                            "text": o_text,
                            "type": label_type,
                            "score": 0.99,
                        })

    # 2. FULL TEXT LOGIC
    full_text = " ".join([w[4] for w in words])
    all_entities = []
    
    res = detector_engine.analyze_text(full_text)
    for match in res.get("matches", []):
        if match.confidence >= 0.3:
            all_entities.append({"text": match.text, "type": match.category, "score": match.confidence})
            
    if use_ai and ai_pipeline_engine:
        rep = ai_pipeline_engine.process_file(file_bytes=full_text.encode('utf-8', errors='ignore'), filename="dummy.txt")
        if rep.get("success") and "entities" in rep:
            for e in rep["entities"]:
                all_entities.append({"text": e.get("text", ""), "type": e.get("entity_type", "PII"), "score": e.get("score", 0.8)})
                
    # 3. MAP ENTITIES TO RECTS
    for e in all_entities:
        e_text = e["text"]
        if not e_text.strip(): continue
        for w in words:
            if e_text in w[4] or w[4] in e_text:
                if len(w[4]) >= 2:
                    findings.append({
                        "rect": [w[0], w[1], w[2], w[3]],
                        "text": e_text,
                        "type": e["type"],
                        "score": e["score"],
                    })

    # DEDUPLICATE
    unique_findings = []
    for f in findings:
        is_dup = False
        f_rect = fitz.Rect(f["rect"])
        for uf in unique_findings:
            if f["type"] == uf["type"] and fitz.Rect(uf["rect"]).intersects(f_rect):
                is_dup = True
                break
        if not is_dup:
            unique_findings.append(f)
            
    # RENDER
    draw = ImageDraw.Draw(img, "RGBA")
    for f in unique_findings:
        rect = f["rect"]
        draw.rectangle(
            [(rect[0], rect[1]), (rect[2], rect[3])],
            outline=(255, 0, 0, 255),
            fill=(255, 255, 0, 80),
            width=3
        )
        
    out_io = io.BytesIO()
    img.save(out_io, format="PNG")
    
    return unique_findings, out_io.getvalue()

"""

new_code = code[:start_idx] + new_func + code[end_idx:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_code)
print("SUCCESS!")
