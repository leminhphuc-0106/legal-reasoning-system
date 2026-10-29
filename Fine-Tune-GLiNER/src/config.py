import os
from dataclasses import dataclass
from gliner import GLiNER


@dataclass
class ConfigTraining:
    # 1. Model
    model_name: str = "belumind/barb-2-ie-vi"

    # 2. Thư mục lưu model
    output_dir: str = (
        "/content/drive/MyDrive/Project/Xet_Khen_Thuong/"
        "Models/GLiNER-Model"
    )
    # 3. Tham số huấn luyện
    max_steps: int = 500
    learning_rate: float = 1e-5

    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8

    # 4. Đánh giá và ghi log
    eval_strategy: str = "steps"
    eval_steps: int = 50

    logging_strategy: str = "steps"
    logging_steps: int = 10

    # 5. Lưu checkpoint
    save_strategy: str = "no"


def train_model(
    model: GLiNER,
    train_data: list,
    eval_data: list,
    config: ConfigTraining,
):
    # Tạo thư mục lưu model
    os.makedirs(config.output_dir, exist_ok=True)

    # Kiểm tra số lượng dữ liệu
    print("Train samples:", len(train_data))
    print("Eval samples:", len(eval_data))

    # Fine-tuning
    trainer = model.train_model(
        output_dir=config.output_dir,
        train_dataset=train_data,
        eval_dataset=eval_data,

        max_steps=config.max_steps,
        learning_rate=config.learning_rate,

        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,

        eval_strategy=config.eval_strategy,
        eval_steps=config.eval_steps,

        logging_strategy=config.logging_strategy,
        logging_steps=config.logging_steps,

        save_strategy=config.save_strategy,
    )

    # Lưu model cuối cùng
    model.save_pretrained(config.output_dir)

    print(f"Đã lưu model tại: {config.output_dir}")

    return trainer


# ==========================
# Sử dụng
# ==========================

# config = ConfigTraining()

# model = GLiNER.from_pretrained(config.model_name)

# trainer = train_model(
#     model=model,
#     train_data=clean_data,
#     eval_data=clean_data_eval,
#     config=config,
# )