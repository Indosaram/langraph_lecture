"""
4교시: Human-in-the-loop — 트렌드 카피 최종 승인 및 피드백
3교시 그래프 + Checkpointer + 인간 검토 노드
"""
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from tavily import TavilyClient
import os

load_dotenv()

# ========== 1. State 정의 ==========
class TrendCopyState(TypedDict):
    product_name: str
    target_audience: str
    tone: str
    usp: str
    ad_copy: str
    search_query: str
    search_results: list[str]
    trend_keywords: list[str]
    quality_score: int
    feedback: str
    iteration_count: int

class HITLCopyState(TrendCopyState):
    human_feedback: str
    human_approved: bool

# ========== 2. LLM & Tool 초기화 ==========
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
checkpointer = MemorySaver()

# ========== 3. Node 구현 (3교시에서 가져옴) ==========
def search_trends_node(state: HITLCopyState) -> dict:
    query = (
        f"{state['product_name']} {state['target_audience']} "
        f"최신 트렌드 마케팅"
    )
    results = tavily_client.search(
        query=query,
        max_results=5,
        search_depth="advanced"
    )
    summaries = [r["content"] for r in results["results"]]
    print(f"🔍 검색 완료: {len(summaries)}건의 결과")
    return {"search_query": query, "search_results": summaries}


def extract_trends_node(state: HITLCopyState) -> dict:
    prompt = f"""
    아래 검색 결과를 분석하여,
    '{state['product_name']}' 마케팅에 활용할 수 있는 
    최신 트렌드 키워드 5개를 추출해주세요.
    
    [검색 결과]
    {chr(10).join(state['search_results'][:5])}
    
    출력 형식:
    1. [키워드] - [활용 근거]
    """
    response = llm.invoke(prompt)
    keywords = response.content.split("\n")
    print(f"📊 트렌드 키워드 {len(keywords)}개 추출")
    return {"trend_keywords": keywords}


def trend_copywriter_node(state: HITLCopyState) -> dict:
    prompt = f"""
    당신은 데이터 기반 퍼포먼스 마케팅 카피라이터입니다.
    아래의 실시간 트렌드 분석 결과를 반영하여 
    전환율(CVR)을 극대화할 광고 카피 3개를 작성해주세요.
    
    [제품/서비스] {state['product_name']}
    [타겟 오디언스] {state['target_audience']}
    [톤앤매너] {state['tone']}
    [핵심 USP] {state['usp']}
    
    [📊 실시간 트렌드 키워드]
    {chr(10).join(state['trend_keywords'])}
    
    [📊 검색 결과 컨텍스트]
    {chr(10).join(state['search_results'][:3])}
    
    출력 형식 (카피 3개):
    ---
    [카피 #N]
    헤드라인: (15자 이내)
    서브카피: (30자 이내)  
    CTA: (버튼 텍스트)
    반영 트렌드: (어떤 트렌드를 왜 적용했는지)
    ---
    """
    response = llm.invoke(prompt)
    return {"ad_copy": response.content}


def quality_evaluator_node(state: HITLCopyState) -> dict:
    prompt = f"""
    아래 광고 카피의 품질을 1-10점으로 평가해주세요.
    
    [광고 카피]
    {state['ad_copy']}
    
    평가 기준:
    1. 타겟 적합성
    2. 트렌드 반영도
    3. 클릭 유도력
    4. 메시지 명확성
    
    출력 형식:
    점수: [숫자만]
    피드백: [구체적인 개선 방향]
    """
    response = llm.invoke(prompt)
    try:
        score = int(''.join(filter(str.isdigit, 
                    response.content.split('\n')[0]))[:2])
        score = min(score, 10)
    except (ValueError, IndexError):
        print("⚠️ 점수 파싱 실패, 기본값 5점 적용")
        score = 5
    
    return {
        "quality_score": score,
        "feedback": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1
    }


# ========== 4교시 전용 노드 ==========
def human_review_node(state: HITLCopyState) -> dict:
    """이 노드 실행 직전에 그래프가 일시 정지됩니다"""
    print("\n" + "=" * 50)
    print("👤 마케터 검토 대기 중...")
    print("=" * 50)
    print(f"\n📝 검토 대상 카피:\n{state['ad_copy']}")
    print(f"\n📊 AI 품질 평가: {state['quality_score']}/10")
    print(f"💬 AI 피드백: {state['feedback']}")
    return {}


def revise_copy_node(state: HITLCopyState) -> dict:
    """마케터 피드백을 반영하여 카피 수정"""
    prompt = f"""
    기존 광고 카피를 마케터의 피드백을 반영하여 수정해주세요.
    
    [기존 카피]
    {state['ad_copy']}
    
    [마케터 피드백]
    {state['human_feedback']}
    
    피드백을 정확히 반영하면서도 기존 카피의 장점은 유지해주세요.
    """
    response = llm.invoke(prompt)
    return {"ad_copy": response.content}


def final_output_node(state: HITLCopyState) -> dict:
    print("\n🎉 최종 승인된 광고 카피")
    print(f"\n{state['ad_copy']}")
    print(f"\n👤 마케터 코멘트: {state['human_feedback']}")
    return {}


