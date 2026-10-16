from dataclasses import asdict, dataclass, fields
from typing import Literal, Any, Dict, Iterable, Optional
from pathlib import Path
import ast

@dataclass
class ConfigTraining:
    # Model checkpoint
    prev_path: str | None = None

    # Training schedule
    num_steps: int = 200
    train_batch_size: int = 8
    eval_every: int = 20
    warmup_ratio: float = 0.1
    scheduler_type: str = "cosine"

    # Learning rates
    lr_encoder: float = 1e-5
    lr_others: float = 5e-5
    weight_decay_encoder: float = 0.01
    weight_decay_other: float = 0.01
    max_grad_norm: float = 1.0

    # Loss configuration
    loss_alpha: float = -1
    loss_gamma: float = 0
    loss_reduction: Literal["sum", "mean", "none"] = "sum"
    negatives: float = 1.0
    masking: Literal["none", "global", "label", "span"] = "none"

    # Checkpointing
    save_total_limit: int = 2

    # Component freezing
    freeze_components: list[str] | None = None


def load_config(path: Optional[str] = None, overrides: Iterable[str] = ()) -> ConfigTraining:
    data: Dict[str, Any] = {}
    if path:
        import yaml

        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Override không hợp lệ (cần key=value): {item!r}")
        key, val = item.split("=", 1)
        data[key.strip()] = _coerce(val.strip())
    valid = {f.name for f in fields(ConfigTraining)}
    unknown = set(data) - valid
    if unknown:
        raise ValueError(f"Khoá cấu hình không hợp lệ: {sorted(unknown)}. Hợp lệ: {sorted(valid)}")
    return ConfigTraining(**data)



def _coerce(value: str) -> Any:
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value