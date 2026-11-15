#OCR file pdf
def extract_text_from_pdf(pdf_bytes) -> str:
    """OCR toàn bộ file PDF và trả về văn bản thô."""
    POPPLER_PATH = "D:/ProgramFile86/poppler-26.09.0/Library/bin"
    from pdf2image import convert_from_bytes
    from pdf2image.pdf2image import pdfinfo_from_bytes

    info = pdfinfo_from_bytes(pdf_bytes,
        poppler_path=POPPLER_PATH)
    total_pages = info["Pages"]

    print(f"PDF có {total_pages} trang")

    text = ""
    for page_num in range(1, total_pages + 1):
        print(f"OCR trang {page_num}/{total_pages}...")

        image = convert_from_bytes(
            pdf_bytes,
            first_page=page_num,
            last_page=page_num,
            poppler_path=POPPLER_PATH,
        )[0]
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = (
            r"D:\ProgramFile86\Tesseract\tesseract.exe"
        )

        page_text = pytesseract.image_to_string(image, lang="vie")

        text += f"\n===== TRANG {page_num} =====\n"
        text += page_text

    return text