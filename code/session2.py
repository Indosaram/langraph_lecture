"""
2교시: 단일 노드 에이전트 — 타겟 맞춤형 카피 생성기
State 정의 → Node 구현 → Graph 조립 → 실행
"""
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

# ========== 1. State 정의 ==========
class CopywriterState(TypedDict):
    product_name: str
    target_audience: str
    tone: str
    usp: str
    ad_copy: str

# ========== 2. LLM 초기화 ==========
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ========== 3. Node 구현 ==========
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

# ========== 4. Graph 조립 ==========
graph_builder = StateGraph(CopywriterState)
graph_builder.add_node("copywriter", copywriter_node)
graph_builder.add_edge(START, "copywriter")
graph_builder.add_edge("copywriter", END)
graph = graph_builder.compile()

# ========== 5. 실행 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 2교시: 단일 노드 카피 생성기")
    print("=" * 50)
    
    result = graph.invoke({
        "product_name": "글로우핏 콜라겐 젤리",
        "target_audience": "25-35세 여성, 피부 관리에 관심이 높고 간편한 이너뷰티 제품 선호",
        "tone": "트렌디하고 감각적인, MZ세대 감성",
        "usp": "하루 1포로 콜라겐 5,000mg 섭취, 맛있는 복숭아 맛",
        "ad_copy": ""
    })
    
    print("\n🎯 생성된 광고 카피")
    print("=" * 50)
    print(result["ad_copy"])
    print("\n✅ 2교시 완료!")
