"""
보너스 실습: FastAPI로 LangGraph 에이전트 배포하기
2교시에서 만든 단일 노드 카피 생성기를 REST API로 감싸는 예제
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

load_dotenv()


# ========== 1. State & Graph (2교시 코드 재사용) ==========
class CopywriterState(TypedDict):
    product_name: str
    target_audience: str
    tone: str
    usp: str
    ad_copy: str


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


def copywriter_node(state: CopywriterState) -> dict:
    prompt = f"""
    당신은 퍼포먼스 마케팅 전문 카피라이터입니다.
    
    아래 정보를 바탕으로 클릭률(CTR)을 극대화할 수 있는 
    광고 카피 3개를 작성해주세요.
    
    [제품/서비스] {state['product_name']}
    [타겟 오디언스] {state['target_audience']}
    [톤앤매너] {state['tone']}
    [핵심 USP] {state['usp']}
    
    각 카피는 다음을 포함해야 합니다:
    1. 헤드라인 (15자 이내)
    2. 서브 카피 (30자 이내)
    3. CTA 버튼 텍스트
    
    광고 플랫폼: Meta(Instagram/Facebook) 피드 광고
    """
    response = llm.invoke(prompt)
    return {"ad_copy": response.content}


graph_builder = StateGraph(CopywriterState)
graph_builder.add_node("copywriter", copywriter_node)
graph_builder.add_edge(START, "copywriter")
graph_builder.add_edge("copywriter", END)
graph = graph_builder.compile()


# ========== 2. FastAPI 앱 ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 카피 생성 에이전트 API 시작!")
    yield
    print("👋 API 종료")


app = FastAPI(
    title="카피 생성 에이전트 API",
    description="LangGraph 기반 광고 카피 생성 API",
    lifespan=lifespan,
)


# 요청/응답 모델 정의
class CopyRequest(BaseModel):
    product_name: str
    target_audience: str
    tone: str = "트렌디하고 감각적인"
    usp: str


class CopyResponse(BaseModel):
    ad_copy: str


@app.post("/generate", response_model=CopyResponse)
async def generate_copy(request: CopyRequest):
    """광고 카피를 생성합니다"""
    result = graph.invoke({
        "product_name": request.product_name,
        "target_audience": request.target_audience,
        "tone": request.tone,
        "usp": request.usp,
        "ad_copy": ""
    })
    return CopyResponse(ad_copy=result["ad_copy"])


@app.get("/health")
async def health():
    return {"status": "ok"}


# ========== 3. 실행 ==========
# uv run fastapi dev code/server.py
