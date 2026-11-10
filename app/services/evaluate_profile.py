import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

def map_data_to_criteria(data, criteria, model, tokenizer, device, threshold=0.65):
    from app.pipe_line.embedding import get_embedding_map
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

def evaluate(text = """Cá nhân: Đinh Thị O
    Loại xét: Khen thưởng - Bằng khen của Chủ tịch UBND thành phố
    Thời điểm xét: tháng 08/2024
    Danh hiệu thi đua: Lao động tiên tiến 2022 - 2023; Lao động tiên tiến 2023 - 2024
    Kết quả đánh giá: Hoàn thành xuất sắc nhiệm vụ 2022 - 2023; Hoàn thành xuất sắc nhiệm vụ 2023 - 2024
    Hình thức khen thưởng: Giấy khen của Hiệu trưởng 2022 - 2023; Giấy khen của Hiệu trưởng 2023 - 2024
    Sáng kiến NCKH: 02 sáng kiến được công nhận có hiệu quả áp dụng và phạm vi ảnh hưởng ở cơ sở trong năm học 2022 - 2023 và 2023 - 2024
    """, ):
    from app.pipe_line.data_parser import parse_text_to_dict
    data = parse_text_to_dict(text)
    award = data["LOAI_XET"]
    type_ = data["LOAI_DOI_TUONG"]
    # 1. Khởi tạo model và tokenizer
    
    from app.pipe_line.embedding import load_embedding_model
    embedding_model, tokenizer, device = load_embedding_model()

    # 2. Tạo embedding cho tất cả node trong Neo4j
    from app.pipe_line.query_graph import build_name_embeddings, create_vector_index, query_graph, find_criterion
    build_name_embeddings(
        batch_size=100,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device
    )

    # 3. Tạo Vector Index
    create_vector_index()

    # 4. Thử nghiệm truy vấn Knowledge Graph
    results = query_graph(
        text_name=award,
        top_k=5,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device
    )

    print(f"\nKết quả truy vấn cho: {award}")

    for i, result in enumerate(results, start=1):
        print(f"\nKết quả {i}:")
        print(f"Node ID: {result['node_id']}")
        print(f"Name: {result['name']}")
        print(f"Type: {result['type']}")
        print(f"Article ID: {result['article_id']}")
        print(f"Section ID: {result['section_id']}")
        print(f"Similarity Score: {result['score']:.4f}")

    criteria = find_criterion(results=results, type_=type_)

    # Mapping dữ liệu hồ sơ với tiêu chí
    mapped_results = map_data_to_criteria(
        data=data,
        criteria=criteria,
        model=embedding_model,
        tokenizer=tokenizer,
        device=device,
        threshold=0.65
    )
    coverage = evaluate_criterion_coverage(
        criteria=criteria,
        mapped_results=mapped_results
    )

    return mapped_results, criteria, data, coverage
