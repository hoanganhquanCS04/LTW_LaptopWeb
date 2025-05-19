from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import json
import traceback
from typing import List, Dict, Any

# Load environment variables
load_dotenv()


llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY"), 
    )


# Load data from JSON file
def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def format_for_vectorstore(data: List[Dict[str, Any]]):
    texts = []
    metadatas = []
    
    for item in data:
        # Combine title and description for better matching
        text = f"{item['title']} {item['description']}"
        texts.append(text)
        
        # Keep all original data as metadata
        metadata = {
            "title": item['title'],
            "link": item['link'],
            "description": item['description']
        }
        metadatas.append(metadata)
    
    return texts, metadatas

# RAG function to answer questions
def answer_question(question: str, vector_store: InMemoryVectorStore, embeddings) -> str:
    try:
        # Create prompt template
        prompt_template = PromptTemplate.from_template("""
        Bạn là trợ lý hướng dẫn về FFmpeg.
        Dựa trên câu hỏi của người dùng, hãy gợi ý các video hướng dẫn FFmpeg phù hợp.
        Luôn đưa vào link đến video hướng dẫn liên quan trong câu trả lời của bạn.
        Nếu câu hỏi của người dùng không khớp với thông tin có sẵn, hãy lịch sự nói rằng bạn không có thông tin đó.
        
        Câu hỏi: {question}
        
        Thông tin liên quan:
        {context}
        
        Trả lời bằng tiếng Việt:
        """)
        
        # Search for documents - sử dụng similarity_search
        docs = vector_store.similarity_search(question, k=2)
        
        if not docs:
            return "Tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong các bài hướng dẫn FFmpeg hiện có."
        
        # Format context
        context_parts = []
        for doc in docs:
            context_parts.append(
                f"Tiêu đề: {doc.metadata['title']}\n"
                f"Mô tả: {doc.metadata['description']}\n"
                f"Link: {doc.metadata['link']}\n"
            )
        
        context = "\n".join(context_parts)
        
        chain = (
            {"question": lambda x: x, "context": lambda x: context}
            | prompt_template
            | llm
            | StrOutputParser()
        )
        
        # Execute chain
        result = chain.invoke(question)
        return result
        
    except Exception as e:
        traceback.print_exc()  # In ra stack trace đầy đủ
        return f"Xin lỗi, đã xảy ra lỗi khi tìm kiếm thông tin: {str(e)}"

# Main function
def main():
    print("Đang khởi tạo chatbot FFmpeg...")
    
    try:
        # Load data
        data = load_json_data("playlist_videos.json")
        
        # Format data
        texts, metadatas = format_for_vectorstore(data)
        
        # Initialize embeddings
        print("Đang khởi tạo mô hình embedding...")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            print("Đã khởi tạo HuggingFaceEmbeddings thành công")
        except Exception as e:
            
            # Nếu HuggingFaceEmbeddings thất bại, thử dùng SentenceTransformerEmbeddings
            from langchain_community.embeddings import SentenceTransformerEmbeddings
            embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            print("Đã khởi tạo SentenceTransformerEmbeddings thành công")
        
        # Create vector store
        vector_store = InMemoryVectorStore.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas
        )
        print("Đã tạo vector store trong bộ nhớ.")
        
        print("Chatbot sẵn sàng! Hãy đặt câu hỏi về FFmpeg (gõ 'exit' để thoát).")
        
        # Chat loop
        while True:
            user_question = input("\nCâu hỏi của bạn: ")
            if user_question.lower() == 'exit':
                print("Tạm biệt!")
                break
            response = answer_question(user_question, vector_store, embeddings)
            print(f"\n{response}\n")
                
    except Exception as e:
        print(f"Lỗi khi khởi tạo: {str(e)}")
        traceback.print_exc()  # In ra stack trace đầy đủ

if __name__ == "__main__":
    main()