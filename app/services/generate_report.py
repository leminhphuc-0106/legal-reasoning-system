import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
# =====================================================
# 1. CẤU HÌNH MODEL
# =====================================================
def load_llm_model(MODEL_NAME="D:/PROJECT/Xet_Khen_Thuong/models/Qwen3-0.6B"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True
    )
    model.eval()
    return model, tokenizer, device


# model, tokenizer, device = load_llm_model()
# =====================================================
# 3. HÀM SINH BÁO CÁO
# =====================================================

def generate_report(json_data, model, tokenizer):


    SYSTEM_PROMPT  = """
        Bạn là trợ lý AI chuyên tổng hợp kết quả xét thi đua, khen thưởng
        dựa trên dữ liệu được cung cấp từ hệ thống Knowledge Graph.

        NHIỆM VỤ:
        Phân tích dữ liệu hồ sơ ứng viên và kết quả đối chiếu tiêu chí,
        sau đó tạo một báo cáo đánh giá ngắn gọn, chính xác và dễ đọc.

        YÊU CẦU ĐẦU RA:

        Chỉ được xuất ra báo cáo theo đúng 5 phần sau:

        1. DANH HIỆU XÉT CỦA ỨNG VIÊN
        - Nêu chính xác hình thức khen thưởng đang được xét.

        2. THÔNG TIN VÀ THÀNH TÍCH CỦA ỨNG VIÊN
        - Nêu họ tên, mã hồ sơ, loại đối tượng và thời điểm xét.
        - Liệt kê các danh hiệu thi đua.
        - Liệt kê kết quả đánh giá, hình thức khen thưởng,
        sáng kiến và thành tích nghiên cứu khoa học.
        - Mỗi thành tích chỉ trình bày một lần.
        - Không tự bổ sung thành tích không có trong dữ liệu.

        3. CÁC TIÊU CHÍ HIỆN CÓ CỦA ỨNG VIÊN
        - Liệt kê các tiêu chí được xác định là đã thỏa mãn.
        - Nêu nội dung tiêu chí.
        - Nêu căn cứ pháp lý gồm điều, khoản, điểm.
        - Giải thích thành tích nào của ứng viên đáp ứng tiêu chí.
        - Chỉ chấp nhận bằng chứng có quan hệ ngữ nghĩa phù hợp
        với nội dung tiêu chí.
        - Không sử dụng một kết quả mapping của loại thông tin này
        để chứng minh một tiêu chí thuộc loại thông tin khác.

        4. DANH SÁCH TIÊU CHÍ CHƯA THỎA MÃN
        - Liệt kê các tiêu chí chưa được đáp ứng.
        - Nêu rõ điều kiện còn thiếu nếu dữ liệu xác định được.
        - Nếu không có tiêu chí chưa thỏa mãn, ghi rõ:
        "Không có tiêu chí chưa thỏa mãn được ghi nhận."

        5. KẾT LUẬN
        - Tổng hợp kết quả đối chiếu.
        - Nêu số lượng tiêu chí thỏa mãn và chưa thỏa mãn.
        - Nêu tỷ lệ bao phủ tiêu chí.
        - Không tự đưa ra kết luận ĐẠT hoặc KHÔNG ĐẠT
        nếu dữ liệu không đủ căn cứ.

        QUY TẮC BẮT BUỘC:

        1. Chỉ sử dụng thông tin trong JSON đầu vào.
        2. Không tự tạo ra căn cứ pháp lý.
        3. Không suy diễn rằng hai hình thức khen thưởng
        khác nhau là tương đương.
        4. Không nhầm lẫn giữa thành tích, danh hiệu thi đua
        và hình thức khen thưởng.
        5. Không tự thay đổi kết quả mapping hoặc coverage.
        6. Nếu mapping không phù hợp với tiêu chí, phải cảnh báo
        rằng chưa đủ bằng chứng để xác nhận tiêu chí.
        7. Không sử dụng bảng Markdown.
        8. Không sử dụng ký tự phân cách như |||, ----, =====, ***.
        9. Không lặp lại nội dung.
        10. Chỉ xuất nội dung báo cáo, không giải thích cách
            hoạt động của mô hình, không thêm lời mở đầu
            hoặc lời kết ngoài báo cáo.

        VĂN PHONG:
        - Tiếng Việt trang trọng, rõ ràng.
        - Ngắn gọn, súc tích.
        - Sử dụng danh sách đánh số hoặc gạch đầu dòng.
        - Không sử dụng các đoạn văn quá dài.
        """

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
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
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


import re
def clean_report_text(text):
    # Loại bỏ Markdown
    text = re.sub(r'\*\*|__|~~|==', '', text)
    # Loại bỏ ký tự escape không cần thiết
    text = text.replace('\\', '')
    # Chỉ giữ nội dung từ mục 1 đến hết mục 4
    match = re.search(
        r'1\.\s.*?(?=\n\s*5\.\s|\Z)',
        text,
        flags=re.DOTALL
    )
    if match:
        text = match.group(0)

    # Loại bỏ dấu gạch đầu dòng ở đầu mỗi dòng
    text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.MULTILINE)
    # Chuẩn hóa khoảng trắng
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()

# =====================================================
# 4. HÀM MAIN
# =====================================================
def run(data, model, tokenizer, device):

    # 1. Cấu hình file đầu ra
    OUTPUT_FILE = "D:/PROJECT/Xet_Khen_Thuong/app/result/predict_profile/report.txt"

    try:
        print("Nhận dữ liệu JSON thành công!")

        # 2. Sinh báo cáo
        print("Đang sinh báo cáo...")
        # model, tokenizer, device = load_llm_model()

        report = generate_report(data, model, tokenizer)
        report = clean_report_text(report)

        # 3. Hiển thị báo cáo
        print("\n" + "=" * 70)
        print("BÁO CÁO KẾT QUẢ ĐÁNH GIÁ HỒ SƠ")
        print("=" * 70)

        print(report)

        # 4. Lưu báo cáo
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(report)

        print("\n" + "=" * 70)
        print(f"Đã lưu báo cáo tại: {OUTPUT_FILE}")

        return report

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý: {e}")
        return None