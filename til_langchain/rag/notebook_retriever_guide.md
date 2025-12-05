# Jupyter Notebook에서 Retriever 사용 가이드

현재 노트북 파일(`rag_practices.ipynb`)의 146번째 라인에서 사용할 올바른 코드입니다.

## 문제 상황
```python
# ❌ 에러 발생 코드
retriever.get_relevant_documents(query)
# AttributeError: 'VectorStoreRetriever' object has no attribute 'get_relevant_documents'
```

## 해결 방법

### 1. 기본 사용법 (invoke 메서드)

```python
# ✅ 올바른 코드
query = "한국의 역사가 궁금해"
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# invoke() 메서드 사용 (LangChain v0.2.0+)
docs = retriever.invoke(query)
print(f"검색된 문서: {len(docs)}개")
print(docs[0].page_content)
```

### 2. 다양한 검색 방식

#### 2.1 Similarity 검색 (기본)
```python
# 유사도 기반 검색 (가장 유사한 문서 k개 반환)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
docs = retriever.invoke("한국의 역사가 궁금해")
```

#### 2.2 MMR 검색 (다양성)
```python
# Maximum Marginal Relevance (다양성 있는 결과)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,              # 최종 반환 개수
        "fetch_k": 10,       # 초기 검색 개수
        "lambda_mult": 0.5   # 0=다양성 중심, 1=유사도 중심
    }
)
docs = retriever.invoke("한국의 역사가 궁금해")
```

#### 2.3 유사도 임계값 검색
```python
# 특정 유사도 이상만 반환
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.8  # 0.8 이상만 반환
    }
)
docs = retriever.invoke("한국의 역사가 궁금해")
```

### 3. 유사도 점수와 함께 검색

```python
# retriever가 아닌 vectorstore에서 직접 호출
docs_with_scores = vectorstore.similarity_search_with_score(
    "한국의 역사가 궁금해",
    k=3
)

for doc, score in docs_with_scores:
    print(f"유사도 점수: {score:.4f}")
    print(f"문서 내용: {doc.page_content[:100]}...\n")
```

### 4. RAG 체인 구성

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 문서 포맷팅 함수
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 프롬프트 템플릿
template = """당신은 한국 역사 전문가입니다. 주어진 문맥을 기반으로 질문에 답변해주세요.

문맥:
{context}

질문: {question}

답변:"""

prompt = ChatPromptTemplate.from_template(template)

# RAG 체인 구성
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | client  # 기존에 생성한 ChatGoogleGenerativeAI 인스턴스
    | StrOutputParser()
)

# 체인 실행
answer = rag_chain.invoke("고조선은 누가 세웠나요?")
print(answer)
```

## 노트북에 추가할 셀 코드

```python
# ===== 새로운 셀 1: Retriever 기본 사용 =====
query = "한국의 역사가 궁금해"
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# invoke() 메서드 사용 (최신 방식)
docs = retriever.invoke(query)
print(f"검색된 문서 개수: {len(docs)}")
for i, doc in enumerate(docs, 1):
    print(f"\n[문서 {i}]")
    print(doc.page_content[:150])
```

```python
# ===== 새로운 셀 2: 유사도 점수 확인 =====
docs_with_scores = vectorstore.similarity_search_with_score(query, k=3)
for i, (doc, score) in enumerate(docs_with_scores, 1):
    print(f"\n[문서 {i}] 유사도: {score:.4f}")
    print(doc.page_content[:150])
```

```python
# ===== 새로운 셀 3: MMR 검색 =====
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
        "lambda_mult": 0.5
    }
)
docs_mmr = retriever_mmr.invoke(query)
print(f"MMR 검색 결과: {len(docs_mmr)}개")
```

```python
# ===== 새로운 셀 4: RAG 체인 구성 =====
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

template = """당신은 한국 역사 전문가입니다. 주어진 문맥을 기반으로 질문에 답변해주세요.

문맥:
{context}

질문: {question}

답변:"""

prompt = ChatPromptTemplate.from_template(template)

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | client
    | StrOutputParser()
)

# 테스트
answer = rag_chain.invoke("고조선은 누가 세웠나요?")
print(answer)
```

## 핵심 포인트

1. **invoke() 사용**: `get_relevant_documents()`는 deprecated되어 `invoke()`를 사용해야 합니다
2. **search_type 선택**:
   - `"similarity"`: 가장 유사한 문서 (기본)
   - `"mmr"`: 다양성 있는 결과
   - `"similarity_score_threshold"`: 임계값 기반
3. **k 파라미터**: 반환할 문서 개수 지정
4. **RAG 체인**: Retriever를 체인으로 연결하여 질의응답 시스템 구축

## 참고 자료
- LangChain Retriever 공식 문서: https://python.langchain.com/docs/modules/data_connection/retrievers/
- FAISS Vectorstore 문서: https://python.langchain.com/docs/integrations/vectorstores/faiss