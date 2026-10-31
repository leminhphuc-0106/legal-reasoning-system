from transformers import T5Tokenizer, AutoModelForSeq2SeqLM
import torch

# model_path = (
#     "./models/Vi-T5-Base-Tach-Cau"
# )

#Load model đã fine-tune
def load_model(model_path):
    from pathlib import Path
    offload_dir = Path("./offload/simplify_model").resolve()
    offload_dir.mkdir(parents=True, exist_ok=True)
    # 1. Load tokenizer
    tokenizer = T5Tokenizer.from_pretrained(model_path)

    if tokenizer.pad_token is None:
        if tokenizer.eos_token is None:
            raise ValueError("Tokenizer không có pad_token hoặc eos_token.")
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    # 2. Load model
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_path,
        torch_dtype="auto",
        device_map="auto",
        offload_folder=str(offload_dir),
        offload_state_dict=True,
    )
    return model, tokenizer
    # model.eval()


#hàm gọi model và tách câu
def simplify(chunk, tokenizer, model):
    inputs = tokenizer(
        chunk,
        return_tensors="pt",
        truncation=True,
        max_length=512
    ).to(model.device)

    # 5. Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            num_beams=4,
            repetition_penalty=1.1,
            no_repeat_ngram_size=3,
            early_stopping=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # 6. Decode toàn bộ chuỗi được sinh ra
    answer = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return answer


