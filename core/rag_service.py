import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import settings


# 初始化嵌入模型 (复用之前配置好的 nomic-embed-text)
embedding_model = OllamaEmbeddings(
    model=settings.OLLAMA_EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)
# 修改存储路径到项目根目录，而不是core目录下
DB_PATH = settings.CHROMA_DB_PATH
# 或者直接指定绝对路径
# DB_PATH = "./chroma_rag_db"  # 这会存储在项目根目录


# 把数据存储到语义数据库
def process_and_stor_file(file_path, user_id):
     """ 后台任务：解析文件并存入该用户的专属向量库"""

     if file_path.endswith(".pdf"):
         doc = PyPDFLoader(file_path).load()
     elif file_path.endswith(".txt"):
         doc = TextLoader(file_path,encoding="utf-8").load()
     else:
         print("不支持的文件格式")
         return

     collection_name = f"user_{user_id}_docs"
     doc_spliter = RecursiveCharacterTextSplitter(
         chunk_size=300,
         chunk_overlap=50,
         add_start_index=True
     )
     all_docs = doc_spliter.split_documents(doc)

     my_company_collection = Chroma(
         collection_name=collection_name,
         embedding_function=embedding_model,
         persist_directory=DB_PATH
     )

     my_company_collection.add_documents(all_docs)

def retrive_user_from_knowledge(user_id,search_query):
    """
    供智能体调用的检索工具：只查当前用户的专属知识库
    """
    # 指定白哦名称
    collection_name = f"user_{user_id}_docs"

    my_company_collection = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=DB_PATH
    )

    result_docs = my_company_collection.similarity_search(search_query,k=2)
    if not result_docs:
        return "未在您的知识库中检索到相关信息。"

    context = "\n\n".join(
        f"【您的专属参考资料】:\n{doc.page_content}" for doc in result_docs
    )
    return context
