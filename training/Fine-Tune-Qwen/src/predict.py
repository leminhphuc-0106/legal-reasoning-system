def generate_report(model, tokenizer, SYSTEM_PROMPT, json_data, max_new_tokens=2048):
    import json
    import torch
    user_prompt = f"""
            Hãy tạo báo cáo đánh giá từ kết quả JSON sau:
            {json.dumps(json_data, ensure_ascii=False, indent=2)}
            Yêu cầu:
            - Phân tích hồ sơ ứng viên.
            - Đánh giá kết quả mapping.
            - Giải thích các tiêu chí được truy xuất từ Knowledge Graph.
            - Chỉ ra các điểm chưa hợp lý nếu có.
            - Bảo toàn kết luận và số liệu đánh giá gốc.
            - Không tự suy diễn thông tin pháp lý.
            """

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    # -------------------------------------------------
    # Chuyển messages thành input
    # -------------------------------------------------

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
        return_dict=True
    )

    # Đưa input đến thiết bị của embedding layer.
    # Không chuyển toàn bộ model vì đang sử dụng device_map="auto".
    input_device = model.get_input_embeddings().weight.device

    inputs = {
        key: value.to(input_device)
        for key, value in inputs.items()
    }

    input_ids = inputs["input_ids"]

    print(f"Input shape: {input_ids.shape}")

    # -------------------------------------------------
    # Sinh nội dung
    # -------------------------------------------------

    with torch.inference_mode():
        print("ĐANG SINH KÊT QUẢ.....")
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id
        )

    # -------------------------------------------------
    # Chỉ lấy phần nội dung được sinh thêm
    # -------------------------------------------------

    input_length = input_ids.shape[-1]

    generated_tokens = outputs[0][input_length:]

    report = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return report.strip()