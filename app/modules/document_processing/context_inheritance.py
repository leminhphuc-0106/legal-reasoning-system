#Kế thừa ngữ cảnh
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

