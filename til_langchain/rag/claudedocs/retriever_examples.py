"""
FAISS Vectorstore Retriever 완전 예제
LangChain v0.2.0+ 호환 코드
"""

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS, DistanceStrategy

# 환경 변수 로드
load_dotenv()

# 1. 문서 로드
print("=== 1. 문서 로드 ===")
loader = TextLoader("../data/history.txt")
documents = loader.load()
print(f"로드된 문서 개수: {len(documents)}")

# 2. 텍스트 분할
print("\n=== 2. 텍스트 분할 ===")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len
)
document_list = text_splitter.split_documents(documents)
print(f"분할된 청크 개수: {len(document_list)}")

# 3. 임베딩 모델 초기화
print("\n=== 3. 임베딩 모델 초기화 ===")
embeddings_model = GoogleGenerativeAIEmbeddings(
    model='models/gemini-embedding-001'
)

# 4. FAISS Vectorstore 생성
print("\n=== 4. FAISS Vectorstore 생성 ===")
vectorstore = FAISS.from_documents(
    document_list,
    embedding=embeddings_model,
    distance_strategy=DistanceStrategy.COSINE
)
print("Vectorstore 생성 완료")

# ==========================================
# Retriever 사용 예제
# ==========================================

query = "한국의 역사가 궁금해"

# 예제 1: 기본 Similarity 검색
print("\n=== 예제 1: 기본 Similarity 검색 ===")
retriever_basic = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
docs = retriever_basic.invoke(query)
print(f"검색된 문서 개수: {len(docs)}")
for i, doc in enumerate(docs, 1):
    print(f"\n[문서 {i}]")
    print(f"내용: {doc.page_content[:100]}...")
    print(f"메타데이터: {doc.metadata}")

# 예제 2: MMR 검색 (다양성 있는 결과)
print("\n=== 예제 2: MMR 검색 (다양성) ===")
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,              # 최종 반환 개수
        "fetch_k": 10,       # 초기 검색 개수
        "lambda_mult": 0.5   # 유사도:다양성 = 0.5:0.5
    }
)
docs_mmr = retriever_mmr.invoke(query)
print(f"MMR 검색 문서 개수: {len(docs_mmr)}")
for i, doc in enumerate(docs_mmr, 1):
    print(f"\n[MMR 문서 {i}]")
    print(f"내용: {doc.page_content[:100]}...")

# 예제 3: 유사도 임계값 검색
print("\n=== 예제 3: 유사도 임계값 검색 ===")
retriever_threshold = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.7  # 0.7 이상만 반환
    }
)
docs_threshold = retriever_threshold.invoke(query)
print(f"임계값 이상 문서 개수: {len(docs_threshold)}")
for i, doc in enumerate(docs_threshold, 1):
    print(f"\n[임계값 문서 {i}]")
    print(f"내용: {doc.page_content[:100]}...")

# 예제 4: 직접 유사도 점수 확인
print("\n=== 예제 4: 유사도 점수 확인 ===")
docs_with_scores = vectorstore.similarity_search_with_score(query, k=3)
for i, (doc, score) in enumerate(docs_with_scores, 1):
    print(f"\n[문서 {i}] - 유사도 점수: {score:.4f}")
    print(f"내용: {doc.page_content[:100]}...")

# 예제 5: 다양한 쿼리 테스트
print("\n=== 예제 5: 다양한 쿼리 테스트 ===")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

test_queries = [
    "고조선의 건국은 언제인가요?",
    "삼국시대에 대해 알려주세요",
    "조선시대의 특징은 무엇인가요?"
]

for test_query in test_queries:
    print(f"\n쿼리: {test_query}")
    results = retriever.invoke(test_query)
    print(f"검색 결과: {len(results)}개 문서")
    print(f"첫 번째 문서: {results[0].page_content[:80]}...")

# ==========================================
# Vectorstore 저장 및 로드
# ==========================================

print("\n=== Vectorstore 저장 및 로드 ===")

# 저장
vectorstore.save_local("./rag_vectorstore")
print("Vectorstore 저장 완료: ./rag_vectorstore")

# 로드
loaded_vectorstore = FAISS.load_local(
    "../rag_vectorstore",
    embeddings_model,
    allow_dangerous_deserialization=True
)
print("Vectorstore 로드 완료")

# 로드된 vectorstore로 retriever 생성
loaded_retriever = loaded_vectorstore.as_retriever(search_kwargs={"k": 1})
loaded_docs = loaded_retriever.invoke("한국의 역사")
print(f"로드된 retriever 검색 결과: {len(loaded_docs)}개")