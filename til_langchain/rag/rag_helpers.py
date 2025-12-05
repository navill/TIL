from __future__ import annotations

import asyncio
from typing import Sequence, TYPE_CHECKING

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import DistanceStrategy, FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

if TYPE_CHECKING:
    from langchain_core.documents import Document
    from langchain_core.vectorstores import VectorStoreRetriever

"""
# 프로젝트 사용 모듈(고정)
llm_client: ChatGoogleGenerativeAI

embedding_model: GoogleGenerativeAIEmbeddings(Embeddings)
Embeddings ref: https://reference.langchain.com/python/langchain_core/embeddings/

vectorstore: FAISS(VectorStore)
VectorStore ref: https://reference.langchain.com/python/langchain_core/vectorstores/

retriever: VectorStoreRetriever(BaseRetriever)
BaseRetriever ref: https://reference.langchain.com/python/langchain_core/retrievers/
"""

load_dotenv()

embeddings_model = GoogleGenerativeAIEmbeddings(model='models/gemini-embedding-001')


def get_client() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=1.0,
    )


def get_prompt_template(prompt: str) -> ChatPromptTemplate:
    # ex: prompt = "You are an expert in astronomy. Answer the question. <Question>: {input}"
    # prompt_template = get_prompt_template(raw_prompt)
    # chain = prompt_template | client
    # chain.invoke({"input": "지구의 자전 주기는?"})
    return ChatPromptTemplate.from_template(template=prompt)


async def get_text_docs(file_path: str) -> list[Document]:
    return await TextLoader(file_path=file_path).aload()


