"""
【案例】通过向量计算语义相似度：余弦相似度（本地 BGE-M3）

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 5.2 案例：把多句话转成向量，再两两比较

知识点速览：
- 这个案例的重点不是特定模型，而是“向量一旦拿到手，就可以做数学比较”，这是语义检索的底层基础。
- 文本转成向量后，可用余弦相似度衡量两段文本的语义是否接近：值通常在 [-1, 1]，越接近 1 一般表示越相似。
- 公式：cos(theta) = (A·B) / (|A||B|)；在 Python 里常用 np.dot 和 np.linalg.norm 实现。
- 相似度比较常用于检索排序、文本去重、聚类、推荐等任务。
- 本文件后端使用本地 BGE-M3（HuggingFaceEmbeddings）；与云端 DashScope 版接口不同，但“向量 → 余弦相似度”的比较逻辑相同。
- encode_kwargs 里 normalize_embeddings=True 时，向量已 L2 归一化，此时余弦相似度等价于点积；下面仍按完整公式手写，便于对照教程。

模型卡片：https://huggingface.co/BAAI/bge-m3
"""

# pip install langchain-huggingface sentence-transformers torch numpy
import os
from pathlib import Path

import numpy as np
import torch
from langchain_huggingface import HuggingFaceEmbeddings

# 部分 conda 环境会把 SSL_CERT_FILE 指到不存在的 cacert.pem，导致 huggingface_hub/httpx 下载失败
_ssl_cert = os.environ.get("SSL_CERT_FILE")
if _ssl_cert and not Path(_ssl_cert).is_file():
    os.environ.pop("SSL_CERT_FILE", None)

# 准备多句文本，用于观察“语义越接近，相似度通常越高”
texts = ["我喜欢吃苹果", "苹果是我最喜欢吃的水果", "我喜欢用苹果手机"]

# 自动选择设备：NVIDIA CUDA 可用时走 GPU，否则 CPU（Windows + AMD 一般会落到这里）
device = "cuda" if torch.cuda.is_available() else "cpu"
print("当前设备：", device, sep="")

# 本地 BGE-M3：批量把多句文本转成 dense 向量
embeddings_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)
embeddings = embeddings_model.embed_documents(texts)


def cosine_similarity(vec1, vec2):
    """计算两个向量的余弦相似度：点积 / (模长之积)，结果越接近 1 一般越相似"""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)


print("文本相似度比较结果:")
print("=" * 60)

for i in range(len(texts)):
    for j in range(i + 1, len(texts)):
        similarity = cosine_similarity(embeddings[i], embeddings[j])
        print(f"文本{i+1} vs 文本{j+1}:")
        print(f"  文本{i+1}: {texts[i]}")
        print(f"  文本{j+1}: {texts[j]}")
        print(f"  余弦相似度: {similarity:.4f}")
        print("-" * 40)

"""
【输出示例】
当前设备：cpu
文本相似度比较结果:
============================================================
文本1 vs 文本2:
  文本1: 我喜欢吃苹果
  文本2: 苹果是我最喜欢吃的水果
  余弦相似度: 0.8833
----------------------------------------
文本1 vs 文本3:
  文本1: 我喜欢吃苹果
  文本3: 我喜欢用苹果手机
  余弦相似度: 0.8629
----------------------------------------
文本2 vs 文本3:
  文本2: 苹果是我最喜欢吃的水果
  文本3: 我喜欢用苹果手机
  余弦相似度: 0.7740
----------------------------------------
# 相对关系：文本1 vs 文本2（都关于吃苹果）最高；涉及“苹果手机”的两对更低
"""
