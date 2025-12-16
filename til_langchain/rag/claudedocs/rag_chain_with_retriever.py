"""
RAG 체인과 Retriever 통합 예제
LangChain v0.2.0+ 호환 완전한 RAG 파이프라인
"""

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS, DistanceStrategy
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 환경 변수 로드
load_dotenv()

# ==========================================
# 1. 문서 준비 및 Vectorstore 생성
# ==========================================

print("=== RAG 파이프라인 초기화 ===\n")

# 문서 로드
loader = TextLoader("../data/history.txt")
documents = loader.load()

# 텍스트 분할
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len
)
document_list = text_splitter.split_documents(documents)
print(f"문서 분할 완료: {len(document_list)}개 청크")

# 임베딩 모델 초기화
embeddings_model = GoogleGenerativeAIEmbeddings(
    model='models/gemini-embedding-001'
)

# FAISS Vectorstore 생성
vectorstore = FAISS.from_documents(
    document_list,
    embedding=embeddings_model,
    distance_strategy=DistanceStrategy.COSINE
)
print("Vectorstore 생성 완료\n")

# ==========================================
# 2. Retriever 생성
# ==========================================

# 방법 1: 기본 Similarity Retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # 상위 3개 문서 반환
)

# 방법 2: MMR Retriever (다양성 추구)
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
        "lambda_mult": 0.7  # 유사도 70%, 다양성 30%
    }
)

# 방법 3: 임계값 기반 Retriever
retriever_threshold = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.75
    }
)

print("Retriever 생성 완료\n")

# ==========================================
# 3. LLM 모델 초기화
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
)
print("LLM 모델 초기화 완료\n")

# ==========================================
# 4. RAG 프롬프트 템플릿 작성
# ==========================================

template = """당신은 한국 역사 전문가입니다. 주어진 문맥을 기반으로 질문에 답변해주세요.
답변할 수 없는 경우 "주어진 문맥에서 해당 정보를 찾을 수 없습니다"라고 말씀해주세요.

문맥:
{context}

질문: {question}

답변:"""

prompt = ChatPromptTemplate.from_template(template)
print("프롬프트 템플릿 생성 완료\n")

# ==========================================
# 5. RAG 체인 구성
# ==========================================

def format_docs(docs):
    """검색된 문서를 하나의 문자열로 포맷팅"""
    return "\n\n".join(doc.page_content for doc in docs)


# 체인 구성: Retriever -> Format -> Prompt -> LLM -> Parser
rag_chain = (
    {
        "context": retriever | format_docs,  # retriever로 문서 검색 후 포맷팅
        "question": RunnablePassthrough()     # 질문을 그대로 전달
    }
    | prompt
    | llm
    | StrOutputParser()
)

print("RAG 체인 구성 완료\n")

# ==========================================
# 6. RAG 체인 실행 및 테스트
# ==========================================

print("=== RAG 체인 실행 테스트 ===\n")

# 테스트 질문 1
question1 = "고조선은 누가 세웠나요?"
print(f"질문 1: {question1}")
answer1 = rag_chain.invoke(question1)
print(f"답변 1: {answer1}\n")
print("-" * 80 + "\n")

# 테스트 질문 2
question2 = "삼국시대에는 어떤 나라들이 있었나요?"
print(f"질문 2: {question2}")
answer2 = rag_chain.invoke(question2)
print(f"답변 2: {answer2}\n")
print("-" * 80 + "\n")

# 테스트 질문 3
question3 = "통일신라의 특징은 무엇인가요?"
print(f"질문 3: {question3}")
answer3 = rag_chain.invoke(question3)
print(f"답변 3: {answer3}\n")
print("-" * 80 + "\n")

# ==========================================
# 7. 검색된 문서 확인 (디버깅용)
# ==========================================

print("=== 검색된 문서 확인 ===\n")

test_query = "고조선은 누가 세웠나요?"
retrieved_docs = retriever.invoke(test_query)

print(f"쿼리: {test_query}")
print(f"검색된 문서 개수: {len(retrieved_docs)}\n")

for i, doc in enumerate(retrieved_docs, 1):
    print(f"[문서 {i}]")
    print(f"내용: {doc.page_content[:200]}...")
    print(f"메타데이터: {doc.metadata}")
    print()

# ==========================================
# 8. 다양한 Retriever를 사용한 체인 비교
# ==========================================

print("=== 다양한 Retriever 비교 ===\n")

# MMR Retriever를 사용한 체인
rag_chain_mmr = (
    {
        "context": retriever_mmr | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

test_question = "한국 역사에서 중요한 시대는 언제인가요?"

print(f"질문: {test_question}\n")

print("[Similarity Retriever 결과]")
answer_similarity = rag_chain.invoke(test_question)
print(f"{answer_similarity}\n")

print("[MMR Retriever 결과]")
answer_mmr = rag_chain_mmr.invoke(test_question)
print(f"{answer_mmr}\n")

# ==========================================
# 9. 스트리밍 응답 (선택적)
# ==========================================

print("=== 스트리밍 응답 예제 ===\n")

question_stream = "조선시대에 대해 설명해주세요"
print(f"질문: {question_stream}\n답변: ", end="")

for chunk in rag_chain.stream(question_stream):
    print(chunk, end="", flush=True)

print("\n\n" + "=" * 80)
print("RAG 파이프라인 테스트 완료")