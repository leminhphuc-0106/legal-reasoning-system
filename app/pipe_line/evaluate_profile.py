import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

def get_model_and_tokenizer(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Khởi tạo và trả về model embedding và tokenizer.
    Args:
        model_name: Tên model embedding.
    Returns:
        embedding_model: Model embedding đã được khởi tạo.
        tokenizer: Tokenizer đã được khởi tạo.
        device: Thiết bị sử dụng (CPU hoặc GPU).
    """
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    # Khởi tạo tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Khởi tạo model embedding
    embedding_model = AutoModel.from_pretrained(
        model_name
    ).to(device)

    embedding_model.eval()

    return embedding_model, tokenizer, device



def get_embedding(sentence: str, tokenizer, embedding_model, device) -> list:
    """
    Chuyển một câu thành vector embedding.
    Args:
        sentence: Câu đầu vào.
        tokenizer: Tokenizer đã được khởi tạo.
        embedding_model: Model embedding đã được khởi tạo.
        device: Thiết bị sử dụng (CPU hoặc GPU).
    Returns:
        Vector embedding đã được chuẩn hóa.
    """

    if not isinstance(sentence, str) or not sentence.strip():
        raise ValueError("Câu đầu vào không được để trống.")

    # Tokenization
    inputs = tokenizer(
        sentence.strip(),
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    ).to(device)
    with torch.inference_mode():

        # Lấy hidden states
        outputs = embedding_model(**inputs)

        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]

        # Mean Pooling có sử dụng Attention Mask
        mask = attention_mask.unsqueeze(-1).expand(
            token_embeddings.size()
        ).float()

        sum_embeddings = torch.sum(
            token_embeddings * mask,
            dim=1
        )

        sum_mask = torch.clamp(
            mask.sum(dim=1),
            min=1e-9
        )

        embeddings = sum_embeddings / sum_mask

        # L2 Normalize
        embeddings = F.normalize(
            embeddings,
            p=2,
            dim=1
        )
    # Trả về một vector duy nhất
    return embeddings[0].cpu().tolist()

#Tính emnbedding cho tất cả các node có thuộc tính name trong Neo4j và lưu vào thuộc tính name_embedding
# Tính embedding cho tất cả các node có thuộc tính name trong Neo4j
# và lưu vào thuộc tính name_embedding
def build_name_embeddings(batch_size=100, tokenizer=None, embedding_model=None, device=None):

    from app.pipe_line.build_graph import connect_neo4j

    driver = connect_neo4j()

    try:
        with driver.session() as session:

            # 1. Lấy tất cả node có thuộc tính name
            records = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                  AND trim(toString(n.name)) <> ''

                RETURN
                    elementId(n) AS node_id,
                    toString(n.name) AS name
            """).data()

            if not records:
                print("Không tìm thấy node nào có thuộc tính name.")
                return

            print(f"Tìm thấy {len(records)} node.")

            # 2. Chia batch và tạo embedding
            for i in range(0, len(records), batch_size):

                batch_records = records[i:i + batch_size]
                rows = []

                for record in batch_records:

                    name = record["name"]

                    embedding = get_embedding(
                        name,
                        tokenizer,
                        embedding_model,
                        device
                    )

                    rows.append({
                        "node_id": record["node_id"],
                        "embedding": embedding
                    })

                # 3. Lưu embedding và gắn label Entity
                session.run("""
                    UNWIND $rows AS row

                    MATCH (n)
                    WHERE elementId(n) = row.node_id

                    SET n:Entity
                    SET n.name_embedding = row.embedding
                """, rows=rows).consume()

    finally:
        driver.close()

#Tạo Vector Index cho thuộc tính name_embedding nếu chưa tồn tại
def create_vector_index():
    from app.pipe_line.build_graph import connect_neo4j

    driver = connect_neo4j()

    query = """
    CREATE VECTOR INDEX name_embedding IF NOT EXISTS
    FOR (n:Entity)
    ON (n.name_embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """

    try:
        with driver.session() as session:

            # Tạo Vector Index nếu chưa tồn tại
            session.run(query).consume()

            # Kiểm tra trạng thái Index
            # result = session.run("""
            #     SHOW VECTOR INDEXES
            #     YIELD name, state, labelsOrTypes, properties
            #     RETURN name, state, labelsOrTypes, properties
            # """)

    finally:
        driver.close()

# Truy vấn Knowledge Graph dựa trên embedding của tên đầu vào
def query_graph(text_name: str, top_k: int = 1, tokenizer=None, embedding_model=None, device=None):

    from app.pipe_line.build_graph import connect_neo4j

    if not text_name or not text_name.strip():
        raise ValueError("Tên đầu vào không được để trống.")

    if top_k < 1:
        raise ValueError("top_k phải lớn hơn hoặc bằng 1.")

    # Tạo embedding cho text đầu vào
    embedding = get_embedding(text_name, tokenizer, embedding_model, device)

    driver = connect_neo4j()

    query = """
    CALL db.index.vector.queryNodes(
        'name_embedding',
        $top_k,
        $embedding
    )
    YIELD node, score

    RETURN
        elementId(node) AS node_id,
        node.name AS name,
        node.type AS type,
        node.article_id AS article_id,
        node.section_id AS section_id,
        score

    ORDER BY score DESC
    """

    try:
        with driver.session() as session:

            records = session.run(
                query,
                embedding=embedding,
                top_k=top_k
            )

            return [record.data() for record in records]

    finally:
        driver.close()


