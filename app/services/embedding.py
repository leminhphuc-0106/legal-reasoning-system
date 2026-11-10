import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

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