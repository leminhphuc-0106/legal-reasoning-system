#Kiểm tra fast text và numpy
import numpy as np
print(np.__version__)

import fasttext
print("FastText OK")


data_path = "./Train-FastText-Model/data/train.txt"

model = fasttext.train_supervised(
    input=data_path,
    epoch=50,
    lr=0.2,
    wordNgrams=2,
    dim=100,
    loss="softmax",
    verbose=2
)

model.save_model("./Models/Fast_text_model/fast_text_model.bin")


test_path = "./Train-FastText-Model/data/test.txt"
result = model.test(test_path)

print("Samples :", result[0])
print("Precision:", result[1])
print("Recall   :", result[2])

print(result)