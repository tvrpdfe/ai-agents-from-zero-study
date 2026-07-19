"""
【案例】LangChain 本地 BGE-M3 封装：单条与批量文本向量化

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 4.5 案例：用 LangChain 的统一接口做单条与批量向量化

知识点速览：
- 这个案例与 Text2Embedding_DashScope.py 的核心链路一致，变化的只是 Embedding 后端：从云端 DashScopeEmbeddings 换成本地 HuggingFaceEmbeddings(BAAI/bge-m3)。
- embed_query(text)：更偏“查询阶段”，常用于把用户问题转成向量。
- embed_documents(texts)：更偏“索引阶段”，常用于把文档片段批量转成向量。
- 返回值分别是“单个向量”和“向量列表”；BGE-M3 的 dense 维度一般为 1024，建索引和查询时应保持模型一致。
- 本示例只演示 dense 向量；BGE-M3 还支持 sparse / multi-vector（ColBERT）能力，不在此展开。
- 首次运行会从 HuggingFace 下载 BAAI/bge-m3（体积较大，需网络）。若访问受限，可先设置环境变量：
  HF_ENDPOINT=https://hf-mirror.com
- 设备自动选择：有 CUDA 用 cuda，否则 cpu。Windows + AMD 显卡当前官方 PyTorch 无稳定 ROCm 路径，通常会走 CPU。

模型卡片：https://huggingface.co/BAAI/bge-m3
"""

# pip install langchain-huggingface sentence-transformers torch
import os
from pathlib import Path

import torch
from langchain_huggingface import HuggingFaceEmbeddings

# 部分 conda 环境会把 SSL_CERT_FILE 指到不存在的 cacert.pem，导致 huggingface_hub/httpx 下载失败
_ssl_cert = os.environ.get("SSL_CERT_FILE")
if _ssl_cert and not Path(_ssl_cert).is_file():
    os.environ.pop("SSL_CERT_FILE", None)

# 自动选择设备：NVIDIA CUDA 可用时走 GPU，否则 CPU（Windows + AMD 一般会落到这里）
device = "cuda" if torch.cuda.is_available() else "cpu"
print("当前设备：", device, sep="")

# normalize_embeddings=True：输出 L2 归一化向量，后续做余弦相似度时更方便
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

text = "This is a test document."

# 单条文本 → 一个向量（列表）；这类写法更贴近“把用户问题转成查询向量”
query_result = embeddings.embed_query(text)
# sep=""：print 多个参数时用空字符串连接，默认是空格；这里让「文本向量长度：」和数字紧挨着输出，中间不留空
print("文本向量长度：", len(query_result), sep="")

# 多条文本 → 多个向量（列表的列表）；这类写法更贴近“批量建索引”
doc_results = embeddings.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!",
    ]
)
print(doc_results)
# sep=""：多个参数之间不加空格，输出如「文本向量数量：5，文本向量长度：1024」
print(
    "文本向量数量：", len(doc_results), "，文本向量长度：", len(doc_results[0]), sep=""
)

"""
【输出示例】
当前设备：cpu
文本向量长度：1024
[[...], [...], [...], [...], [...]]
文本向量数量：5，文本向量长度：1024
"""
