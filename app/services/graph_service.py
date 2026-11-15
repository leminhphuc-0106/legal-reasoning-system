from app.modules.knowlege_graph import load_embedding_model, build_graph, build_name_embeddings, create_vector_index, query_graph
from app.modules.knowlege_graph import get_embedding_map
# Truy xuất các đường dẫn quan hệ trong Knowledge Graph dựa trên node có độ tương đồng cao nhất.
# Lọc theo loại thực thể và article_id, đồng thời loại bỏ các đường dẫn trùng lặp dạng tiền tố.
def find_criterion(results, type_):
    criteria = []

    # 1. Lấy node có Similarity Score cao nhất
    if not results:
        print("\nKhông tìm thấy node phù hợp.")
        return criteria

    best_result = max(results, key=lambda x: x["score"])
    article_id = best_result["article_id"]

    # 2. Kết nối Neo4j
    from app.database.connection import Neo4jConnection
    neo4j = Neo4jConnection()
    driver = neo4j.get_driver()
    cypher = """
        MATCH path = (h:Entity)-[*1..5]->(t:Entity)

        WHERE h.type = $type_
        AND ALL(r IN relationships(path)
            WHERE r.article_id = $article_id)

        RETURN
            [n IN nodes(path) | {
                name: n.name,
                type: n.type
            }] AS nodes,

            [r IN relationships(path) | {
                relation: type(r),
                article_id: r.article_id,
                section_id: r.section_id,
                point_label: r.point_label
            }] AS relations
    """

    try:
        with driver.session() as session:
            result = session.run(
                cypher,
                article_id=article_id,
                type_=type_
            )

            # 3. Thu thập toàn bộ path
            all_paths = []

            for record in result:
                nodes = record["nodes"]
                relations = record["relations"]

                path = []

                for i, rel in enumerate(relations):
                    path.append({
                        "head": nodes[i]["name"],
                        "head_type": nodes[i]["type"],
                        "relation": rel["relation"],
                        "tail": nodes[i + 1]["name"],
                        "tail_type": nodes[i + 1]["type"],
                        "text": (
                            f'{nodes[i]["name"]} '
                            f'{rel["relation"]} '
                            f'{nodes[i + 1]["name"]}'
                        )
                    })

                if path:
                    all_paths.append({
                        "article_id": relations[0]["article_id"],
                        "section_id": relations[0]["section_id"],
                        "point_label": relations[0]["point_label"],
                        "path": path
                    })

        # 4. Kiểm tra path1 có phải tiền tố của path2 không
        def is_prefix(path1, path2):
            if len(path1) >= len(path2):
                return False

            return all(
                (
                    p1["head"],
                    p1["relation"],
                    p1["tail"]
                ) == (
                    p2["head"],
                    p2["relation"],
                    p2["tail"]
                )
                for p1, p2 in zip(path1, path2)
            )

        # 5. Loại bỏ các path dư thừa
        for i, item in enumerate(all_paths):
            current_path = item["path"]

            redundant = any(
                is_prefix(current_path, other["path"])
                and (
                    item["article_id"],
                    item["section_id"],
                    item["point_label"]
                ) == (
                    other["article_id"],
                    other["section_id"],
                    other["point_label"]
                )
                for j, other in enumerate(all_paths)
                if i != j
            )

            if not redundant:
                criteria.append(item)

    finally:
        driver.close()
    return criteria


