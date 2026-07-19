"""
【案例】将 Document 列表向量化并写入 Qdrant（BGE-M3 + langchain-qdrant）

对应教程章节：第 18 章 - 向量数据库与 Embedding 实战 → 6.1 案例：把 Document 列表写入向量库，再用检索器取回结果

知识点速览：
- 这是本章最贴近“向量库实战入口”的案例，演示的是：先准备 Document，再向量化，再写入 Qdrant，最后按相似度检索。
- QdrantVectorStore.from_documents() 会自动读取每个 Document 的 page_content，调用 embedding 做向量化，并把原文、向量、metadata 一起写入 Qdrant collection。
- as_retriever() 得到的是检索器；invoke(查询文本) 时，LangChain 会先把查询文本转成向量，再去库里找最相关的 Document。
- 这个案例是 RAG 的底层能力演示，不包含文档加载器、文本分割器和“检索后交给大模型生成答案”的完整流程。
- url 和 collection_name 要与本地环境一致；如果要复用已有 collection，查询端也必须使用同一个 collection_name，且 embedding 模型需与写入时一致。
- 嵌入模型使用本地 BGE-M3（dense 维度一般为 1024，距离度量用 COSINE，并开启 normalize_embeddings）。

前置条件：本机已启动 Qdrant，例如 Dashboard http://localhost:6333/dashboard
模型卡片：https://huggingface.co/BAAI/bge-m3
"""

# pip install langchain-qdrant langchain-huggingface sentence-transformers torch
import os
from pathlib import Path

import torch
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# 部分 conda 环境会把 SSL_CERT_FILE 指到不存在的 cacert.pem，导致 httpx/huggingface_hub/qdrant 客户端失败
_ssl_cert = os.environ.get("SSL_CERT_FILE")
if _ssl_cert and not Path(_ssl_cert).is_file():
    os.environ.pop("SSL_CERT_FILE", None)

# 1. 初始化嵌入模型（本地 BGE-M3）
device = "cuda" if torch.cuda.is_available() else "cpu"
print("当前设备：", device, sep="")

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

# 2. 构造 Document 列表：page_content 是正文，metadata 是附加信息
# 在完整 RAG 中，这些 Document 往往来自“加载器 + 分割器”；本案例先用手写数据聚焦理解向量库存取流程
texts = [
    "通义千问是阿里巴巴研发的大语言模型。",
    "Qdrant 是一个高性能的向量数据库，适合相似度检索。",
    "LangChain 可以轻松集成各种大模型和向量数据库。",
]
documents = [
    Document(page_content=text, metadata={"source": "manual"}) for text in texts
]

# 3. 一次性写入 Qdrant：内部会对每个 Document 的 page_content 做向量化，并创建/写入 collection
# force_recreate=True：每次运行重建 collection，避免维度/配置冲突；生产环境请改为 False 并复用已有库
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "embedding_demo"

vector_store = QdrantVectorStore.from_documents(
    documents=documents,
    embedding=embeddings,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME,
    force_recreate=True,
)
print("已写入 Qdrant：", QDRANT_URL, " collection=", COLLECTION_NAME, sep="")

# 4. 得到检索器：当你 invoke 查询文本时，LangChain 会先把问题向量化，再在库中做相似度检索
retriever = vector_store.as_retriever(search_kwargs={"k": 2})
results = retriever.invoke("LangChain 和向量数据库怎么结合？")
print("检索结果：")
for res in results:
    print("-", res.page_content)

"""
【输出示例】
当前设备：cpu
已写入 Qdrant：http://localhost:6333 collection=embedding_demo
检索结果：
- LangChain 可以轻松集成各种大模型和向量数据库。
- Qdrant 是一个高性能的向量数据库，适合相似度检索。
"""
