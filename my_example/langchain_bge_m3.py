"""
LangChain 1.x 中使用 BGE-M3 嵌入模型的示例

BGE-M3（BAAI General Embedding M3，智源研究院）：
  - 多语言（100+ 语言），最长支持 8192 token
  - 稠密向量维度 1024
  - 原生还支持稀疏（lexical）和多向量（ColBERT 风格）检索，
    但 LangChain 只封装了其稠密向量能力；稀疏/多向量需直接用 FlagEmbedding 库

LangChain 中使用 BGE-M3 的常见方式：
  方式一：langchain-huggingface 的 HuggingFaceEmbeddings（官方推荐，sentence-transformers 后端）
  方式二：HuggingFaceBgeEmbeddings（FlagEmbedding 后端，BGE 官方库，见文末注释）
  方式三：Ollama / Xinference / vLLM 等部署成 OpenAI 兼容接口后用 OpenAIEmbeddings（见文末注释）

运行前准备（方式一）：
  pip install -U langchain-huggingface sentence-transformers
  首次运行会自动从 HuggingFace 下载 BAAI/bge-m3（约 2.2GB）；
  国内下载慢可先设置镜像：set HF_ENDPOINT=https://hf-mirror.com
"""

import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings


# ---------------------------------------------------------------------------
# 0. 创建 Embeddings 实例
# ---------------------------------------------------------------------------
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},                  # 有 GPU 改成 "cuda"
        encode_kwargs={"normalize_embeddings": True},    # BGE 官方建议归一化：归一化后点积 = 余弦相似度
    )
    # 注意：BGE-M3 与 bge-large-zh 等旧型号不同，查询前不需要加指令前缀


# ---------------------------------------------------------------------------
# 1. 基础用法：embed_query / embed_documents + 余弦相似度
# ---------------------------------------------------------------------------
def demo_basic() -> None:
    embeddings = get_embeddings()

    query_vec = embeddings.embed_query("LangChain 是什么？")
    print(f"查询向量维度：{len(query_vec)}")             # 1024

    docs = [
        "LangChain 是一个用于构建大语言模型应用的框架。",
        "BGE-M3 是智源研究院发布的多语言嵌入模型。",
        "今天天气不错，适合出门散步。",
    ]
    doc_vecs = embeddings.embed_documents(docs)

    # 归一化后，点积即余弦相似度
    scores = [float(np.dot(query_vec, dv)) for dv in doc_vecs]
    for doc, score in zip(docs, scores):
        print(f"  相似度 {score:.4f}  {doc}")


# ---------------------------------------------------------------------------
# 2. 与向量库结合：InMemoryVectorStore（langchain-core 内置，零额外依赖）
#    生产环境可换成 FAISS / Chroma / Milvus 等，接口完全一致
# ---------------------------------------------------------------------------
def demo_vectorstore() -> None:
    from langchain_core.vectorstores import InMemoryVectorStore

    embeddings = get_embeddings()

    vectorstore = InMemoryVectorStore.from_texts(
        [
            "BGE-M3 支持超过 100 种语言的嵌入计算。",
            "BGE-M3 最长可以处理 8192 个 token 的文本。",
            "LangChain 1.x 推荐使用 create_agent 构建智能体。",
            "麻婆豆腐是四川的经典名菜。",
        ],
        embedding=embeddings,
    )

    # 2a. 直接相似度搜索（带分数）
    results = vectorstore.similarity_search_with_score("bge-m3 能处理多长的文本？", k=2)
    print("相似度搜索结果：")
    for doc, score in results:
        print(f"  分数 {score:.4f}  {doc.page_content}")

    # 2b. 作为 Retriever 使用（可直接接入 RAG chain / agent 的 tool）
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    docs = retriever.invoke("bge-m3 支持多少种语言？")
    print("Retriever 召回：")
    for doc in docs:
        print(f"  {doc.page_content}")


# ---------------------------------------------------------------------------
# 方式二：HuggingFaceBgeEmbeddings（FlagEmbedding 后端）
#   pip install -U langchain-community FlagEmbedding
#
#   from langchain_community.embeddings import HuggingFaceBgeEmbeddings
#   embeddings = HuggingFaceBgeEmbeddings(
#       model_name="BAAI/bge-m3",
#       model_kwargs={"device": "cpu"},
#       encode_kwargs={"normalize_embeddings": True},
#   )
#
# 方式三：OpenAI 兼容接口（Xinference / vLLM / Ollama 部署 bge-m3 时）
#   pip install -U langchain-openai
#
#   from langchain_openai import OpenAIEmbeddings
#   embeddings = OpenAIEmbeddings(
#       model="bge-m3",
#       base_url="http://localhost:9997/v1",   # 以 Xinference 为例
#       api_key="not-needed",
#   )
#
# 提示：BGE-M3 的稀疏 / 多向量混合检索能力，LangChain 未封装，
#       需要时直接用 FlagEmbedding 的 BGEM3FlagModel。
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 20, "1. 基础嵌入与相似度", "=" * 20)
    demo_basic()
    print("=" * 20, "2. 向量库与检索器", "=" * 20)
    demo_vectorstore()
