import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel


# Khởi tạo mô hình embedding và tokenizer từ tên model hoặc đường dẫn được cung cấp.
# Tự động xác định thiết bị thực thi CPU/GPU, đưa mô hình về chế độ đánh giá và trả về các thành phần cần thiết.
def load_embedding_model(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Khởi tạo model embedding, tokenizer và xác định thiết bị thực thi.
    Args:
        model_name: Tên hoặc đường dẫn model embedding.

    Returns:
        model: Model embedding.
        tokenizer: Tokenizer tương ứng.
        device: Thiết bị thực thi (CPU/GPU).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()
    return model, tokenizer, device


# Chuyển một câu văn bản thành vector embedding thông qua mô hình ngôn ngữ.
# Áp dụng Mean Pooling có Attention Mask và L2 Normalization để tạo vector biểu diễn ngữ nghĩa.
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


# Chuyển văn bản thành vector embedding phục vụ quá trình ánh xạ và so sánh dữ liệu.
# Sử dụng Mean Pooling kết hợp Attention Mask và L2 Normalization, trả về tensor embedding đã chuẩn hóa.
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



# Tạo embedding cho thuộc tính name của các node trong Knowledge Graph theo từng batch.
# Lưu vector embedding vào Neo4j và gắn label Entity cho các node được xử lý.
def build_name_embeddings(batch_size=100, tokenizer=None, embedding_model=None, device=None):
    from app.database.connection import Neo4jConnection
    neo4j = Neo4jConnection()
    driver = neo4j.get_driver()
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


# Tạo Vector Index trên thuộc tính name_embedding của các node Entity trong Neo4j.
# Cho phép tìm kiếm node dựa trên độ tương đồng cosine giữa các vector embedding.
def create_vector_index():
    from app.database.connection import Neo4jConnection
    neo4j = Neo4jConnection()
    driver = neo4j.get_driver()
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
            session.run(query).consume()
    finally:
        driver.close()