def parse_text_to_dict(text):
    field_mapping = {
        "Cá nhân": "DOI_TUONG",
        "Tập thể": "DOI_TUONG",
        "Loại xét": "LOAI_XET",
        "Thời điểm xét": "THOI_DIEM_XET",
        "Danh hiệu thi đua": "DANH_HIEU_THI_DUA",
        "Kết quả đánh giá": "KET_QUA_DANH_GIA",
        "Hình thức khen thưởng": "HINH_THUC_KHEN_THUONG",
        "Sáng kiến NCKH": "SANG_KIEN_NCKH"
    }

    result = {}
    lines = text.splitlines()

    # Lấy dòng đầu tiên không rỗng
    first_line = next((line.strip() for line in lines if line.strip()), "")

    if first_line.startswith("Cá nhân:"):
        result["LOAI_DOI_TUONG"] = "CA_NHAN"

    elif first_line.startswith("Tập thể:"):
        result["LOAI_DOI_TUONG"] = "TAP_THE"

    # Trích xuất dữ liệu
    for line in lines:
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        if key in field_mapping:
            result[field_mapping[key]] = value

    return result


def find_criterion(results, type_):
    criteria = []
    # 5. Lấy node có Similarity Score cao nhất
    if results:
        best_result = max(results, key=lambda x: x["score"])

        # Chuyển thông tin node thành dictionary
        best_node = {
            "node_id": best_result["node_id"],
            "name": best_result["name"],
            "type": best_result["type"],
            "article_id": best_result["article_id"],
            "section_id": best_result["section_id"],
            "similarity_score": best_result["score"]
        }

        print("\n===== NODE CÓ SIMILARITY CAO NHẤT =====")
        print(best_node)

        article_id = best_node["article_id"]

        from app.pipe_line.build_graph import connect_neo4j

        driver = connect_neo4j()

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



        with driver.session() as session:

            result = session.run(
                cypher,
                article_id=article_id,
                type_=type_
            )

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
                            f' {rel["relation"]} '
                            f'{nodes[i + 1]["name"]}'
                        )
                    })

                if path:
                    criteria.append({
                        "article_id": relations[0]["article_id"],
                        "section_id": relations[0]["section_id"],
                        "point_label": relations[0]["point_label"],
                        "path": path
                    })

        driver.close()
    else:
        best_node = None
        print("\nKhông tìm thấy node phù hợp.")

    return criteria


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


def load_embedding_model_map(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model.to(device)
    model.eval()

    return model, tokenizer, device


def get_embedding_map(text, model, tokenizer, device):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

        # Mean Pooling
        attention_mask = inputs["attention_mask"]

        token_embeddings = outputs.last_hidden_state

        mask = attention_mask.unsqueeze(-1).expand(
            token_embeddings.size()
        ).float()

        embedding = torch.sum(token_embeddings * mask, dim=1) / torch.clamp(
            mask.sum(dim=1), min=1e-9
        )

    return F.normalize(embedding, p=2, dim=1)

def evaluate(text = """Cá nhân: Đinh Thị O
    Loại xét: Khen thưởng - Bằng khen của Chủ tịch UBND thành phố
    Thời điểm xét: tháng 08/2024
    Danh hiệu thi đua: Lao động tiên tiến 2022 - 2023; Lao động tiên tiến 2023 - 2024
    Kết quả đánh giá: Hoàn thành xuất sắc nhiệm vụ 2022 - 2023; Hoàn thành xuất sắc nhiệm vụ 2023 - 2024
    Hình thức khen thưởng: Giấy khen của Hiệu trưởng 2022 - 2023; Giấy khen của Hiệu trưởng 2023 - 2024
    Sáng kiến NCKH: 02 sáng kiến được công nhận có hiệu quả áp dụng và phạm vi ảnh hưởng ở cơ sở trong năm học 2022 - 2023 và 2023 - 2024
    """):


    data = parse_text_to_dict(text)
    award = data["LOAI_XET"]
    type_ = data["LOAI_DOI_TUONG"]


    # 1. Khởi tạo model và tokenizer
    embedding_model, tokenizer, device = get_model_and_tokenizer()
    embedding_model.eval()

    # 2. Tạo embedding cho tất cả node trong Neo4j
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
    # Hiển thị kết quả
    for i, criterion in enumerate(criteria, 1):

        print(f"\n===== CRITERION {i} =====")

        for item in criterion["path"]:
            print(
                item["text"]
            )

    model, tokenizer, device = load_embedding_model_map()

    # Mapping dữ liệu hồ sơ với tiêu chí
    mapped_results = map_data_to_criteria(
        data=data,
        criteria=criteria,
        model=model,
        tokenizer=tokenizer,
        device=device,
        threshold=0.65
    )

    for field, items in mapped_results.items():
        print(f"\n{'=' * 70}")
        print(f"FIELD: {field}")
        print(f"{'=' * 70}")

        for item in items:
            print(f"\n[INPUT] {item['input']}")

            if not item["matches"]:
                print("  -> Không tìm thấy tiêu chí phù hợp.")
                continue

            for i, match in enumerate(item["matches"], 1):
                print(f"\n  MATCH {i}: {match['text']}")
                print(f"  Similarity: {match['similarity']:.4f}")
                print(f"  Article: {match['article_id']}")
                print(f"  Section: {match['section_id']}")
                print(f"  Point: {match['point_label']}")

    return mapped_results
