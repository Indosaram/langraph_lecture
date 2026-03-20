"""
1교시: API 연결 테스트
Google Gemini API가 정상 동작하는지 확인합니다.
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os

load_dotenv()

print("=" * 50)
print("🔧 1교시: 환경 설정 및 API 연결 테스트")
print("=" * 50)

# 1. API 키 확인
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY가 .env에 설정되지 않았습니다.")
    exit(1)
print(f"✅ API Key 로드: {api_key[:10]}...")

# 2. Gemini 모델 초기화 및 테스트
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

response = llm.invoke("안녕하세요! LangGraph 실습을 위한 테스트입니다.")
print(f"\n💬 Gemini 응답:\n{response.content}")
print("\n✅ Google Gemini API 연결 성공!")

# 3. Tavily API 키 확인
tavily_key = os.getenv("TAVILY_API_KEY")
if tavily_key:
    print(f"✅ Tavily API Key 로드: {tavily_key[:10]}...")
else:
    print("⚠️  TAVILY_API_KEY가 설정되지 않았습니다. (3교시에서 필요)")
