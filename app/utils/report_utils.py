import re
def clean_report_text(text):
    # Loại bỏ Markdown
    text = re.sub(r'\*\*|__|~~|==', '', text)
    # Loại bỏ ký tự escape không cần thiết
    text = text.replace('\\', '')
    # Chỉ giữ nội dung từ mục 1 đến hết mục 4
    match = re.search(
        r'1\.\s.*?(?=\n\s*5\.\s|\Z)',
        text,
        flags=re.DOTALL
    )
    if match:
        text = match.group(0)

    # Loại bỏ dấu gạch đầu dòng ở đầu mỗi dòng
    text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.MULTILINE)
    # Chuẩn hóa khoảng trắng
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()