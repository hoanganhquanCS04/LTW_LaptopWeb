from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Avg
from .models import ChatMessage
from product.models import Product, Category
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import traceback
import json

# Load environment variables
load_dotenv()

# Khởi tạo LLM Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# Hàm lấy base url
def get_base_url(request=None):
    if request:
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        return f"{scheme}://{host}"
    return "http://127.0.0.1:8000"

# Hàm lấy dữ liệu sản phẩm từ CSDL và format cho vectorstore
def get_all_products_for_vectorstore(request=None):
    products = Product.objects.filter(status='True')
    texts = []
    metadatas = []
    base_url = get_base_url(request)
    for p in products:
        text = f"{p.title} {p.description or ''} {p.category.title}"
        metadata = {
            "title": p.title,
            "price": str(p.price),
            "category": p.category.title,
            "description": p.description[:150] if p.description else '',
            "url": f"{base_url}/product/{p.id}/{p.slug}/"
        }
        texts.append(text)
        metadatas.append(metadata)
    return texts, metadatas

# Khởi tạo embeddings và vectorstore (cache lại để không load lại mỗi request)
embeddings = None
vector_store = None
def get_vector_store(request=None):
    global embeddings, vector_store
    if embeddings is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    if vector_store is None:
        texts, metadatas = get_all_products_for_vectorstore(request)
        vector_store = InMemoryVectorStore.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas
        )
    return vector_store, embeddings

# Prompt template cho Gemini
prompt_template = PromptTemplate.from_template("""
Bạn là tư vấn viên bán hàng laptop và phụ kiện. 
Trả lời ngắn gọn, tự nhiên, rõ ràng, dễ hiểu, không rập khuôn.
Nếu khách hỏi giá sản phẩm, chỉ trả lời đúng giá và link.
Nếu khách hỏi hãng, loại, hoặc muốn gợi ý, chỉ liệt kê tối đa 3 sản phẩm phù hợp nhất, mỗi sản phẩm 1 dòng, có số thứ tự, tên, giá, link.
Nếu khách hỏi sản phẩm đắt nhất/rẻ nhất, chỉ trả lời đúng 1 sản phẩm.
Nếu khách hỏi về mục đích sử dụng, hãy gợi ý sản phẩm phù hợp nhất và lý do.
Nếu không rõ, hãy hỏi lại khách cho rõ hơn.

Câu hỏi khách: {question}

Dữ liệu sản phẩm liên quan:
{context}

Trả lời:
""")

# Hàm trả lời câu hỏi
def answer_question(question, vector_store, embeddings):
    try:
        # Lấy 5 sản phẩm liên quan nhất
        docs = vector_store.similarity_search(question, k=5)
        if not docs:
            return "Xin lỗi, tôi không tìm thấy sản phẩm phù hợp với yêu cầu của bạn."
        # Format context
        context_parts = []
        for idx, doc in enumerate(docs, 1):
            context_parts.append(
                f"{idx}. {doc.metadata['title']} - {doc.metadata['price']} đồng. {doc.metadata['url']}"
            )
        context = "\n".join(context_parts)
        # Tạo chain Gemini
        chain = (
            {"question": lambda x: x, "context": lambda x: context}
            | prompt_template
            | llm
            | StrOutputParser()
        )
        result = chain.invoke(question)
        return result
    except Exception as e:
        traceback.print_exc()
        return f"Xin lỗi, đã xảy ra lỗi khi xử lý: {str(e)}"

# API endpoint cho chatbot
@csrf_exempt
@require_POST
def ask_chatbot(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        vector_store, embeddings = get_vector_store(request)
        bot_response = answer_question(user_message, vector_store, embeddings)
        ChatMessage.objects.create(user_message=user_message, bot_response=bot_response)
        return JsonResponse({'response': bot_response})
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)