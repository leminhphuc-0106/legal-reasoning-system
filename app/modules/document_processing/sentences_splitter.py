#Load model đã fine-tune
def load_model(model_path="./models/Vi-T5-Base-Tach-Cau"):
    from transformers import T5Tokenizer, AutoModelForSeq2SeqLM
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


#Tách từng câu
def simplify(chunk, tokenizer, model):
    import torch
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

#Tách cả văn bản sau khi chunking
def simplify_chunk(text_chunks):
    #Tách câu đơn bằng mô hình Vi-T5 đã fine-tune
    model, tokenizer = load_model()
    splited_results = []
    count = 0
    for chunk in text_chunks:
        answer = simplify(chunk["text"], tokenizer, model)
        answer = {
            "text": answer,
            "article_id": chunk["article_id"],
            "section_id": chunk["section_id"],
            "point_label": chunk["point_label"]
        }
        splited_results.append(answer)
        if count <= 5:
            count += 1
            print(answer)
    return splited_results
