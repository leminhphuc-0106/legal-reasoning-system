import sys

import fasttext
import joblib

from classifier_utils import (
    FASTTEXT_MODEL_PATH,
    LOGISTIC_MODEL_PATH,
    SVM_MODEL_PATH,
    TEST_PATH,
    TRAIN_PATH,
    evaluate_predictions,
    load_fasttext_data,
    predict_fasttext,
    print_comparison,
    train_logistic_regression,
    train_svm,
)

# Đảm bảo in tiếng Việt đúng trên Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Đọc dữ liệu kiểm thử dùng chung cho cả ba mô hình.
def load_test_data():
    X_test, y_test = load_fasttext_data(TEST_PATH)
    return X_test, y_test


# Đánh giá mô hình FastText đã lưu.
def evaluate_fasttext(X_test, y_test):
    if not FASTTEXT_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy mô hình FastText tại {FASTTEXT_MODEL_PATH}. "
            "Hãy chạy train.py trước."
        )

    model = fasttext.load_model(str(FASTTEXT_MODEL_PATH))
    y_pred = predict_fasttext(model, X_test)
    return evaluate_predictions(y_test, y_pred, "FastText")


# Đánh giá mô hình sklearn đã lưu; nếu chưa có thì huấn luyện lại.
def evaluate_sklearn_model(path, model_name, trainer, X_train, y_train, X_test, y_test):
    if path.exists():
        model = joblib.load(path)
        print(f"Đã nạp mô hình {model_name} từ: {path}")
    else:
        print(f"Chưa có mô hình {model_name}, tiến hành huấn luyện lại...")
        model = trainer(X_train, y_train)

    return evaluate_predictions(y_test, model.predict(X_test), model_name)


# Chạy đánh giá cả FastText, SVM và Logistic Regression trên cùng tập test.
def main():
    X_train, y_train = load_fasttext_data(TRAIN_PATH)
    X_test, y_test = load_test_data()

    print(f"Số mẫu huấn luyện: {len(X_train)}")
    print(f"Số mẫu kiểm thử   : {len(X_test)}")

    results = [
        evaluate_fasttext(X_test, y_test),
        evaluate_sklearn_model(
            SVM_MODEL_PATH,
            "SVM (TF-IDF + LinearSVC)",
            train_svm,
            X_train,
            y_train,
            X_test,
            y_test,
        ),
        evaluate_sklearn_model(
            LOGISTIC_MODEL_PATH,
            "Logistic Regression (TF-IDF)",
            train_logistic_regression,
            X_train,
            y_train,
            X_test,
            y_test,
        ),
    ]

    print_comparison(results)


if __name__ == "__main__":
    main()
