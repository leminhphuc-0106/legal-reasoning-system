import sys

from classifier_utils import (
    LOGISTIC_MODEL_PATH,
    SVM_MODEL_PATH,
    TRAIN_PATH,
    TEST_PATH,
    evaluate_predictions,
    load_fasttext_data,
    save_model,
    train_logistic_regression,
    train_svm,
)

# Đảm bảo in tiếng Việt đúng trên Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Huấn luyện và đánh giá hai mô hình SVM và Logistic Regression.
def main():
    X_train, y_train = load_fasttext_data(TRAIN_PATH)
    X_test, y_test = load_fasttext_data(TEST_PATH)

    print(f"Số mẫu huấn luyện: {len(X_train)}")
    print(f"Số mẫu kiểm thử   : {len(X_test)}")

    # Huấn luyện và đánh giá SVM trên tập kiểm thử.
    svm_model = train_svm(X_train, y_train)
    save_model(svm_model, SVM_MODEL_PATH)
    evaluate_predictions(y_test, svm_model.predict(X_test), "SVM (TF-IDF + LinearSVC)")

    # Huấn luyện và đánh giá Logistic Regression trên tập kiểm thử.
    logistic_model = train_logistic_regression(X_train, y_train)
    save_model(logistic_model, LOGISTIC_MODEL_PATH)
    evaluate_predictions(
        y_test,
        logistic_model.predict(X_test),
        "Logistic Regression (TF-IDF)",
    )


if __name__ == "__main__":
    main()
