from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

# Đường dẫn dùng chung cho các script huấn luyện và đánh giá.
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
DATA_DIR = BASE_DIR / "data"
TRAIN_PATH = DATA_DIR / "train.txt"
TEST_PATH = DATA_DIR / "test.txt"
MODEL_DIR = PROJECT_ROOT / "models"
FASTTEXT_MODEL_PATH = MODEL_DIR / "Fast_text_model" / "fast_text_model.bin"
SVM_MODEL_PATH = MODEL_DIR / "SVM_Model" / "svm_model.joblib"
LOGISTIC_MODEL_PATH = MODEL_DIR / "Logistic_Regression_Model" / "logistic_regression_model.joblib"

# Thứ tự nhãn cố định để confusion matrix luôn hiển thị giống nhau.
LABEL_ORDER = ["KEEP", "DROP"]


# Đọc dữ liệu định dạng FastText: mỗi dòng là "__label__NHAN nội dung câu".
def load_fasttext_data(path):
    texts, labels = [], []

    with open(path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            parts = line.split(maxsplit=1)
            if len(parts) != 2 or not parts[0].startswith("__label__"):
                continue

            labels.append(parts[0].replace("__label__", ""))
            texts.append(parts[1])

    return texts, labels


# Tạo bộ vector hóa TF-IDF dùng chung cho SVM và Logistic Regression.
def build_vectorizer():
    return TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )


# Huấn luyện mô hình SVM tuyến tính trên đặc trưng TF-IDF.
def train_svm(texts, labels):
    model = Pipeline([
        ("tfidf", build_vectorizer()),
        ("svm", LinearSVC(class_weight="balanced", random_state=42)),
    ])
    model.fit(texts, labels)
    return model


# Huấn luyện mô hình Logistic Regression trên đặc trưng TF-IDF.
def train_logistic_regression(texts, labels):
    model = Pipeline([
        ("tfidf", build_vectorizer()),
        ("logistic", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])
    model.fit(texts, labels)
    return model


# Lưu mô hình đã huấn luyện xuống thư mục models.
def save_model(model, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    print(f"Đã lưu mô hình tại: {path}")


# Lấy nhãn dự đoán từ mô hình FastText (hỗ trợ cả dự đoán theo lô).
def predict_fasttext(model, texts):
    labels, _ = model.predict(list(texts), k=1)
    return [
        (label[0] if isinstance(label, (list, tuple)) else label).replace("__label__", "")
        for label in labels
    ]


# In confusion matrix dạng bảng chữ để dễ đọc trên terminal.
def print_confusion_matrix(matrix, labels):
    print("Confusion matrix (hàng = thực tế, cột = dự đoán):")
    header = " " * 18 + "".join(f"{label:>10}" for label in labels)
    print(header)

    for label, row in zip(labels, matrix):
        values = "".join(f"{value:>10}" for value in row)
        print(f"{'Thực tế ' + label:<18}{values}")


# Tính và in đầy đủ confusion matrix, precision, recall, f1 cho một mô hình.
def evaluate_predictions(y_true, y_pred, model_name, labels=None):
    labels = labels or LABEL_ORDER

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    accuracy = accuracy_score(y_true, y_pred)
    macro = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )

    print("\n" + "=" * 70)
    print(f"KẾT QUẢ ĐÁNH GIÁ: {model_name}")
    print("=" * 70)

    print_confusion_matrix(matrix, labels)

    print("\nBáo cáo chi tiết theo từng nhãn:")
    print(classification_report(
        y_true, y_pred, labels=labels, digits=4, zero_division=0
    ))

    print("Chỉ số tổng hợp:")
    print(f"  Accuracy          : {accuracy:.4f}")
    print(f"  Precision (macro) : {macro[0]:.4f}")
    print(f"  Recall    (macro) : {macro[1]:.4f}")
    print(f"  F1-score  (macro) : {macro[2]:.4f}")
    print(f"  Precision (weighted): {weighted[0]:.4f}")
    print(f"  Recall    (weighted): {weighted[1]:.4f}")
    print(f"  F1-score  (weighted): {weighted[2]:.4f}")

    return {
        "model": model_name,
        "accuracy": accuracy,
        "precision_macro": macro[0],
        "recall_macro": macro[1],
        "f1_macro": macro[2],
        "precision_weighted": weighted[0],
        "recall_weighted": weighted[1],
        "f1_weighted": weighted[2],
        "confusion_matrix": matrix.tolist(),
    }


# In bảng so sánh nhanh các chỉ số của nhiều mô hình.
def print_comparison(results):
    print("\n" + "=" * 70)
    print("BẢNG SO SÁNH CÁC MÔ HÌNH")
    print("=" * 70)
    print(f"{'Mô hình':<34}{'Accuracy':>10}{'Precision':>12}{'Recall':>10}{'F1':>10}")

    for item in results:
        print(
            f"{item['model']:<34}"
            f"{item['accuracy']:>10.4f}"
            f"{item['precision_macro']:>12.4f}"
            f"{item['recall_macro']:>10.4f}"
            f"{item['f1_macro']:>10.4f}"
        )
