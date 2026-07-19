"""
【案例】使用 langchain_qdrant 将文本写入 Qdrant 向量库（add_texts）

对应教程章节：第 19 章 - RAG 检索增强生成 → 2.1.1 from_documents 与 add_texts；也可与第 18 章向量库写入案例对照阅读

知识点速览：
- 这个案例展示的是纯文本流驱动的入库路线：先创建 `QdrantVectorStore`，再通过 `add_texts()` 把字符串列表写入向量库。
- `add_texts(texts, metadatas)` 会在内部调用 `embed_documents(texts)` 做批量向量化，然后把文本、向量和 metadata 一起写入 Qdrant。
- 这条路线和 `from_documents(...)` 并不冲突：前者更适合你手里已经是纯文本列表，后者更适合你已经有 `Document` 列表。
- 本例里额外手动执行了一次 `embed_documents`，目的是先观察“向量长什么样、维度是多少”；真正做存储时，这一步不是必须的。
- 返回的 ids 可用于后续更新、删除或追踪；collection_name 需要和后续检索端保持一致。
- 嵌入模型使用本地 BGE-M3（dense 维度一般为 1024）；向量库为 Qdrant（默认 COSINE）。

前置条件：本机已启动 Qdrant，例如 Dashboard http://localhost:6333/dashboard
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

# 1. 初始化嵌入模型（本地 BGE-M3）
device = "cuda" if torch.cuda.is_available() else "cpu"
print("当前设备：", device, sep="")

embeddingsModel = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

# 2. 待写入的文本及（可选）元数据
texts = [
    "我喜欢吃苹果",
    "苹果是我最喜欢吃的水果",
    "我喜欢用苹果手机",
]

# 批量转成向量：这里只是为了先观察向量维度和内容；真正写入时 add_texts 内部会再次完成向量化
embeddings = embeddingsModel.embed_documents(texts)
for i, vec in enumerate(embeddings, 1):
    print(f"文本 {i}: {texts[i-1]}")
    print(f"向量长度: {len(vec)}")
    print(f"前10个向量值: {vec[:10]}\n")

# 定义每条文本对应的元数据信息；真实 RAG 中这些 metadata 往往来自 Document.metadata，也可作为来源展示或过滤条件
metadata = [{"segment_id": str(i)} for i in range(1, len(texts) + 1)]

# 3. 创建 Qdrant 向量存储实例：连上库并（可选择）重建 collection；真正写入发生在 add_texts()
# force_recreate=True：演示时每次从空库开始，避免旧数据干扰；生产环境请改为 False
vector_store = QdrantVectorStore.construct_instance(
    embedding=embeddingsModel,
    client_options={"url": QDRANT_URL},
    collection_name=COLLECTION_NAME,
    force_recreate=True,
)
print("已连接 Qdrant：", QDRANT_URL, " collection=", COLLECTION_NAME, sep="")

# 4. 将文本与元数据写入向量库（add_texts 内部会调 embed_documents，无需先算向量）
ids = vector_store.add_texts(texts, metadatas=metadata)

# 打印存储记录的 ID
print("写入 ids:", ids)

"""
【输出示例】
当前设备：cpu
文本 1: 我喜欢吃苹果
向量长度: 1024
前10个向量值: [...]

文本 2: 苹果是我最喜欢吃的水果
向量长度: 1024
前10个向量值: [...]

文本 3: 我喜欢用苹果手机
向量长度: 1024
前10个向量值: [...]

已连接 Qdrant：http://localhost:6333 collection=rag_newsgroups
写入 ids: [...]
"""
