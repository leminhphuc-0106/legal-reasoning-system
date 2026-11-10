import re
# from pprint import pprint

ARTICLE_RE = re.compile(
    r"^\s*Điều\s+(\d+)\.\s*(.*)$",
    re.IGNORECASE
)

CLAUSE_RE = re.compile(
    r"^\s*(\d+)\.\s+(.+)$"
)

POINT_RE = re.compile(
    r"(?<!\w)([a-zđ])\)\s*",
    re.IGNORECASE
)

#Hàm chunking theo cấu trúc
def structure_base_chunk(text):
    import re
    pattern = r'(?m)^\s*Điều\s+\d+\.\s*.*$'
    #Chứa vị trí tìm được "Điều"
    matches = list(re.finditer(pattern, text))

    articles = []
    text_after_extraction = ""
    for i, match in enumerate(matches):

        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        article = text[start:end].strip()
        articles.append(article)
        text_after_extraction += article
    i = 1
    # for article in articles:
    #     print(f"====Article {i}====")
    #     print(article)
    #     i += 1

    return articles


# 2. NORMALIZE OCR
def normalize_line(line):
    line = line.strip()

    # 1. XÓA SỐ TRANG
    if re.fullmatch(r"\d+", line):
        return ""
    
    # 2. SỬA LỖI OCR: "©)" -> "c)"
    line = re.sub(
        r"^©\)",
        "c)",
        line,
        flags=re.IGNORECASE
    )

    # 3. SỬA LỖI OCR: "¬.)" -> "4)"
    line = re.sub(
        r"^¬\.\.",
        "4.",
        line,
        flags=re.IGNORECASE
    )

    # 4. SỬA LỖI OCR: "ø)" -> "g)"
    line = re.sub(
        r"^ø\)",
        "g)",
        line,
        flags=re.IGNORECASE
    )

    return line

# 3. BUILD STRUCTURE TREE
def build_structure(text):
    lines = text.splitlines()
    article = None
    current_clause = None
    current_point = None

    for raw_line in lines:
        #Xử lí lỗi trước
        line = normalize_line(raw_line)
        if not line:
            continue
        # ----------------------------------------------------
        # PHÁT HIỆN ĐIỀU
        # ----------------------------------------------------
        match = ARTICLE_RE.match(line)
        #NẾU CÓ ĐIỀU
        if match:
            article = {
                "article_id": int(match.group(1)),
                "content_art": match.group(2).strip(),
                "sections": []
            }

            current_clause = None
            current_point = None
            continue
        if article is None:
            continue

        # ----------------------------------------------------
        # PHÁT HIỆN KHOẢN
        # ----------------------------------------------------
        match = CLAUSE_RE.match(line)
        #NẾU CÓ KHOẢN
        if match:
            current_clause = {
                "section_id": int(match.group(1)),
                "title_sec": match.group(2).strip(),
                "points": []
            }

            # current_clause["title_sec"] = match.group(2).strip()
            article["sections"].append(current_clause)
            current_point = None
            continue

        # ----------------------------------------------------
        # POINT
        # ----------------------------------------------------
        # CHỈ PHẦN NÀY DÙNG finditer()
        # ----------------------------------------------------

        if current_clause is not None:
            #TÌM CÁC LINE KHỚP VÀ CHUYỂN THÀNH LIST
            point_matches = list(POINT_RE.finditer(line))
            if point_matches:
                for i, point_match in enumerate(point_matches):
                    # Label: a, b, c...
                    label = point_match.group(1).lower()
                    # Bắt đầu nội dung sau "a)"
                    start = point_match.end()

                    # Nếu còn point tiếp theo thì nội dung
                    # kết thúc ngay trước point tiếp theo
                    if i + 1 < len(point_matches):
                        end = point_matches[i + 1].start()
                    else:
                        end = len(line)
                    point_text = line[start:end].strip()

                    # Xóa dấu ; ở cuối nội dung
                    point_text = point_text.strip(" ;")

                    current_point = {
                        "label": label,
                        "text": point_text
                    }

                    current_clause["points"].append(current_point)

                continue

        # ----------------------------------------------------
        # CONTINUATION
        # ----------------------------------------------------
        #Kiểm tra và gán dòng vào điểm
        if current_point is not None:
            current_point["text"] += " " + line

        #Nếu không có điểm, đang có khoản thì gán vào khoản
        elif current_clause is not None:
            current_clause["title_sec"] += " " + line

        #Nếu cả khoản và điểm k có thì gán vào điều
        elif article is not None:
            article["content_art"] += " " + line

    return article


def context_inheritance(results_chunking):
    all_chunks = []
    article_ids = set()

    for article in results_chunking:
        article_id = article["article_id"]

        # Thu thập article_id, tự động loại bỏ trùng lặp
        article_ids.add(article_id)

        article_text = f"Điều {article_id}: {article['content_art']}"

        if article["sections"]:
            for section in article["sections"]:
                section_id = section["section_id"]

                section_text = (
                    f"{article_text}\n"
                    f"Khoản {section_id}: {section['title_sec']}"
                )

                if section["points"]:
                    for point in section["points"]:
                        chunk_text = (
                            f"{section_text}\n"
                            f"Điểm {point['label']}) {point['text']}"
                        )

                        all_chunks.append({
                            "text": chunk_text,
                            "article_id": article_id,
                            "section_id": section_id,
                            "point_label": point["label"]
                        })

                else:
                    all_chunks.append({
                        "text": section_text,
                        "article_id": article_id,
                        "section_id": section_id,
                        "point_label": None
                    })

        else:
            all_chunks.append({
                "text": article_text,
                "article_id": article_id,
                "section_id": None,
                "point_label": None
            })

    return all_chunks, list(article_ids)

