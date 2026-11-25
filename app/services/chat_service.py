import re
import threading
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

# =====================================================
# 1. CẤU HÌNH MODEL
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_DIR = MODELS_DIR / "Model-Qwen-Viet"
BASE_MODEL_DIR = MODELS_DIR / "Qwen3-0.6B"

_model_bundle = None
_model_lock = threading.Lock()
_generation_lock = threading.Lock()

SYSTEM_PROMPT = """
Bạn là trợ lý AI hỗ trợ tra cứu pháp luật và xét khen thưởng hành chính.
Hãy trả lời bằng tiếng Việt trang trọng, rõ ràng, ngắn gọn và đúng trọng tâm.
Chỉ sử dụng thông tin trong ngữ cảnh được cung cấp và kiến thức pháp luật chung.
Không tự tạo ra căn cứ pháp lý, số hiệu văn bản hoặc thành tích không có trong dữ liệu.
Nếu dữ liệu không đủ để kết luận, hãy nói rõ là chưa đủ căn cứ.
"""


# Tải tokenizer và mô hình Qwen-Viet (kèm adapter LoRA) một lần duy nhất.
def load_chat_model():
    global _model_bundle

    if _model_bundle is not None:
        return _model_bundle

    with _model_lock:
        if _model_bundle is not None:
            return _model_bundle

        tokenizer = AutoTokenizer.from_pretrained(
            str(MODEL_DIR),
            trust_remote_code=True,
        )

        adapter_config = MODEL_DIR / "adapter_config.json"
        if adapter_config.exists():
            # Model-Qwen-Viet là adapter LoRA nên cần nạp base model trước.
            base_path = str(BASE_MODEL_DIR) if BASE_MODEL_DIR.exists() else "Qwen/Qwen3-0.6B"
            base_model = AutoModelForCausalLM.from_pretrained(
                base_path,
                dtype="auto",
                device_map="auto",
                trust_remote_code=True,
            )
            model = PeftModel.from_pretrained(base_model, str(MODEL_DIR))
        else:
            model = AutoModelForCausalLM.from_pretrained(
                str(MODEL_DIR),
                dtype="auto",
                device_map="auto",
                trust_remote_code=True,
            )

        model.eval()
        _model_bundle = (model, tokenizer)

    return _model_bundle


# Tóm tắt ngắn gọn danh sách hồ sơ để làm ngữ cảnh cho trợ lý.
def build_candidate_context(candidates):
    if not candidates:
        return ""

    lines = []
    for candidate in candidates[:10]:
        coverage = candidate.get("coverage") or {}
        lines.append(
            "- {name} ({id}): đạt {achieved}/{total} tiêu chí, tỷ lệ {percent}%.".format(
                name=candidate.get("name", "Chưa rõ"),
                id=candidate.get("id", "Chưa rõ"),
                achieved=coverage.get("achieved_criteria", 0),
                total=coverage.get("total_criteria", 0),
                percent=coverage.get("coverage_percentage", 0),
            )
        )

    return "\n".join(lines)


# Sinh câu trả lời của trợ lý từ câu hỏi, lịch sử hội thoại và ngữ cảnh hồ sơ.
def generate_chat_answer(message, history=None, candidates=None):
    model, tokenizer = load_chat_model()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    context = build_candidate_context(candidates)
    if context:
        messages.append({
            "role": "system",
            "content": f"Thông tin hồ sơ đang xét:\n{context}",
        })

    # Giới hạn lịch sử và độ dài mỗi tin nhắn để không vượt ngữ cảnh của model.
    for item in (history or [])[-6:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()[:1500]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
        return_dict=True,
    )

    # Chỉ chuyển input tới thiết bị chứa embedding do model dùng device_map="auto".
    input_device = model.get_input_embeddings().weight.device
    inputs = {key: value.to(input_device) for key, value in inputs.items()}

    input_length = inputs["input_ids"].shape[-1]

    # Tuần tự hóa quá trình sinh để tránh nhiều request dùng chung model cùng lúc.
    with _generation_lock, torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    answer = tokenizer.decode(
        outputs[0][input_length:],
        skip_special_tokens=True,
    )

    # Loại bỏ các ký hiệu Markdown để câu trả lời hiển thị gọn trên giao diện.
    answer = re.sub(r"\*\*|__|`", "", answer)

    return answer.strip()
