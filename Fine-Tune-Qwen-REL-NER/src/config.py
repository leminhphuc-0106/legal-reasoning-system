
from dataclasses import dataclass, field
from typing import Literal

import torch
from transformers import BitsAndBytesConfig
from peft import LoraConfig
from trl import SFTConfig


# ============================================================
# QUANTIZATION CONFIG
# Quản lý cấu hình lượng tử hóa 4-bit cho QLoRA.
# ============================================================
@dataclass
class QuantizationConfig:
    load_in_4bit: bool = True
    quant_type: Literal["nf4", "fp4"] = "nf4"
    use_double_quant: bool = True
    compute_dtype: torch.dtype = torch.bfloat16

    def build(self) -> BitsAndBytesConfig:
        return BitsAndBytesConfig(
            load_in_4bit=self.load_in_4bit,
            bnb_4bit_quant_type=self.quant_type,
            bnb_4bit_use_double_quant=self.use_double_quant,
            bnb_4bit_compute_dtype=self.compute_dtype,
        )


# ============================================================
# LORA CONFIG
# Quản lý các tham số LoRA dùng để fine-tune model.
# ============================================================
@dataclass
class LoRAConfig:
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"

    #Các layer được cập nhật trong quá trình Fine-Tune
    target_modules: list[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )

    def build(self) -> LoraConfig:
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            bias=self.bias,
            task_type=self.task_type,
            target_modules=self.target_modules,
        )


# ============================================================
# TRAINING CONFIG
# Quản lý tham số huấn luyện và cấu hình SFT.
# ============================================================
@dataclass
class TrainingConfig:
    output_dir: str = '/content/drive/MyDrive/Project/Xet_Khen_Thuong/Fine-Tune-Qwen-Ner-Rel/CheckPoints'
    # Số epoch
    num_train_epochs: int = 6

    # Batch size
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8

    # Tối ưu hóa
    learning_rate: float = 1e-4
    optim: str = "paged_adamw_8bit"
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.01

    # Logging và lưu checkpoint

    logging_steps: int = 1
    save_strategy: str = "steps"
    save_steps: int = 5
    save_total_limit: int = 2


    # Logging và checkpoint
    # logging_steps: int = 1
    # save_strategy: str = "epoch"
    # save_total_limit: int = 2
    # load_best_model_at_end: bool = True
    # metric_for_best_model: str = "eval_loss"
    # greater_is_better: bool = False

    # Đánh giá
    eval_strategy: str = "epoch"

    # Precision
    fp16: bool = False
    bf16: bool = True

    # Tiết kiệm bộ nhớ
    gradient_checkpointing: bool = True
    gradient_checkpointing_kwargs: dict = field(
        default_factory=lambda: {"use_reentrant": False}
    )

    # Hugging Face reporting
    report_to: str = "none"

    # Cấu hình riêng cho SFT
    dataset_text_field: str = "text"
    max_length: int = 512
    packing: bool = False

    def build(self) -> SFTConfig:
        return SFTConfig(
            output_dir=self.output_dir,
            num_train_epochs=self.num_train_epochs,
            per_device_train_batch_size=self.per_device_train_batch_size,
            per_device_eval_batch_size=self.per_device_eval_batch_size,
            gradient_accumulation_steps=self.gradient_accumulation_steps,
            learning_rate=self.learning_rate,
            optim=self.optim,
            logging_steps=self.logging_steps,
            save_strategy=self.save_strategy,
            save_steps=self.save_steps,
            save_total_limit=self.save_total_limit,
            eval_strategy=self.eval_strategy,
            fp16=self.fp16,
            bf16=self.bf16,
            gradient_checkpointing=self.gradient_checkpointing,
            gradient_checkpointing_kwargs=(
                self.gradient_checkpointing_kwargs
            ),
            lr_scheduler_type=self.lr_scheduler_type,
            weight_decay=self.weight_decay,
            report_to=self.report_to,
            dataset_text_field=self.dataset_text_field,
            max_length=self.max_length,
            packing=self.packing,
        )


# # ============================================================
# # KHỞI TẠO CONFIG
# # ============================================================
# quantization_config = QuantizationConfig()
# lora_config = LoRAConfig()
# training_config = TrainingConfig()

# bnb_config = quantization_config.build()
# peft_config = lora_config.build()
# training_args = training_config.build()