# ========== 분기 로직 ==========
def should_retry(state: HITLCopyState) -> str:
    if state["quality_score"] >= 8:
        print(f"✅ 품질 통과! (점수: {state['quality_score']})")
        return "pass"
    elif state["iteration_count"] >= 3:
        print(f"⚠️ 최대 반복 도달 (점수: {state['quality_score']})")
        return "pass"
    else:
        print(f"🔄 재작성 필요 (점수: {state['quality_score']}, "
              f"반복: {state['iteration_count']})")
        return "retry"


def route_after_review(state: HITLCopyState) -> str:
    if state.get("human_approved", False):
        return "approved"
    else:
        return "revise"


# ========== 5. Graph 조립 ==========
graph_builder = StateGraph(HITLCopyState)

graph_builder.add_node("search_trends", search_trends_node)
graph_builder.add_node("extract_trends", extract_trends_node)
graph_builder.add_node("trend_copywriter", trend_copywriter_node)
graph_builder.add_node("quality_evaluator", quality_evaluator_node)
graph_builder.add_node("human_review", human_review_node)
graph_builder.add_node("revise_copy", revise_copy_node)
graph_builder.add_node("final_output", final_output_node)

graph_builder.add_edge(START, "search_trends")
graph_builder.add_edge("search_trends", "extract_trends")
graph_builder.add_edge("extract_trends", "trend_copywriter")
graph_builder.add_edge("trend_copywriter", "quality_evaluator")

graph_builder.add_conditional_edges(
    "quality_evaluator", should_retry,
    {"pass": "human_review", "retry": "trend_copywriter"}
)
graph_builder.add_conditional_edges(
    "human_review", route_after_review,
    {"approved": "final_output", "revise": "revise_copy"}
)
graph_builder.add_edge("revise_copy", "human_review")
graph_builder.add_edge("final_output", END)

graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]
)

# ========== 6. 실행 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 4교시: Human-in-the-loop 카피 승인 워크플로우")
    print("=" * 50)
    
    config = {"configurable": {"thread_id": "marketing-copy-review-1"}}
    
    # ---- Step 1: 검색 → 추출 → 생성 → 평가 → 멈춤 ----
    print("\n📍 Step 1: 에이전트 실행 (human_review 직전에 멈춤)")
    result = graph.invoke(
        {
            "product_name": "글로우핏 콜라겐 젤리",
            "target_audience": "25-35세 여성, 이너뷰티 관심",
            "tone": "트렌디하고 감각적인",
            "usp": "하루 1포, 콜라겐 5,000mg, 복숭아 맛",
            "ad_copy": "",
            "search_query": "",
            "search_results": [],
            "trend_keywords": [],
            "quality_score": 0,
            "feedback": "",
            "iteration_count": 0,
            "human_feedback": "",
            "human_approved": False,
        },
        config
    )
    
    state = graph.get_state(config)
    print(f"\n⏸️ 그래프 일시 정지! 다음 노드: {state.next}")
    print(f"📝 현재 카피 (일부):\n{result.get('ad_copy', '')[:200]}...")
    
    # ---- Step 2+: 인터랙티브 피드백 루프 ----
    while True:
        approved = input("\n승인하시겠습니까? (y/n): ").strip().lower()
        feedback = input("피드백을 입력하세요: ").strip()

        graph.update_state(
            config,
            values={
                "human_approved": approved == "y",
                "human_feedback": feedback
            },
            as_node="human_review"
        )

        result = graph.invoke(None, config)
        state = graph.get_state(config)

        if not state.next:
            # 그래프가 END에 도달 (승인됨)
            break

        # 수정 후 다시 human_review 직전에 멈춤
        print(f"\n📝 수정된 카피:\n{result.get('ad_copy', '')[:300]}...")

    print("\n" + "=" * 50)
    print("✅ 4교시 완료! 전체 HITL 워크플로우 검증 성공!")
    print("=" * 50)

    # ========== 실습 과제 1: 톤 변경 시나리오 ==========
    print("\n" + "=" * 50)
    print("🏋️ 과제 1: 피드백 시나리오 체험 (톤 변경)")
    print("=" * 50)

    config_ex1 = {"configurable": {"thread_id": "exercise-tone-change"}}

    graph.invoke(
        {
            "product_name": "글로우핏 콜라겐 젤리",
            "target_audience": "25-35세 여성, 이너뷰티 관심",
            "tone": "트렌디하고 감각적인",
            "usp": "하루 1포, 콜라겐 5,000mg, 복숭아 맛",
            "ad_copy": "",
            "search_query": "",
            "search_results": [],
            "trend_keywords": [],
            "quality_score": 0,
            "feedback": "",
            "iteration_count": 0,
            "human_feedback": "",
            "human_approved": False,
        },
        config_ex1
    )

    while True:
        approved = input("\n[과제1] 승인하시겠습니까? (y/n): ").strip().lower()
        feedback = input("[과제1] 피드백을 입력하세요: ").strip()

        graph.update_state(
            config_ex1,
            values={
                "human_approved": approved == "y",
                "human_feedback": feedback
            },
            as_node="human_review"
        )

        result_ex1 = graph.invoke(None, config_ex1)
        state_ex1 = graph.get_state(config_ex1)

        if not state_ex1.next:
            break

        print(f"📝 수정된 카피:\n{result_ex1.get('ad_copy', '')[:300]}...")

    print("\n✅ 과제 1 완료!")