def split_contents(content: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    if isinstance(content, str):
        return splitter.split_text(text=content)
    else:
        raise ValueError("입력값이 문자열이 아닙니다.")


async def atransform_documents(
        contents: list[Document],
        chunk_size: int = 500,
        chunk_overlap: int = 100
) -> Sequence[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    if isinstance(contents, list):
        for doc in contents:
            if not isinstance(doc, Document):
                raise ValueError("객체 타입이 langchain_core.documents.Document 타입이 아닙니다.")
        return await splitter.atransform_documents(documents=contents)
    else:
        raise ValueError("입력값이 list가 아닙니다.")


async def get_embeddings(texts: list[str], embed_model: GoogleGenerativeAIEmbeddings) -> list[list[float]]:
    return await embed_model.aembed_documents(texts=texts)


async def get_vectorstore(document_list: list[Document], embed_model: GoogleGenerativeAIEmbeddings) -> FAISS:
    return await FAISS.afrom_documents(
        document_list,
        embedding=embed_model,
        distance_strategy=DistanceStrategy.COSINE
    )


async def search(vectorstore: FAISS, query: str, k: int = 1) -> list[Document]:
    return await vectorstore.asimilarity_search(query=query, k=k)


def get_retriever(vectorstore: FAISS, k: int = 1) -> VectorStoreRetriever:
    return vectorstore.as_retriever(search_kwargs={"k": k})


async def retrieve(retriever: VectorStoreRetriever, query: str) -> list[Document]:
    # ainvoke/invoke -> Runnable
    return await retriever.ainvoke(input=query)


async def test_search(query: str) -> list[Document]:
    history_docs: list[Document] = await get_text_docs("data/history.txt")
    vector_store = await get_vectorstore(history_docs, embeddings_model)
    return await search(vector_store, query)


async def test_retrieve(query: str) -> list[Document]:
    history_docs: list[Document] = await get_text_docs("data/history.txt")
    vectorstore = await get_vectorstore(history_docs, embeddings_model)
    retriever = get_retriever(vectorstore, k=1)
    return await retrieve(retriever, query)


async def test_chain(query: str) -> str:
    def format_docs(docs):
        """검색된 문서를 하나의 문자열로 포맷팅"""
        return "\n\n".join(doc.page_content for doc in docs)

    template = """당신은 한국 역사 전문가입니다. 주어진 문맥을 기반으로 질문에 답변해주세요.
    답변할 수 없는 경우 "주어진 문맥에서 해당 정보를 찾을 수 없습니다"라고 말씀해주세요.

    문맥:
    {context}

    질문: {question}

    답변:"""

    prompt = ChatPromptTemplate.from_template(template)
    history_docs: list[Document] = await get_text_docs("data/history.txt")
    vectorstore = await get_vectorstore(history_docs, embeddings_model)
    retriever = get_retriever(vectorstore, k=1)
    rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | get_client()
            | StrOutputParser()
    )
    return await rag_chain.ainvoke(input=query)


if __name__ == '__main__':
    query = "한국 역사에 대해 알려줘"
    loop = asyncio.new_event_loop()
    search_result = loop.run_until_complete(test_search(query=query))
    # [Document(id='e2a38dae-3fb4-4074-bcab-249a8741a793', metadata={'source': 'data/history.txt'}, page_content='한국의 역사는 수천 년에 걸쳐 이어져 온 긴 여정 속에서 다양한 문화와 전통이 형성되고 발전해 왔습니다. 고조선에서 시작해 삼국 시대의 경쟁, 그리고 통일 신라와 고려를 거쳐 조선까지, 한반도는 많은 변화를 겪었습니다.\n\n고조선은 기원전 2333년 단군왕검에 의해 세워졌다고 전해집니다. 이는 한국 역사상 최초의 국가로, 한민족의 시원이라 할 수 있습니다. 이후 기원전 1세기경에는 한반도와 만주 일대에서 여러 소국이 성장하며 삼한 시대로 접어듭니다.\n\n4세기경, 고구려, 백제, 신라의 삼국이 한반도의 주요 세력으로 부상했습니다. 이 시기는 삼국이 각각 문화와 기술, 무력을 발전시키며 경쟁적으로 성장한 시기로, 한국 역사에서 중요한 전환점을 마련했습니다. 특히 고구려는 북방의 강대국으로 성장하여 중국과도 여러 차례 전쟁을 벌였습니다.\n\n7세기 말, 신라는 당나라와 연합하여 백제와 고구려를 차례로 정복하고, 한반도 최초의 통일 국가인 통일 신라를 건립합니다. 이 시기에 신라는 불교를 국교로 채택하며 문화와 예술이 크게 발전했습니다.\n\n그러나 10세기에 이르러 신라는 내부의 분열과 외부의 압력으로 쇠퇴하고, 이를 대체하여 고려가 성립됩니다. 고려 시대에는 과거제도의 도입과 더불어 청자 등 고려 고유의 문화가 꽃피었습니다.\n\n조선은 1392년 이성계에 의해 건국되어, 1910년까지 이어졌습니다. 조선 초기에는 세종대왕이 한글을 창제하여 백성들의 문해율을 높이는 등 문화적, 과학적 성취가 이루어졌습니다. 그러나 조선 후기에는 내부적으로 실학의 발전과 함께 사회적 변화가 모색되었으나, 외부로부터의 압력은 점차 커져만 갔습니다.\n\n19세기 말부터 20세기 초에 걸쳐 한국은 제국주의 열강의 침략을 받으며 많은 시련을 겪었습니다. 1910년, 한국은 일본에 의해 강제로 병합되어 35년간의 식민 지배를 받게 됩니다. 이 기간 동안 한국인들은 독립을 위한 다양한 운동을 전개했으며, 이는 1945년 일본의 패망으로 이어지는 독립으로 결실을 맺었습니다.\n\n해방 후 한반도는 남북으로 분단되어 각각 다른 정부가 수립되었고, 1950년에는 한국전쟁이 발발하여 큰 피해를 입었습니다. 전쟁 후 남한은 빠른 경제 발전을 이루며 오늘날에 이르렀습니다.\n\n한국의 역사는 오랜 시간 동안 수많은 시련과 도전을 겪으며 형성된 깊은 유산을 지니고 있습니다. 오늘날 한국은 그 역사적 배경 위에서 세계적으로 중요한 역할을 하고 있으며, 과거의 역사가 현재와 미래에 어떻게 영향을 미치는지를 이해하는 것은 매우 중요합니다.')]
    retrieve_result = loop.run_until_complete(test_retrieve(query=query))
    # [Document(id='6be5ec21-4d2e-4acd-9dcd-c3f62eb640f9', metadata={'source': 'data/history.txt'}, page_content='한국의 역사는 수천 년에 걸쳐 이어져 온 긴 여정 속에서 다양한 문화와 전통이 형성되고 발전해 왔습니다. 고조선에서 시작해 삼국 시대의 경쟁, 그리고 통일 신라와 고려를 거쳐 조선까지, 한반도는 많은 변화를 겪었습니다.\n\n고조선은 기원전 2333년 단군왕검에 의해 세워졌다고 전해집니다. 이는 한국 역사상 최초의 국가로, 한민족의 시원이라 할 수 있습니다. 이후 기원전 1세기경에는 한반도와 만주 일대에서 여러 소국이 성장하며 삼한 시대로 접어듭니다.\n\n4세기경, 고구려, 백제, 신라의 삼국이 한반도의 주요 세력으로 부상했습니다. 이 시기는 삼국이 각각 문화와 기술, 무력을 발전시키며 경쟁적으로 성장한 시기로, 한국 역사에서 중요한 전환점을 마련했습니다. 특히 고구려는 북방의 강대국으로 성장하여 중국과도 여러 차례 전쟁을 벌였습니다.\n\n7세기 말, 신라는 당나라와 연합하여 백제와 고구려를 차례로 정복하고, 한반도 최초의 통일 국가인 통일 신라를 건립합니다. 이 시기에 신라는 불교를 국교로 채택하며 문화와 예술이 크게 발전했습니다.\n\n그러나 10세기에 이르러 신라는 내부의 분열과 외부의 압력으로 쇠퇴하고, 이를 대체하여 고려가 성립됩니다. 고려 시대에는 과거제도의 도입과 더불어 청자 등 고려 고유의 문화가 꽃피었습니다.\n\n조선은 1392년 이성계에 의해 건국되어, 1910년까지 이어졌습니다. 조선 초기에는 세종대왕이 한글을 창제하여 백성들의 문해율을 높이는 등 문화적, 과학적 성취가 이루어졌습니다. 그러나 조선 후기에는 내부적으로 실학의 발전과 함께 사회적 변화가 모색되었으나, 외부로부터의 압력은 점차 커져만 갔습니다.\n\n19세기 말부터 20세기 초에 걸쳐 한국은 제국주의 열강의 침략을 받으며 많은 시련을 겪었습니다. 1910년, 한국은 일본에 의해 강제로 병합되어 35년간의 식민 지배를 받게 됩니다. 이 기간 동안 한국인들은 독립을 위한 다양한 운동을 전개했으며, 이는 1945년 일본의 패망으로 이어지는 독립으로 결실을 맺었습니다.\n\n해방 후 한반도는 남북으로 분단되어 각각 다른 정부가 수립되었고, 1950년에는 한국전쟁이 발발하여 큰 피해를 입었습니다. 전쟁 후 남한은 빠른 경제 발전을 이루며 오늘날에 이르렀습니다.\n\n한국의 역사는 오랜 시간 동안 수많은 시련과 도전을 겪으며 형성된 깊은 유산을 지니고 있습니다. 오늘날 한국은 그 역사적 배경 위에서 세계적으로 중요한 역할을 하고 있으며, 과거의 역사가 현재와 미래에 어떻게 영향을 미치는지를 이해하는 것은 매우 중요합니다.')]
    chain_result = loop.run_until_complete(test_chain(query=query))
    """
    한국의 역사는 고조선에서 시작하여 삼국 시대의 경쟁, 통일 신라와 고려를 거쳐 조선에 이르기까지 오랜 변화를 겪었습니다.
    
    *   **고조선**: 기원전 2333년 단군왕검에 의해 세워졌다고 전해지는 한국 역사상 최초의 국가입니다.
    *   **삼한 시대**: 기원전 1세기경부터 한반도와 만주 일대에서 여러 소국이 성장한 시기입니다.
    *   **삼국 시대**: 4세기경 고구려, 백제, 신라의 삼국이 주요 세력으로 부상하여 문화와 기술, 무력을 발전시키며 경쟁했습니다. 특히 고구려는 북방의 강대국으로 성장했습니다.
    *   **통일 신라**: 7세기 말, 신라가 당나라와 연합하여 백제와 고구려를 정복하고 한반도 최초의 통일 국가를 건립했습니다. 이 시기에는 불교를 국교로 채택하며 문화와 예술이 크게 발전했습니다.
    *   **고려**: 10세기 신라의 쇠퇴를 대체하여 성립되었습니다. 과거제도가 도입되었고 청자 등 고려 고유의 문화가 꽃피웠습니다.
    *   **조선**: 1392년 이성계에 의해 건국되어 1910년까지 이어졌습니다. 세종대왕의 한글 창제 등 문화적, 과학적 성취가 있었으나, 후기에는 내부적 변화 모색과 함께 외부로부터의 압력이 커졌습니다.
    *   **근대 격동기**: 19세기 말부터 20세기 초, 제국주의 열강의 침략을 겪고 1910년 일본에 강제 병합되어 35년간 식민 지배를 받았습니다. 1945년 일본의 패망으로 독립을 맞이했습니다.
    *   **현대**: 해방 후 한반도는 남북으로 분단되었고, 1950년 한국전쟁이 발발하여 큰 피해를 입었습니다. 전쟁 후 남한은 빠른 경제 발전을 이루어 오늘날에 이르렀습니다.
    
    한국의 역사는 수많은 시련과 도전을 겪으며 형성된 깊은 유산을 지니고 있으며, 오늘날에도 세계적으로 중요한 역할을 하고 있습니다.
    """
