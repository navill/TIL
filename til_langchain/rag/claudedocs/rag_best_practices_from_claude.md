# RAG (Retrieval-Augmented Generation) 모범 사례 가이드

> LangChain을 활용한 프로덕션 수준의 RAG 시스템 구축 가이드

## 목차
1. [RAG 시스템 아키텍처 개요](#1-rag-시스템-아키텍처-개요)
2. [청킹 전략](#2-청킹-전략)
3. [임베딩 모델 선택](#3-임베딩-모델-선택)
4. [벡터 스토어 비교](#4-벡터-스토어-비교)
5. [검색 전략](#5-검색-전략)
6. [프롬프트 엔지니어링](#6-프롬프트-엔지니어링)
7. [성능 최적화](#7-성능-최적화)
8. [일반적인 문제와 해결책](#8-일반적인-문제와-해결책)
9. [프로덕션 배포 체크리스트](#9-프로덕션-배포-체크리스트)

---

## 1. RAG 시스템 아키텍처 개요

### 1.1 RAG란 무엇인가?

RAG(Retrieval-Augmented Generation)는 LLM의 응답 생성 시 외부 지식 베이스에서 관련 정보를 검색하여 컨텍스트로 제공하는 기법입니다.

**핵심 장점:**
- **최신 정보 활용**: LLM 학습 이후 데이터도 활용 가능
- **환각(Hallucination) 감소**: 실제 문서 기반 응답으로 신뢰성 향상
- **출처 추적**: 응답의 근거가 되는 문서 확인 가능
- **도메인 특화**: 특정 분야의 전문 지식 제공
- **비용 효율적**: 전체 모델 파인튜닝보다 저렴

### 1.2 RAG 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 파이프라인                             │
└─────────────────────────────────────────────────────────────┘

[데이터 준비 단계] (오프라인)
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 문서 로드     │ -> │ 문서 분할     │ -> │ 임베딩 생성   │
│ (Loaders)    │    │ (Splitters)  │    │ (Embeddings) │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              v
                                    ┌──────────────────┐
                                    │  벡터 스토어      │
                                    │ (Vector Store)   │
                                    └──────────────────┘

[쿼리 처리 단계] (온라인)
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 사용자 질의   │ -> │ 문서 검색     │ -> │ 컨텍스트 구성 │
└──────────────┘    │ (Retriever)  │    └──────────────┘
                    └──────────────┘           │
                                              v
                    ┌──────────────────────────────┐
                    │  프롬프트 + 컨텍스트 + 질의   │
                    └──────────────────────────────┘
                                   │
                                   v
                    ┌──────────────┐    ┌──────────────┐
                    │    LLM       │ -> │   최종 답변   │
                    └──────────────┘    └──────────────┘
```

### 1.3 기본 구현 예제

```python
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 문서 로드
loader = TextLoader("data/documents.txt")
documents = await loader.aload()

# 2. 문서 분할
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)
splits = await text_splitter.atransform_documents(documents)

# 3. 벡터 스토어 생성
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = await FAISS.afrom_documents(splits, embeddings)

# 4. 리트리버 생성
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. RAG 체인 구성
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

template = """다음 문맥을 기반으로 질문에 답변하세요:

{context}

질문: {question}
답변:"""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 6. 실행
result = await rag_chain.ainvoke("질문을 입력하세요")
```

---

## 2. 청킹 전략

### 2.1 청킹이란?

청킹(Chunking)은 긴 문서를 작은 단위로 분할하는 과정입니다. 적절한 청킹은 RAG 성능에 결정적 영향을 미칩니다.

### 2.2 청킹 매개변수

#### chunk_size (청크 크기)

**권장 범위: 200-1000 문자**

| 크기 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 작음 (100-300) | 정확한 검색, 빠른 처리 | 문맥 손실, 많은 청크 수 | 정형 데이터, FAQ, 용어집 |
| 중간 (400-800) | 균형잡힌 성능 | - | 일반 문서, 기사, 보고서 |
| 큼 (900-1500) | 풍부한 문맥, 적은 청크 수 | 느린 검색, 불필요한 정보 포함 | 긴 서사, 소설, 법률 문서 |

**설정 가이드:**
```python
# 짧은 정형 데이터 (FAQ, 용어집)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=20
)

# 일반 문서 (기본 권장)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

# 긴 서사 문서 (소설, 긴 리포트)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
```

#### chunk_overlap (청크 중첩)

**권장 비율: chunk_size의 10-20%**

```python
# 규칙: overlap = chunk_size * 0.1 ~ 0.2
chunk_size = 500
chunk_overlap = 50   # 10% - 최소 문맥 보존
chunk_overlap = 100  # 20% - 권장 (기본값)
chunk_overlap = 150  # 30% - 최대 문맥 보존 (중복 증가)
```

**중첩이 중요한 이유:**
- 청크 경계에서 문장이 잘리는 문제 방지
- 앞뒤 문맥 정보 보존
- 검색 정확도 향상

### 2.3 청킹 전략 비교

#### 2.3.1 RecursiveCharacterTextSplitter (권장)

**특징:** 계층적 구분자 시도 (`\n\n` → `\n` → ` ` → 문자)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
    separators=["\n\n", "\n", " ", ""]  # 우선순위 순
)
```

**장점:**
- 대부분의 경우 최적의 결과
- 의미 단위 보존 (문단 → 문장 → 단어)
- 다양한 문서 형식에 범용적으로 적용

**사용 예:**
- 일반 텍스트, 마크다운, 기사, 보고서
- 구조화된 문서

#### 2.3.2 CharacterTextSplitter

**특징:** 단일 구분자 기반 분할

```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    separator="\n\n",  # 빈 줄 기준
    chunk_size=500,
    chunk_overlap=50
)
```

**장점:**
- 간단하고 빠름
- 명확한 구조의 문서에 적합

**단점:**
- 문맥 고려 부족
- 구분자가 없으면 비효율적

**사용 예:**
- 명확히 구분된 섹션이 있는 문서
- CSV, 로그 파일

#### 2.3.3 TokenTextSplitter

**특징:** LLM 토큰 수 기준 분할

```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=200,  # 토큰 수
    chunk_overlap=20
)
```

**장점:**
- LLM 토큰 제한을 정확히 준수
- 입력 길이 예측 가능

**단점:**
- 토큰화 오버헤드
- 느린 처리 속도

**사용 예:**
- 토큰 제한이 엄격한 LLM 사용 시
- GPT-3.5 (4k 제한), Claude (100k 제한) 등

#### 2.3.4 도메인 특화 Splitter

```python
# 마크다운 문서
from langchain_text_splitters import MarkdownHeaderTextSplitter

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)

# Python 코드
from langchain_text_splitters import PythonCodeTextSplitter

python_splitter = PythonCodeTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

# HTML 문서
from langchain_text_splitters import HTMLHeaderTextSplitter

html_splitter = HTMLHeaderTextSplitter(
    headers_to_split_on=[
        ("h1", "Header 1"),
        ("h2", "Header 2"),
    ]
)
```

### 2.4 청킹 최적화 실무 팁

#### 1. 문서 타입별 전략

```python
def get_splitter_for_document_type(doc_type: str):
    """문서 타입에 따른 최적 Splitter 반환"""

    if doc_type == "markdown":
        return MarkdownHeaderTextSplitter(...)

    elif doc_type == "code":
        return PythonCodeTextSplitter(...)

    elif doc_type == "long_narrative":
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    elif doc_type == "qa_pairs":
        return RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=20
        )

    else:  # 기본값
        return RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
```

#### 2. 동적 청크 크기 조정

```python
async def adaptive_chunking(document, target_chunks=50):
    """문서 크기에 따라 청크 크기 자동 조정"""

    doc_length = len(document.page_content)
    optimal_chunk_size = max(200, min(1000, doc_length // target_chunks))
    optimal_overlap = int(optimal_chunk_size * 0.15)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=optimal_chunk_size,
        chunk_overlap=optimal_overlap
    )

    return await splitter.atransform_documents([document])
```

#### 3. 청크 품질 검증

```python
def validate_chunks(chunks):
    """청크 품질 검증"""

    issues = []

    for i, chunk in enumerate(chunks):
        content = chunk.page_content

        # 너무 짧은 청크
        if len(content) < 50:
            issues.append(f"청크 {i}: 너무 짧음 ({len(content)} 문자)")

        # 완전하지 않은 문장
        if not content.strip().endswith(('.', '!', '?', '다', '요')):
            issues.append(f"청크 {i}: 불완전한 문장")

        # 중복 확인
        for j in range(i+1, len(chunks)):
            if content == chunks[j].page_content:
                issues.append(f"청크 {i}와 {j}: 완전 중복")

    return issues
```

---

## 3. 임베딩 모델 선택

### 3.1 임베딩이란?

임베딩은 텍스트를 고차원 벡터로 변환하여 의미적 유사도를 계산할 수 있게 하는 기술입니다.

### 3.2 주요 임베딩 모델 비교

| 모델 | 차원 | 최대 토큰 | 성능 | 비용 | 언어 지원 |
|------|------|----------|------|------|-----------|
| **text-embedding-3-small** | 1536 | 8191 | 중상 | 낮음 | 다국어 |
| **text-embedding-3-large** | 3072 | 8191 | 최상 | 중간 | 다국어 |
| **gemini-embedding-001** | 768 | 2048 | 중상 | 무료* | 다국어 |
| **cohere-embed-multilingual-v3** | 1024 | 512 | 상 | 중간 | 100개 언어 |
| **sentence-transformers** | 384-1024 | 512 | 중 | 무료 | 다국어 |

*무료 할당량 내

### 3.3 임베딩 모델 선택 기준

#### 1. 언어 지원
```python
# 한국어에 강한 모델
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

# 다국어 지원 (100개 언어)
from langchain_cohere import CohereEmbeddings
embeddings = CohereEmbeddings(
    model="embed-multilingual-v3.0"
)
```

#### 2. 도메인 특화
```python
# 코드 임베딩
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"  # 코드 이해 우수
)

# 의료/법률 등 전문 분야
# 파인튜닝된 모델 사용 권장
```

#### 3. 비용 대비 성능
```python
# 프로토타입/개발: 무료 모델
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

# 프로덕션: 성능 우선
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"
)
```

### 3.4 임베딩 최적화 기법

#### 1. 배치 처리
```python
# 비효율적: 개별 임베딩
for doc in documents:
    embedding = await embeddings.aembed_documents([doc.page_content])

# 효율적: 배치 임베딩
texts = [doc.page_content for doc in documents]
embeddings_batch = await embeddings.aembed_documents(texts)
```

#### 2. 캐싱
```python
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

# 로컬 캐시 스토어
store = LocalFileStore("./embedding_cache")

# 캐시가 적용된 임베딩 모델
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings=embeddings,
    document_embedding_cache=store,
    namespace="my_documents"
)

# 동일한 문서는 캐시에서 로드 (API 호출 절약)
vectorstore = await FAISS.afrom_documents(
    documents,
    cached_embeddings
)
```

#### 3. 차원 축소
```python
# OpenAI 임베딩 차원 축소 (3072 → 1024)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1024  # 기본 3072에서 축소
)

# 장점: 저장 공간 66% 절약, 검색 속도 향상
# 단점: 약간의 정확도 감소 (보통 1-2%)
```

---

## 4. 벡터 스토어 비교

### 4.1 주요 벡터 스토어 비교표

| 벡터 스토어 | 타입 | 확장성 | 속도 | 필터링 | 클라우드 | 가격 | 권장 용도 |
|------------|------|-------|------|--------|---------|------|----------|
| **FAISS** | 로컬 | 중간 | 매우 빠름 | 제한적 | X | 무료 | 개발, 프로토타입 |
| **Chroma** | 로컬/서버 | 중간 | 빠름 | 좋음 | △ | 무료/유료 | 중소규모 |
| **Pinecone** | 클라우드 | 높음 | 빠름 | 우수 | O | 유료 | 프로덕션(대규모) |
| **Weaviate** | 서버/클라우드 | 높음 | 빠름 | 우수 | O | 무료/유료 | 프로덕션 |
| **Qdrant** | 서버/클라우드 | 높음 | 매우 빠름 | 우수 | O | 무료/유료 | 프로덕션 |
| **Milvus** | 서버/클라우드 | 매우 높음 | 빠름 | 우수 | O | 무료/유료 | 엔터프라이즈 |

### 4.2 벡터 스토어별 상세 가이드

#### 4.2.1 FAISS (Facebook AI Similarity Search)

**최적 사용 사례:**
- 로컬 개발 및 프로토타입
- 중소 규모 데이터셋 (< 100만 벡터)
- 빠른 검색 속도가 중요한 경우

```python
from langchain_community.vectorstores import FAISS, DistanceStrategy

# 생성
vectorstore = await FAISS.afrom_documents(
    documents,
    embeddings,
    distance_strategy=DistanceStrategy.COSINE  # COSINE, EUCLIDEAN_DISTANCE, MAX_INNER_PRODUCT
)

# 저장
vectorstore.save_local("./faiss_index")

# 로드
vectorstore = FAISS.load_local(
    "./faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# 검색
results = await vectorstore.asimilarity_search("query", k=5)
```

**장점:**
- 무료, 설치 간단
- 매우 빠른 검색 속도
- 다양한 인덱스 타입 지원

**단점:**
- 복잡한 메타데이터 필터링 제한
- 클라우드 동기화 없음
- 대규모 확장 어려움

#### 4.2.2 Chroma

**최적 사용 사례:**
- 중소 규모 프로덕션 (< 100만 벡터)
- 메타데이터 필터링이 중요한 경우
- 로컬과 클라우드 모두 필요한 경우

```python
from langchain_community.vectorstores import Chroma

# 로컬 저장
vectorstore = await Chroma.afrom_documents(
    documents,
    embeddings,
    persist_directory="./chroma_db"
)

# 메타데이터 필터링
results = await vectorstore.asimilarity_search(
    "query",
    k=5,
    filter={"category": "history", "year": {"$gte": 1900}}
)

# 하이브리드 검색 (유사도 + 키워드)
results = vectorstore.similarity_search(
    "query",
    k=5,
    filter={"$and": [
        {"category": "history"},
        {"$text": {"$search": "keyword"}}
    ]}
)
```

**장점:**
- 우수한 메타데이터 필터링
- 로컬 및 클라이언트-서버 모드
- 오픈소스, 무료

**단점:**
- 대규모 확장 제한적
- FAISS보다 느림

#### 4.2.3 Pinecone

**최적 사용 사례:**
- 대규모 프로덕션 (수백만~수억 벡터)
- 완전 관리형 서비스 필요
- 글로벌 배포

```python
from langchain_community.vectorstores import Pinecone
import pinecone

# 초기화
pinecone.init(
    api_key="your-api-key",
    environment="us-west1-gcp"
)

# 인덱스 생성 (최초 1회)
pinecone.create_index(
    name="my-index",
    dimension=768,
    metric="cosine",
    pod_type="p1.x1"  # 성능 계층 선택
)

# 벡터 스토어 생성
vectorstore = await Pinecone.afrom_documents(
    documents,
    embeddings,
    index_name="my-index"
)

# 하이브리드 검색
results = await vectorstore.asimilarity_search(
    "query",
    k=5,
    filter={"category": {"$eq": "history"}}
)
```

**장점:**
- 완전 관리형 (인프라 걱정 없음)
- 무제한 확장
- 우수한 필터링 및 하이브리드 검색

**단점:**
- 비용 (스토리지 및 쿼리 기반)
- 클라우드 종속

#### 4.2.4 Weaviate

**최적 사용 사례:**
- 엔터프라이즈 프로덕션
- 복잡한 필터링 및 하이브리드 검색
- GraphQL API 필요

```python
from langchain_community.vectorstores import Weaviate
import weaviate

# 클라이언트 생성
client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={"X-OpenAI-Api-Key": "your-key"}
)

# 벡터 스토어 생성
vectorstore = Weaviate(
    client=client,
    index_name="MyDocument",
    text_key="content",
    embedding=embeddings
)

# 하이브리드 검색 (벡터 + BM25)
results = vectorstore.similarity_search(
    "query",
    k=5,
    alpha=0.5  # 0=BM25만, 1=벡터만, 0.5=균형
)

# 복잡한 필터링
results = vectorstore.similarity_search(
    "query",
    k=5,
    where_filter={
        "path": ["category"],
        "operator": "Equal",
        "valueText": "history"
    }
)
```

**장점:**
- 강력한 하이브리드 검색
- GraphQL API
- 오픈소스 + 클라우드 옵션

**단점:**
- 설정 복잡도 높음
- 리소스 사용량 많음

### 4.3 거리 측정 방식 선택

#### Cosine Similarity (코사인 유사도) - 권장

```python
vectorstore = FAISS.from_documents(
    documents,
    embeddings,
    distance_strategy=DistanceStrategy.COSINE
)
```

**특징:**
- 벡터 간 각도 측정 (방향 비교)
- 크기 정규화됨
- 대부분의 경우 최적

**사용 시기:**
- 일반 텍스트 검색
- 의미적 유사도 중요
- 임베딩 모델 대부분이 코사인에 최적화

#### Euclidean Distance (유클리드 거리)

```python
distance_strategy=DistanceStrategy.EUCLIDEAN_DISTANCE
```

**특징:**
- 벡터 간 직선 거리
- 크기 차이 민감

**사용 시기:**
- 벡터 크기가 의미있는 경우
- 이미지 임베딩
- 특수 도메인

#### Inner Product (내적)

```python
distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT
```

**특징:**
- 벡터 내적 계산
- 정규화 안됨

**사용 시기:**
- 특정 모델이 내적에 최적화된 경우
- 추천 시스템

**권장 사항:** 특별한 이유가 없다면 **코사인 유사도** 사용

---

## 5. 검색 전략

### 5.1 기본 검색 방법

#### 5.1.1 유사도 검색 (Similarity Search)

가장 기본적인 검색 방법으로, 쿼리와 가장 유사한 k개 문서를 반환합니다.

```python
# 기본 유사도 검색
results = await vectorstore.asimilarity_search(
    query="한국의 역사",
    k=5  # 상위 5개 문서
)

# 유사도 점수 포함
results = await vectorstore.asimilarity_search_with_score(
    query="한국의 역사",
    k=5
)
# [(Document(...), 0.92), (Document(...), 0.87), ...]
```

**장점:** 빠르고 간단
**단점:** 중복된 정보 반환 가능

#### 5.1.2 MMR 검색 (Maximal Marginal Relevance)

유사도와 다양성을 모두 고려한 검색 방법입니다.

```python
results = await vectorstore.amax_marginal_relevance_search(
    query="한국의 역사",
    k=5,              # 최종 반환할 문서 수
    fetch_k=20,       # 초기 후보 문서 수 (k의 2-4배 권장)
    lambda_mult=0.5   # 0=다양성, 1=유사도, 0.5=균형
)
```

**lambda_mult 설정 가이드:**
- `0.0`: 최대 다양성 (유사도 무시)
- `0.3`: 다양성 우선
- `0.5`: 균형 (기본 권장)
- `0.7`: 유사도 우선
- `1.0`: 최대 유사도 (일반 검색과 동일)

**사용 시기:**
- 다양한 관점의 정보가 필요할 때
- 중복 정보를 피하고 싶을 때
- 탐색적 검색

#### 5.1.3 임계값 기반 검색

유사도 점수가 임계값 이상인 문서만 반환합니다.

```python
# 유사도 0.8 이상만
results = await vectorstore.asimilarity_search_with_relevance_scores(
    query="한국의 역사",
    k=10,
    score_threshold=0.8  # 0.0 ~ 1.0
)

# 필터링
filtered_results = [
    (doc, score) for doc, score in results
    if score >= 0.8
]
```

**임계값 설정 가이드:**
- `0.9+`: 매우 엄격 (거의 완벽한 일치만)
- `0.8-0.9`: 엄격 (관련성 높은 문서만)
- `0.7-0.8`: 적당 (권장)
- `0.6-0.7`: 관대 (더 많은 후보)
- `0.6-`: 매우 관대 (노이즈 증가)

### 5.2 고급 검색 기법

#### 5.2.1 하이브리드 검색 (벡터 + 키워드)

벡터 검색과 키워드 검색을 결합합니다.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# 벡터 리트리버
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# BM25 키워드 리트리버
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 5

# 앙상블 리트리버
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.5, 0.5]  # 가중치 조정
)

# 검색
results = await ensemble_retriever.ainvoke("query")
```

**가중치 설정:**
- `[0.7, 0.3]`: 벡터 우선 (의미 검색 중요)
- `[0.5, 0.5]`: 균형 (권장)
- `[0.3, 0.7]`: 키워드 우선 (정확한 용어 매칭 중요)

#### 5.2.2 재순위화 (Re-ranking)

초기 검색 결과를 재정렬하여 정확도를 높입니다.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

# 기본 리트리버
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

# Cohere Rerank 압축기
compressor = CohereRerank(
    model="rerank-multilingual-v2.0",
    top_n=5  # 최종 5개만
)

# 압축 리트리버
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 검색 (자동으로 재순위화됨)
results = await compression_retriever.ainvoke("query")
```

**재순위화 전략:**
1. 초기 검색: k=20 (넉넉하게)
2. 재순위화: top_n=5 (최종 선별)
3. 정확도 향상: 10-20%

#### 5.2.3 다단계 검색 (Multi-Stage Retrieval)

```python
async def multi_stage_retrieval(query: str):
    """다단계 검색으로 정확도 향상"""

    # 1단계: 넓은 검색 (후보 수집)
    stage1_results = await vectorstore.asimilarity_search(
        query,
        k=50  # 넉넉하게
    )

    # 2단계: 메타데이터 필터링
    filtered = [
        doc for doc in stage1_results
        if doc.metadata.get("language") == "ko"
        and doc.metadata.get("quality_score", 0) >= 0.7
    ]

    # 3단계: MMR로 다양성 추가
    # (filtered 문서들로 새 임시 벡터 스토어 생성)
    temp_vectorstore = await FAISS.afrom_documents(
        filtered,
        embeddings
    )

    stage3_results = await temp_vectorstore.amax_marginal_relevance_search(
        query,
        k=5,
        lambda_mult=0.5
    )

    return stage3_results
```

#### 5.2.4 쿼리 확장 (Query Expansion)

```python
async def query_expansion_search(query: str):
    """LLM으로 쿼리 확장 후 검색"""

    # 1. LLM으로 쿼리 확장
    expansion_prompt = f"""다음 질문을 3가지 다른 방식으로 재작성하세요:

    원본 질문: {query}

    재작성 1:
    재작성 2:
    재작성 3:"""

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    expanded = await llm.ainvoke(expansion_prompt)

    # 2. 각 쿼리로 검색
    all_results = []
    queries = [query] + extract_rewrites(expanded.content)

    for q in queries:
        results = await vectorstore.asimilarity_search(q, k=3)
        all_results.extend(results)

    # 3. 중복 제거 및 재순위화
    unique_results = deduplicate(all_results)
    return unique_results[:5]
```

### 5.3 검색 전략 선택 가이드

| 사용 사례 | 권장 전략 | k 값 | 추가 설정 |
|----------|----------|------|----------|
| 일반 질의응답 | 유사도 검색 | 3-5 | - |
| 복잡한 질문 | MMR | 5-7 | lambda=0.5 |
| 정확도 중요 | 재순위화 | 초기 20, 최종 5 | Cohere Rerank |
| 다양한 관점 필요 | MMR | 7-10 | lambda=0.3 |
| 키워드 정확도 중요 | 하이브리드 | 5 | weights=[0.3, 0.7] |

---

## 6. 프롬프트 엔지니어링

### 6.1 RAG 프롬프트 구조

효과적인 RAG 프롬프트는 다음 요소를 포함해야 합니다:

```
[역할 정의] + [지시사항] + [컨텍스트] + [질문] + [제약사항] + [형식]
```

### 6.2 기본 프롬프트 템플릿

#### 6.2.1 범용 템플릿

```python
template = """당신은 도움이 되는 AI 어시스턴트입니다.

다음 문맥을 참고하여 질문에 답변하세요:

문맥:
{context}

질문: {question}

답변:"""
```

#### 6.2.2 개선된 템플릿 (권장)

```python
template = """당신은 {domain} 전문가입니다.

아래 제공된 문맥을 기반으로 질문에 답변하세요. 문맥에 정보가 없다면 "주어진 정보로는 답변할 수 없습니다"라고 솔직하게 말씀하세요.

문맥:
{context}

질문: {question}

답변 시 다음을 준수하세요:
- 문맥의 정보만 사용하세요
- 추측하지 마세요
- 간결하고 명확하게 답변하세요
- 가능한 경우 출처를 언급하세요

답변:"""
```

### 6.3 도메인별 프롬프트 예제

#### 6.3.1 기술 문서 QA

```python
tech_template = """당신은 기술 문서 전문가입니다.

제공된 문서를 기반으로 기술적 질문에 답변하세요.

문서:
{context}

질문: {question}

답변 시:
1. 정확한 용어를 사용하세요
2. 단계별로 설명하세요
3. 코드 예제가 있다면 포함하세요
4. 전제 조건이나 주의사항을 명시하세요

답변:"""
```

#### 6.3.2 고객 지원

```python
support_template = """당신은 친절한 고객 지원 전문가입니다.

다음 지식 베이스 정보를 참고하여 고객 질문에 답변하세요:

지식 베이스:
{context}

고객 질문: {question}

답변 시:
- 친절하고 공감하는 톤을 유지하세요
- 구체적인 해결 방법을 제시하세요
- 추가 도움이 필요한 경우를 안내하세요
- 관련 문서나 리소스를 언급하세요

답변:"""
```

#### 6.3.3 학술 연구

```python
academic_template = """당신은 {field} 분야의 연구 전문가입니다.

다음 논문 및 자료를 기반으로 학술적 질문에 답변하세요:

참고 자료:
{context}

연구 질문: {question}

답변 시:
- 학술적 엄밀성을 유지하세요
- 인용을 명확히 하세요
- 다양한 관점을 제시하세요
- 제한사항이나 추가 연구 필요성을 언급하세요

답변:"""
```

### 6.4 고급 프롬프트 기법

#### 6.4.1 소스 인용 강제

```python
citation_template = """당신은 신뢰할 수 있는 정보 제공자입니다.

다음 문서를 참고하여 질문에 답변하고, 반드시 출처를 인용하세요.

문서:
{context}

질문: {question}

답변 형식:
답변 내용... [출처: 문서명 또는 섹션]

예시:
한국의 수도는 서울입니다. [출처: 한국 지리 가이드, 1장]

답변:"""
```

#### 6.4.2 단계별 추론 (Chain-of-Thought)

```python
cot_template = """당신은 논리적 사고 전문가입니다.

제공된 정보를 바탕으로 질문에 단계별로 답변하세요.

정보:
{context}

질문: {question}

다음 형식으로 답변하세요:

1. 분석: 질문의 핵심 요소 파악
2. 관련 정보: 제공된 정보 중 관련된 부분
3. 추론: 논리적 추론 과정
4. 결론: 최종 답변

답변:"""
```

#### 6.4.3 반대 증거 확인

```python
balanced_template = """당신은 객관적인 분석가입니다.

제공된 문서를 바탕으로 질문에 답변하되, 찬성과 반대 의견을 모두 제시하세요.

문서:
{context}

질문: {question}

답변 형식:
1. 찬성 의견 및 근거:
2. 반대 의견 및 근거:
3. 종합 판단:

답변:"""
```

### 6.5 프롬프트 최적화 팁

#### 1. 컨텍스트 품질 개선

```python
def format_docs_with_metadata(docs):
    """메타데이터를 포함한 컨텍스트 포맷팅"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get('source', '출처 미상')
        page = doc.metadata.get('page', 'N/A')

        formatted.append(f"""
[문서 {i}]
출처: {source} (페이지 {page})
내용:
{doc.page_content}
---
        """)

    return "\n".join(formatted)
```

#### 2. 동적 프롬프트 조정

```python
def get_adaptive_prompt(query_type: str):
    """질의 유형에 따른 프롬프트 선택"""

    if "how" in query_type.lower():
        # 방법론 질문
        return how_to_template
    elif "why" in query_type.lower():
        # 이유/원인 질문
        return why_template
    elif "compare" in query_type.lower() or "difference" in query_type.lower():
        # 비교 질문
        return comparison_template
    else:
        # 기본 템플릿
        return default_template
```

#### 3. 응답 검증 추가

```python
validation_template = """당신은 신중한 AI 어시스턴트입니다.

문맥:
{context}

질문: {question}

답변을 생성하기 전에:
1. 문맥에 답변에 필요한 정보가 있는가?
2. 정보가 질문과 직접 관련이 있는가?
3. 추가 가정이 필요한가?

이를 바탕으로 답변하세요. 확신이 없다면 그 부분을 명시하세요.

답변:"""
```

### 6.6 프롬프트 성능 측정

```python
async def evaluate_prompt_quality(prompt_template, test_cases):
    """프롬프트 품질 평가"""

    results = {
        "accuracy": 0,
        "hallucination_rate": 0,
        "citation_rate": 0,
        "avg_length": 0,
    }

    for case in test_cases:
        # RAG 체인 실행
        chain = create_rag_chain(prompt_template)
        answer = await chain.ainvoke(case["question"])

        # 평가 기준
        is_correct = evaluate_correctness(answer, case["expected"])
        has_hallucination = detect_hallucination(answer, case["context"])
        has_citation = "[출처:" in answer or "[문서" in answer

        results["accuracy"] += int(is_correct)
        results["hallucination_rate"] += int(has_hallucination)
        results["citation_rate"] += int(has_citation)
        results["avg_length"] += len(answer)

    # 평균 계산
    n = len(test_cases)
    results["accuracy"] /= n
    results["hallucination_rate"] /= n
    results["citation_rate"] /= n
    results["avg_length"] /= n

    return results
```

---

## 7. 성능 최적화

### 7.1 인덱싱 최적화

#### 7.1.1 증분 업데이트

```python
class IncrementalVectorStore:
    """증분 업데이트를 지원하는 벡터 스토어"""

    def __init__(self, index_path: str):
        self.index_path = index_path
        self.vectorstore = None
        self.doc_ids = set()  # 이미 인덱싱된 문서 ID

    async def load_or_create(self):
        """기존 인덱스 로드 또는 새로 생성"""
        if os.path.exists(self.index_path):
            self.vectorstore = FAISS.load_local(
                self.index_path,
                embeddings
            )
            # 기존 문서 ID 로드
            self.doc_ids = self._load_doc_ids()
        else:
            self.vectorstore = None

    async def add_new_documents(self, documents):
        """새 문서만 추가 (중복 방지)"""
        new_docs = [
            doc for doc in documents
            if doc.metadata.get('id') not in self.doc_ids
        ]

        if not new_docs:
            print("추가할 새 문서 없음")
            return

        print(f"{len(new_docs)}개 새 문서 추가 중...")

        if self.vectorstore is None:
            # 최초 생성
            self.vectorstore = await FAISS.afrom_documents(
                new_docs,
                embeddings
            )
        else:
            # 기존 인덱스에 추가
            await self.vectorstore.aadd_documents(new_docs)

        # 문서 ID 업데이트
        for doc in new_docs:
            self.doc_ids.add(doc.metadata.get('id'))

        # 저장
        self.vectorstore.save_local(self.index_path)
        self._save_doc_ids()
```

#### 7.1.2 배치 인덱싱

```python
async def batch_indexing(documents, batch_size=100):
    """대용량 문서를 배치로 인덱싱"""

    total_batches = len(documents) // batch_size + 1
    vectorstores = []

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        batch_num = i // batch_size + 1

        print(f"배치 {batch_num}/{total_batches} 처리 중...")

        vs = await FAISS.afrom_documents(batch, embeddings)
        vectorstores.append(vs)

    # 모든 배치 병합
    print("인덱스 병합 중...")
    main_vectorstore = vectorstores[0]
    for vs in vectorstores[1:]:
        main_vectorstore.merge_from(vs)

    return main_vectorstore
```

### 7.2 검색 최적화

#### 7.2.1 캐싱 전략

```python
from functools import lru_cache
import hashlib

class CachedRetriever:
    """검색 결과 캐싱 리트리버"""

    def __init__(self, vectorstore, cache_size=128):
        self.vectorstore = vectorstore
        self.cache = {}
        self.cache_size = cache_size

    def _hash_query(self, query: str, k: int) -> str:
        """쿼리 해시 생성"""
        return hashlib.md5(f"{query}:{k}".encode()).hexdigest()

    async def retrieve(self, query: str, k: int = 5):
        """캐시된 검색"""
        cache_key = self._hash_query(query, k)

        # 캐시 확인
        if cache_key in self.cache:
            print(f"캐시 히트: {query[:30]}...")
            return self.cache[cache_key]

        # 검색 실행
        results = await self.vectorstore.asimilarity_search(query, k=k)

        # 캐시 저장 (LRU)
        if len(self.cache) >= self.cache_size:
            # 가장 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[cache_key] = results
        return results
```

#### 7.2.2 사전 필터링

```python
async def prefiltered_search(
    vectorstore,
    query: str,
    metadata_filter: dict,
    k: int = 5
):
    """메타데이터 사전 필터링으로 검색 범위 축소"""

    # 1. 메타데이터 필터링 (벡터 검색 전)
    # 이 부분은 벡터 DB에 따라 다름
    # FAISS는 직접 지원하지 않으므로 사후 필터링

    # 더 많은 후보 검색 (필터링 후 k개 확보 위해)
    candidates = await vectorstore.asimilarity_search(
        query,
        k=k * 3  # 여유있게
    )

    # 2. 필터 적용
    filtered = [
        doc for doc in candidates
        if all(
            doc.metadata.get(key) == value
            for key, value in metadata_filter.items()
        )
    ]

    # 3. 상위 k개만 반환
    return filtered[:k]
```

### 7.3 메모리 최적화

#### 7.3.1 스트리밍 인덱싱

```python
async def streaming_indexing(document_generator):
    """메모리 효율적인 스트리밍 인덱싱"""

    vectorstore = None
    batch = []
    batch_size = 50

    async for document in document_generator:
        batch.append(document)

        if len(batch) >= batch_size:
            # 배치 처리
            if vectorstore is None:
                vectorstore = await FAISS.afrom_documents(
                    batch,
                    embeddings
                )
            else:
                await vectorstore.aadd_documents(batch)

            # 메모리 해제
            batch = []

    # 남은 문서 처리
    if batch:
        if vectorstore is None:
            vectorstore = await FAISS.afrom_documents(batch, embeddings)
        else:
            await vectorstore.aadd_documents(batch)

    return vectorstore
```

#### 7.3.2 문서 압축

```python
from langchain.retrievers.document_compressors import LLMChainExtractor

async def compressed_retrieval(query: str):
    """검색 후 문서 압축으로 메모리 절약"""

    # 1. 넉넉하게 검색
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

    # 2. LLM으로 관련 부분만 추출
    compressor = LLMChainExtractor.from_llm(llm)

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )

    # 3. 압축된 문서만 반환 (메모리 효율적)
    compressed_docs = await compression_retriever.ainvoke(query)

    return compressed_docs
```

### 7.4 응답 시간 최적화

#### 7.4.1 병렬 처리

```python
async def parallel_rag_pipeline(queries: list[str]):
    """여러 쿼리를 병렬로 처리"""

    async def process_single_query(query: str):
        # 검색
        docs = await vectorstore.asimilarity_search(query, k=3)

        # RAG 체인 실행
        context = format_docs(docs)
        prompt = template.format(context=context, question=query)
        response = await llm.ainvoke(prompt)

        return response

    # 모든 쿼리 병렬 실행
    tasks = [process_single_query(q) for q in queries]
    results = await asyncio.gather(*tasks)

    return results
```

#### 7.4.2 응답 스트리밍

```python
async def streaming_rag_response(query: str):
    """스트리밍으로 빠른 첫 응답"""

    # 검색 (빠름)
    docs = await vectorstore.asimilarity_search(query, k=3)
    context = format_docs(docs)

    # LLM 스트리밍
    prompt = template.format(context=context, question=query)

    async for chunk in llm.astream(prompt):
        yield chunk  # 즉시 전송
```

### 7.5 성능 모니터링

```python
import time
from functools import wraps

def measure_time(func):
    """실행 시간 측정 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start

        print(f"{func.__name__}: {elapsed:.3f}초")
        return result

    return wrapper

class RAGPerformanceMonitor:
    """RAG 파이프라인 성능 모니터"""

    def __init__(self):
        self.metrics = {
            "retrieval_times": [],
            "llm_times": [],
            "total_times": [],
        }

    @measure_time
    async def monitored_retrieval(self, query: str):
        start = time.time()
        results = await vectorstore.asimilarity_search(query, k=5)
        elapsed = time.time() - start

        self.metrics["retrieval_times"].append(elapsed)
        return results

    @measure_time
    async def monitored_llm_call(self, prompt: str):
        start = time.time()
        response = await llm.ainvoke(prompt)
        elapsed = time.time() - start

        self.metrics["llm_times"].append(elapsed)
        return response

    def print_stats(self):
        """통계 출력"""
        import statistics

        print("\n성능 통계:")
        print(f"검색 평균: {statistics.mean(self.metrics['retrieval_times']):.3f}초")
        print(f"LLM 평균: {statistics.mean(self.metrics['llm_times']):.3f}초")
        print(f"전체 평균: {statistics.mean(self.metrics['total_times']):.3f}초")
```

---

## 8. 일반적인 문제와 해결책

### 8.1 환각(Hallucination) 문제

#### 문제
LLM이 제공된 컨텍스트에 없는 정보를 만들어내는 현상

#### 해결책

**1. 명확한 지시문 추가**
```python
template = """다음 규칙을 엄격히 따르세요:
1. 오직 제공된 문맥만 사용하세요
2. 문맥에 정보가 없으면 "정보가 없습니다"라고 답하세요
3. 추측하거나 일반 지식을 사용하지 마세요

문맥: {context}
질문: {question}
답변:"""
```

**2. 응답 검증 단계 추가**
```python
async def validate_response(response: str, context: str):
    """응답이 컨텍스트 기반인지 검증"""

    validation_prompt = f"""
    다음 응답이 제공된 컨텍스트에만 기반했는지 확인하세요.

    컨텍스트: {context}
    응답: {response}

    검증 결과 (Yes/No):
    """

    validation = await llm.ainvoke(validation_prompt)

    if "No" in validation.content:
        return "죄송합니다. 제공된 정보로는 정확한 답변을 드릴 수 없습니다."

    return response
```

**3. 출처 인용 강제**
```python
template = """모든 주장에 출처를 명시하세요.

예: "한국의 수도는 서울입니다. [출처: 문서 1]"

문맥: {context}
질문: {question}
답변:"""
```

### 8.2 검색 품질 저하

#### 문제
관련 없는 문서가 검색되거나, 관련 문서를 놓치는 현상

#### 해결책

**1. 청킹 전략 재검토**
```python
# 문서 길이 분석
doc_lengths = [len(doc.page_content) for doc in documents]
avg_length = sum(doc_lengths) / len(doc_lengths)

# 적절한 chunk_size 계산
optimal_chunk_size = int(avg_length * 0.7)  # 평균의 70%
```

**2. 쿼리 개선**
```python
async def improve_query(query: str):
    """LLM으로 쿼리 개선"""

    improvement_prompt = f"""
    다음 질문을 더 명확하고 검색하기 좋게 재작성하세요:

    원본: {query}
    개선된 질문:
    """

    improved = await llm.ainvoke(improvement_prompt)
    return improved.content
```

**3. 하이브리드 검색 사용**
```python
# 벡터 + 키워드 검색
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.6, 0.4]
)
```

### 8.3 느린 응답 시간

#### 문제
사용자 경험을 해치는 긴 응답 시간

#### 해결책

**1. 인덱스 사전 로드**
```python
# 애플리케이션 시작 시 인덱스 로드 (한 번만)
@app.on_event("startup")
async def startup_event():
    global vectorstore
    vectorstore = FAISS.load_local(
        "./index",
        embeddings,
        allow_dangerous_deserialization=True
    )
```

**2. 검색 결과 캐싱**
```python
# 자주 묻는 질문 캐싱
from cachetools import TTLCache

query_cache = TTLCache(maxsize=100, ttl=3600)  # 1시간 캐시

async def cached_search(query: str):
    if query in query_cache:
        return query_cache[query]

    results = await vectorstore.asimilarity_search(query)
    query_cache[query] = results
    return results
```

**3. 스트리밍 응답**
```python
# 빠른 첫 토큰 제공
async def stream_response(query: str):
    docs = await vectorstore.asimilarity_search(query, k=3)
    context = format_docs(docs)

    async for chunk in llm.astream(prompt):
        yield chunk
```

### 8.4 메타데이터 필터링 문제

#### 문제
FAISS는 복잡한 메타데이터 필터링을 지원하지 않음

#### 해결책

**1. 사후 필터링**
```python
async def post_filter_search(query: str, filters: dict):
    # 넉넉하게 검색
    results = await vectorstore.asimilarity_search(query, k=50)

    # 필터 적용
    filtered = [
        doc for doc in results
        if all(
            doc.metadata.get(k) == v
            for k, v in filters.items()
        )
    ]

    return filtered[:5]  # 상위 5개
```

**2. 벡터 DB 변경 (권장)**
```python
# Chroma, Pinecone, Weaviate 등으로 전환
# 복잡한 필터링 지원
from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents,
    embeddings,
    persist_directory="./chroma_db"
)

# 복잡한 필터 지원
results = vectorstore.similarity_search(
    query,
    k=5,
    filter={
        "$and": [
            {"category": "history"},
            {"year": {"$gte": 1900}}
        ]
    }
)
```

### 8.5 컨텍스트 길이 초과

#### 문제
검색된 문서가 LLM 컨텍스트 제한을 초과

#### 해결책

**1. 문서 압축**
```python
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)
```

**2. 토큰 수 계산 및 제한**
```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def trim_context(docs, max_tokens: int = 3000):
    """토큰 제한에 맞게 문서 자르기"""
    context = ""
    token_count = 0

    for doc in docs:
        doc_tokens = count_tokens(doc.page_content)

        if token_count + doc_tokens > max_tokens:
            break

        context += doc.page_content + "\n\n"
        token_count += doc_tokens

    return context
```

**3. 문서 요약**
```python
async def summarize_and_use(docs):
    """긴 문서는 요약해서 사용"""
    summaries = []

    for doc in docs:
        if len(doc.page_content) > 1000:
            # 요약 생성
            summary_prompt = f"다음을 간결하게 요약하세요:\n\n{doc.page_content}"
            summary = await llm.ainvoke(summary_prompt)
            summaries.append(summary.content)
        else:
            summaries.append(doc.page_content)

    return "\n\n".join(summaries)
```

### 8.6 다국어 지원 문제

#### 문제
한국어-영어 혼합 문서에서 검색 품질 저하

#### 해결책

**1. 다국어 임베딩 모델 사용**
```python
# 다국어 지원 우수한 모델
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

# 또는
from langchain_cohere import CohereEmbeddings
embeddings = CohereEmbeddings(
    model="embed-multilingual-v3.0"
)
```

**2. 언어별 인덱스 분리**
```python
# 언어 감지
from langdetect import detect

def separate_by_language(documents):
    ko_docs = []
    en_docs = []

    for doc in documents:
        lang = detect(doc.page_content)
        if lang == 'ko':
            ko_docs.append(doc)
        else:
            en_docs.append(doc)

    return ko_docs, en_docs

# 별도 인덱스 생성
ko_vectorstore = await FAISS.afrom_documents(ko_docs, embeddings)
en_vectorstore = await FAISS.afrom_documents(en_docs, embeddings)
```

---

## 9. 프로덕션 배포 체크리스트

### 9.1 사전 준비

#### 환경 설정
- [ ] 환경 변수 관리 (.env, 시크릿 관리)
- [ ] API 키 보안 (AWS Secrets Manager, Azure Key Vault 등)
- [ ] 로깅 설정 (구조화된 로그)
- [ ] 모니터링 도구 연동 (Prometheus, Grafana, Datadog 등)

#### 데이터 준비
- [ ] 문서 품질 검증 (중복, 오류, 형식)
- [ ] 메타데이터 일관성 확인
- [ ] 청킹 전략 최적화 완료
- [ ] 인덱스 백업 계획 수립

### 9.2 성능 최적화

#### 인덱싱
- [ ] 배치 인덱싱 구현
- [ ] 증분 업데이트 메커니즘
- [ ] 인덱스 버전 관리
- [ ] 인덱스 저장소 최적화 (SSD, 클라우드 스토리지)

#### 검색
- [ ] 캐싱 전략 구현 (Redis, Memcached)
- [ ] 쿼리 최적화
- [ ] 응답 시간 SLA 정의 (예: p95 < 500ms)
- [ ] 부하 테스트 완료

#### LLM 호출
- [ ] 토큰 사용량 최적화
- [ ] 응답 스트리밍 구현
- [ ] 재시도 및 폴백 로직
- [ ] Rate limiting 설정

### 9.3 안정성 및 신뢰성

#### 에러 처리
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def robust_retrieval(query: str):
    """재시도 로직이 있는 안정적인 검색"""
    try:
        return await vectorstore.asimilarity_search(query, k=5)
    except Exception as e:
        logging.error(f"검색 실패: {e}")
        raise
```

#### 폴백 전략
```python
async def rag_with_fallback(query: str):
    """폴백이 있는 RAG"""
    try:
        # 메인 RAG 파이프라인
        return await main_rag_chain.ainvoke(query)

    except Exception as e:
        logging.warning(f"메인 RAG 실패: {e}, 폴백 사용")

        # 폴백: 간단한 검색 + LLM
        docs = await vectorstore.asimilarity_search(query, k=2)
        context = format_docs(docs)

        simple_prompt = f"컨텍스트: {context}\n질문: {query}\n답변:"
        return await llm.ainvoke(simple_prompt)
```

#### 헬스 체크
```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/health")
async def health_check():
    """시스템 헬스 체크"""
    try:
        # 벡터 스토어 확인
        await vectorstore.asimilarity_search("test", k=1)

        # LLM 확인
        await llm.ainvoke("test")

        return {"status": "healthy"}

    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

### 9.4 보안

- [ ] 입력 검증 (SQL 인젝션, XSS 방지)
- [ ] 출력 필터링 (민감 정보 마스킹)
- [ ] 접근 제어 (인증, 권한 관리)
- [ ] 감사 로깅 (모든 쿼리 및 응답 기록)
- [ ] Rate limiting (남용 방지)

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """API 키 검증"""
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/query")
async def query_endpoint(
    query: str,
    api_key: str = Depends(verify_api_key)
):
    """보안이 적용된 쿼리 엔드포인트"""

    # 입력 검증
    if len(query) > 500:
        raise HTTPException(status_code=400, detail="Query too long")

    # 쿼리 실행
    result = await rag_chain.ainvoke(query)

    # 감사 로깅
    logging.info(f"Query: {query}, API Key: {api_key[:8]}...")

    return {"answer": result}
```

### 9.5 모니터링 및 관찰성

#### 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge

# 메트릭 정의
query_counter = Counter('rag_queries_total', 'Total RAG queries')
query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')
cache_hit_rate = Gauge('rag_cache_hit_rate', 'Cache hit rate')

@query_duration.time()
async def monitored_query(query: str):
    """메트릭이 수집되는 쿼리"""
    query_counter.inc()

    # 캐시 확인
    if query in cache:
        cache_hit_rate.inc()
        return cache[query]

    # 실행
    result = await rag_chain.ainvoke(query)
    cache[query] = result

    return result
```

#### 로깅 전략
```python
import logging
import json

# 구조화된 로깅
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def log_rag_event(event_type: str, data: dict):
    """구조화된 RAG 이벤트 로깅"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        **data
    }
    logging.info(json.dumps(log_entry))

# 사용 예
async def logged_rag_query(query: str):
    log_rag_event("query_start", {"query": query})

    try:
        result = await rag_chain.ainvoke(query)
        log_rag_event("query_success", {
            "query": query,
            "result_length": len(result)
        })
        return result

    except Exception as e:
        log_rag_event("query_error", {
            "query": query,
            "error": str(e)
        })
        raise
```

### 9.6 스케일링

#### 수평 확장
```python
# FastAPI + Gunicorn 배포
# gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# 로드 밸런싱 (Nginx 설정 예)
"""
upstream rag_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://rag_backend;
    }
}
"""
```

#### 벡터 DB 스케일링
```python
# Pinecone 예제 (샤딩)
# 대규모 데이터셋을 여러 인덱스로 분할

async def sharded_search(query: str, num_shards: int = 4):
    """샤딩된 인덱스에서 병렬 검색"""

    tasks = [
        pinecone_index_shard_i.query(
            query_vector,
            top_k=5
        )
        for i in range(num_shards)
    ]

    results = await asyncio.gather(*tasks)

    # 결과 병합 및 재정렬
    all_results = []
    for shard_results in results:
        all_results.extend(shard_results)

    all_results.sort(key=lambda x: x.score, reverse=True)
    return all_results[:5]
```

### 9.7 비용 최적화

- [ ] 임베딩 캐싱 (동일 문서 재임베딩 방지)
- [ ] LLM 토큰 최적화 (불필요한 컨텍스트 제거)
- [ ] 쿼리 캐싱 (자주 묻는 질문)
- [ ] 배치 처리 (여러 쿼리 동시 처리)
- [ ] 비용 모니터링 (API 사용량 추적)

```python
class CostTracker:
    """비용 추적"""

    def __init__(self):
        self.embedding_tokens = 0
        self.llm_tokens = 0

    def track_embeddings(self, num_docs: int, avg_length: int):
        self.embedding_tokens += num_docs * avg_length

    def track_llm(self, prompt_tokens: int, completion_tokens: int):
        self.llm_tokens += prompt_tokens + completion_tokens

    def estimate_cost(self):
        """비용 추정 (OpenAI 기준)"""
        embedding_cost = self.embedding_tokens / 1000 * 0.0001
        llm_cost = self.llm_tokens / 1000 * 0.002

        return {
            "embedding_cost": embedding_cost,
            "llm_cost": llm_cost,
            "total_cost": embedding_cost + llm_cost
        }
```