import torch
# Ánh xạ các thông tin thành tích trong hồ sơ ứng viên với các tiêu chí tương ứng trong Knowledge Graph.
# Sử dụng cosine similarity giữa các vector embedding để tìm các tiêu chí phù hợp theo ngưỡng tương đồng.
def map_data_to_criteria(data, criteria, model, tokenizer, device, threshold=0.65):
    results = {}

    # Các trường cần mapping
    fields = [
        "DANH_HIEU_THI_DUA",
        "KET_QUA_DANH_GIA",
        "HINH_THUC_KHEN_THUONG",
        "SANG_KIEN_NCKH"
    ]

    # Lấy toàn bộ tiêu chí từ Knowledge Graph
    criterion_texts = []

    for criterion in criteria:
        for item in criterion["path"]:
            criterion_texts.append({
                "text": item["text"],
                "article_id": criterion["article_id"],
                "section_id": criterion["section_id"],
                "point_label": criterion["point_label"],
                "head_type": item["head_type"],
                "relation": item["relation"],
                "tail_type": item["tail_type"]
            })

    if not criterion_texts:
        return results

    # Embedding các tiêu chí
    criterion_embeddings = torch.cat([
        get_embedding_map(
            item["text"], model, tokenizer, device
        )
        for item in criterion_texts
    ], dim=0)

    # Mapping từng trường dữ liệu
    for field in fields:
        value = data.get(field)
        if not value:
            continue

        # Tách các thành tích
        values = [
            x.strip()
            for x in value.split(";")
            if x.strip()
        ]

        results[field] = []

        for text in values:
            input_embedding = get_embedding_map(
                text, model, tokenizer, device
            )

            # Tính cosine similarity
            scores = torch.mm(
                input_embedding,
                criterion_embeddings.T
            )[0]

            # Lấy tiêu chí tương đồng nhất
            best_indices = torch.argsort(
                scores, descending=True
            )

            matches = []

            for idx in best_indices:
                score = scores[idx].item()
                if score < threshold:
                    break

                criterion = criterion_texts[idx]
                matches.append({
                    **criterion,
                    "similarity": round(score, 4)
                })
            results[field].append({
                "input": text,
                "matches": matches
            })
    return results



# Đánh giá mức độ bao phủ của các tiêu chí pháp lý dựa trên kết quả ánh xạ dữ liệu hồ sơ.
# Thống kê số tiêu chí đã đạt, chưa đạt và tỷ lệ bao phủ, đồng thời lưu thông tin đối chiếu tương ứng.
def evaluate_criterion_coverage(criteria, mapped_results):
    """
    Thống kê số tiêu chí có thông tin đối chiếu phù hợp
    trên tổng số tiêu chí được truy vấn từ Knowledge Graph.

    Một tiêu chí được định danh bằng:
    article_id + section_id + point_label
    """

    # 1. Tập hợp toàn bộ tiêu chí duy nhất
    all_criteria = {}

    for criterion in criteria:
        key = (
            criterion["article_id"],
            criterion["section_id"],
            criterion["point_label"]
        )

        all_criteria[key] = {
            "article_id": criterion["article_id"],
            "section_id": criterion["section_id"],
            "point_label": criterion["point_label"],
            "path": criterion["path"]
        }

    total_criteria = len(all_criteria)

    # 2. Tập hợp các tiêu chí đã tìm thấy thông tin phù hợp
    matched_criteria = {}

    for field, items in mapped_results.items():
        for item in items:
            for match in item["matches"]:

                key = (
                    match["article_id"],
                    match["section_id"],
                    match["point_label"]
                )

                if key in all_criteria:
                    # Chỉ tính một lần cho mỗi tiêu chí
                    if key not in matched_criteria:
                        matched_criteria[key] = {
                            **all_criteria[key],
                            "matched_by": []
                        }

                    matched_criteria[key]["matched_by"].append({
                        "field": field,
                        "input": item["input"],
                        "similarity": match["similarity"],
                        "matched_text": match["text"]
                    })

    # 3. Tính tỷ lệ
    achieved = len(matched_criteria)
    not_achieved = total_criteria - achieved

    percentage = (
        achieved / total_criteria * 100
        if total_criteria > 0 else 0
    )

    return {
        "total_criteria": total_criteria,
        "achieved_criteria": achieved,
        "not_achieved_criteria": not_achieved,
        "coverage_percentage": round(percentage, 2),
        "matched_criteria": list(matched_criteria.values()),
        "unmatched_criteria": [
            criterion
            for key, criterion in all_criteria.items()
            if key not in matched_criteria
        ]
    }