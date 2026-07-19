# 参考：用本地 BGE-M3 做文本向量化

本文是一份**通用参考**，说明如何用开源模型 **BAAI/bge-m3** 完成本地文本 Embedding。  
不绑定某一云厂商 SDK；你原先用的是 DashScope、OpenAI、自建服务还是其它 API，都可以按同样思路替换。

## 1. 适用场景

- 希望**不依赖云端 Embedding API**，在本机或内网完成向量化
- 需要和 LangChain 检索器 / 向量库对接，统一使用 `embed_query` / `embed_documents`
- 后续要做余弦相似度、语义检索、去重、聚类等

不在本文范围：

- BGE-M3 的 sparse / multi-vector（ColBERT）混合检索
- 远程 TEI、Xinference、vLLM 等服务化部署（思路类似，加载方式不同）

## 2. 技术选型建议

| 项 | 建议 |
|----|------|
| 模型 | `BAAI/bge-m3` |
| dense 维度 | 一般为 **1024**（建库与查询必须用同一模型） |
| LangChain 封装 | `langchain_huggingface.HuggingFaceEmbeddings` |
| 底层 | `sentence-transformers` + `torch` |
| 归一化 | `encode_kwargs={"normalize_embeddings": True}`，便于余弦相似度 |
| 设备 | 有 NVIDIA CUDA 用 `cuda`，否则 `cpu` |

### 设备说明（简要）

- **NVIDIA + CUDA 版 PyTorch**：可走 GPU
- **仅 CPU / Windows 默认 torch wheel**：走 CPU，功能正常，大批量会慢一些
- **Windows + AMD**：官方 PyTorch 通常无稳定 ROCm 路径，多数情况落到 CPU；Linux + ROCm 另作环境配置

## 3. 依赖

```text
langchain-huggingface>=0.1
sentence-transformers>=3.0
torch>=2.0
numpy   # 若要手写余弦相似度等
```

安装示例：

```bash
pip install "langchain-huggingface>=0.1" "sentence-transformers>=3.0" "torch>=2.0"
```

> Python 环境请按你自己的项目规范选择（venv / conda 等）。首次运行会从 Hugging Face 下载模型，需网络；已缓存后再次加载会快很多。

### 可选：Hugging Face 访问

- **镜像**（访问 Hub 困难时）：

  ```bash
  # Linux / macOS
  export HF_ENDPOINT=https://hf-mirror.com
  # Windows CMD
  set HF_ENDPOINT=https://hf-mirror.com
  ```

- **Token**（消除匿名访问警告、提高限额）：到 Hugging Face 创建 read token，设置环境变量 `HF_TOKEN`。
- **SSL**：若环境变量 `SSL_CERT_FILE` 指向不存在的证书文件，可能导致下载失败；删掉该变量或改成有效路径即可。

## 4. 最小示例：单条与批量向量化

把「任意旧 Embedding 后端」换成 BGE-M3 时，对外尽量保持同一套接口：

```python
import torch
from langchain_huggingface import HuggingFaceEmbeddings

device = "cuda" if torch.cuda.is_available() else "cpu"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": device},
    encode_kwargs={"normalize_embeddings": True},
)

# 查询阶段：一句话 → 一个向量
query_vec = embeddings.embed_query("This is a test document.")
print(len(query_vec))  # 期望 1024

# 索引阶段：多段文本 → 多个向量
doc_vecs = embeddings.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "Hello World!",
    ]
)
print(len(doc_vecs), len(doc_vecs[0]))
```

迁移时通常只需改 **创建 `embeddings` 对象** 的那几行；后面的检索器、向量库、相似度计算可以不动。

## 5. 从其它后端迁移的通用步骤

1. **确认依赖**：安装 `langchain-huggingface`、`sentence-transformers`、`torch`
2. **替换客户端创建逻辑**：删除原云 API Key / base_url / SDK 调用，改为上一节的 `HuggingFaceEmbeddings(...)`
3. **统一调用面**：继续用 `embed_query` / `embed_documents`，避免业务代码绑死某一厂商
4. **核对维度**：打印 `len(vector)`，与旧索引维度不一致时需**重建向量库**
5. **设备与性能**：先 CPU 跑通，再按机器条件考虑 GPU / 服务化
6. **缓存与网络**：首次下载模型；之后可离线加载（需保证 cache 仍在）

## 6. 常见现象

| 现象 | 说明 |
|------|------|
| `Loading weights: 100%` 每次都出现 | 进程启动时从本地 cache 载入权重，属正常，不等于每次重新下载 |
| `unauthenticated requests to the HF Hub` | 未设置 `HF_TOKEN` 的提示，一般不影响已缓存模型的本地推理 |
| 速度慢 | CPU 推理或首次下载；可考虑 GPU、批量 `embed_documents`、服务化部署 |
| 与旧云模型分数对不上 | 不同模型向量空间不同，只比较**同一模型**下的相对关系 |

## 7. 参考链接

- 模型卡片：https://huggingface.co/BAAI/bge-m3
- LangChain HuggingFace 集成：以当前安装的 `langchain-huggingface` 文档为准
