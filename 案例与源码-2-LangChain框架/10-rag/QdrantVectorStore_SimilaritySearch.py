"""
【案例】在 Qdrant 向量库中做相似性检索（similarity_search_with_score）

对应教程章节：第 19 章 - RAG 检索增强生成 → 2.1.3 再往后一步：检索案例和它们是什么关系；也可与第 18 章相似检索案例对照阅读

知识点速览：
- 这个案例对应的是 RAG 的检索阶段：前提是索引已经建好，现在要做的是“把相关内容查出来”。
- 相似性检索的核心流程是：查询文本先向量化，再到向量库中找到与查询向量最接近的若干条记录。
- `similarity_search_with_score(query, k)` 返回 `(Document, score)` 列表。
- 本例使用 Qdrant + COSINE + 归一化 BGE-M3 向量时，score 通常可理解为相似度，一般是越大越相似；请以实际返回为准，不要照搬其它库的“距离越小越相似”假设。
- 运行前需确保 Qdrant 中已有数据，例如先执行同目录下的 QdrantVectorStore_AddTexts.py；`collection_name`、`url` 与 embedding 模型也必须保持一致。
- 在完整 RAG 里，这一步通常不会直接把结果打印完就结束，而是会把查到的 `Document` 进一步组织进 Prompt，再交给 LLM 生成答案。

前置条件：本机已启动 Qdrant（http://localhost:6333），且已写入 collection=rag_newsgroups
模型卡片：https://huggingface.co/BAAI/bge-m3
"""

# pip install langchain-qdrant langchain-huggingface sentence-transformers torch
import os
from pathlib import Path

import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# 部分 conda 环境会把 SSL_CERT_FILE 指到不存在的 cacert.pem，导致 httpx/huggingface_hub/qdrant 客户端失败
_ssl_cert = os.environ.get("SSL_CERT_FILE")
if _ssl_cert and not Path(_ssl_cert).is_file():
    os.environ.pop("SSL_CERT_FILE", None)

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "rag_newsgroups"

# 1. 嵌入模型（与写入时一致，保证向量空间一致）
device = "cuda" if torch.cuda.is_available() else "cpu"
print("当前设备：", device, sep="")

embeddingsModel = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

# 2. 连接已有 collection（与 QdrantVectorStore_AddTexts.py 中 collection_name、url 一致）
vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddingsModel,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME,
)

# 3. 查询文本 → 向量化 → 在库中做相似度检索；这里取前 3 条结果
query = "我喜欢用什么手机"
results = vector_store.similarity_search_with_score(query, k=3)

print("=== 查询结果 ===")
for i, (doc, score) in enumerate(results, 1):
    # COSINE 模式下 score 一般越大越相似；这里直接打印原始 score，避免错误换算
    print(f"结果 {i}:")
    print(f"内容: {doc.page_content}")
    print(f"元数据: {doc.metadata}")
    print(f"score: {score:.4f}")

"""
【输出示例】
当前设备：cpu
=== 查询结果 ===
结果 1:
内容: 我喜欢用苹果手机
元数据: {'segment_id': '3', '_id': '...', '_collection_name': 'rag_newsgroups'}
score: 0.8678
结果 2:
内容: 我喜欢吃苹果
元数据: {'segment_id': '1', ...}
score: 0.6627
结果 3:
内容: 苹果是我最喜欢吃的水果
元数据: {'segment_id': '2', ...}
score: 0.6288
"""
