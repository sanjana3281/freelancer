# # ai_assist/utils_resume_text.py
# import os, io
# import fitz  # PyMuPDF (for PDFs)
# from PIL import Image
# # import pytesseract
# import docx2txt

# # If needed, hardcode Tesseract path (uncomment and set your path)
# # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}

# def _pdf_text_with_ocr(pdf_path: str, dpi: int = 220) -> str:
#     """Try native PDF text, else OCR each page."""
#     doc = fitz.open(pdf_path)

#     # 1) Native text
#     native = []
#     for page in doc:
#         t = page.get_text("text") or ""
#         if t.strip():
#             native.append(t)
#     if native:
#         return "\n".join(native).strip()

#     # 2) OCR fallback
#     chunks = []
#     for page in doc:
#         pix = page.get_pixmap(dpi=dpi)
#         img = Image.open(io.BytesIO(pix.tobytes("png")))
#         chunks.append(pytesseract.image_to_string(img))
#     return "\n".join(chunks).strip()

# def _image_ocr(path: str) -> str:
#     """OCR a single image file (png/jpg/jpeg/tiff…)."""
#     img = Image.open(path)
#     return pytesseract.image_to_string(img).strip()

# def extract_resume_text(path: str) -> str:
#     ext = os.path.splitext(path)[1].lower()
#     try:
#         if ext == ".pdf":
#             return _pdf_text_with_ocr(path)
#         if ext == ".docx":
#             return (docx2txt.process(path) or "").strip()
#         if ext == ".txt":
#             with open(path, "r", encoding="utf-8", errors="ignore") as f:
#                 return f.read().strip()
#         if ext in IMG_EXTS:
#             return _image_ocr(path)
#     except Exception as e:
#         return f"[error extracting text: {e}]"
#     return ""
