import os
import tempfile
import fitz
from PIL import Image, ImageDraw
import io

try:
    from src.logger_config import get_logger, trace_execution
except ImportError:
    try:
        from logger_config import get_logger, trace_execution
    except ImportError:
        import logging
        def get_logger(name):
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)
        def trace_execution(func): return func

logger = get_logger("PII.PDFConverter")

@trace_execution
def convert_office_to_pdf(file_bytes: bytes, ext: str) -> bytes:
    """
    ממיר קובץ Word או Excel ל-PDF בעזרת Microsoft Office שמותקן במחשב.
    """
    import win32com.client
    import pythoncom

    # אתחול COM ל-thread הנוכחי
    pythoncom.CoInitialize()
    
    # שמירת הקובץ זמנית בפורמט המקורי
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_in:
        temp_in.write(file_bytes)
        in_path = temp_in.name

    out_path = in_path + ".pdf"
    app = None
    doc = None
    wb = None
    
    try:
        if ext.lower() in ("doc", "docx"):
            app = win32com.client.Dispatch("Word.Application")
            app.Visible = False
            doc = app.Documents.Open(in_path)
            doc.SaveAs(out_path, FileFormat=17) # 17 = wdFormatPDF
            doc.Close()
            
        elif ext.lower() in ("xls", "xlsx"):
            app = win32com.client.Dispatch("Excel.Application")
            app.Visible = False
            app.DisplayAlerts = False
            wb = app.Workbooks.Open(in_path)
            # הגדרה להדפסה כדי שכל עמודה תתאים לדף במידת האפשר
            for sheet in wb.Worksheets:
                try:
                    sheet.PageSetup.Zoom = False
                    sheet.PageSetup.FitToPagesWide = 1
                    sheet.PageSetup.FitToPagesTall = False
                except Exception as e:
                    logger.warning(f"Could not format sheet for PDF: {e}")
            wb.ExportAsFixedFormat(0, out_path) # 0 = xlTypePDF
            wb.Close(False)
            
        else:
            raise ValueError(f"Unsupported extension for PDF conversion: {ext}")
            
        with open(out_path, "rb") as f:
            pdf_bytes = f.read()
            
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error converting {ext} to PDF: {e}")
        raise e
        
    finally:
        if app:
            app.Quit()
        if os.path.exists(in_path):
            try:
                os.remove(in_path)
            except: pass
        if os.path.exists(out_path):
            try:
                os.remove(out_path)
            except: pass
        pythoncom.CoUninitialize()

@trace_execution
def get_highlighted_images_from_pdf(pdf_bytes: bytes, findings: list) -> list:
    """
    ממיר PDF לתמונות ומצייר מלבנים צהובים סביב הממצאים (findings).
    """
    images_bytes = []
    
    try:
        # פותחים את ה-PDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # חיפוש כל הממצאים בדף כדי למצוא קואורדינטות להדגשה
            rects_to_highlight = []
            for item in findings:
                text = item.get("text", "")
                if text:
                    # חיפוש מדויק של הטקסט
                    instances = page.search_for(text)
                    for inst in instances:
                        rects_to_highlight.append(inst)
            
            # המרת הדף לתמונה (פיקסמפ) עם רקע לבן כברירת מחדל
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False) # איכות כפולה
            img_data = pix.tobytes("png")
            
            # פתיחה ב-PIL כדי לצייר הדגשה
            pil_img = Image.open(io.BytesIO(img_data)).convert("RGBA")
            overlay = Image.new('RGBA', pil_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # צייר את כל הריבועים הצהובים השקופים (מרקר)
            # מכיוון שחולץ עם scale 2, נכפיל את הקואורדינטות ב-2
            for rect in rects_to_highlight:
                scaled_box = [rect.x0 * 2, rect.y0 * 2, rect.x1 * 2, rect.y1 * 2]
                # מלבן צהוב חצי שקוף עם מסגרת
                draw.rectangle(scaled_box, fill=(255, 255, 0, 100), outline=(255, 165, 0, 200), width=3)
                
            # שילוב הציור עם התמונה המקורית
            combined = Image.alpha_composite(pil_img, overlay)
            
            # שמירה חזרה לבייטים
            out_bio = io.BytesIO()
            combined.convert("RGB").save(out_bio, format="PNG")
            images_bytes.append(out_bio.getvalue())
            
    except Exception as e:
        logger.error(f"Error extracting highlighted images: {e}", exc_info=True)
        
    return images_bytes
