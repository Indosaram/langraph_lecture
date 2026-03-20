"""
3교시: Tool 연동 에이전트 — 검색 기반 트렌드 카피 기획
Tavily 검색 → 트렌드 추출 → 카피 생성 → 자체 평가 루프
"""
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
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

# ========== 2. LLM & Tool 초기화 ==========
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ========== 3. Node 구현 ==========
def search_trends_node(state: TrendCopyState) -> dict:
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
    
    return {
        "search_query": query,
        "search_results": summaries
    }


def extract_trends_node(state: TrendCopyState) -> dict:
    prompt = f"""
    아래 검색 결과를 분석하여,
    '{state['product_name']}' 마케팅에 활용할 수 있는 
    최신 트렌드 키워드 5개를 추출해주세요.
    
    [검색 결과]
    {chr(10).join(state['search_results'][:5])}
    
    각 키워드에 대해 간단한 활용 근거도 함께 제시해주세요.
    
    출력 형식:
    1. [키워드] - [활용 근거]
    2. ...
    """
    
    response = llm.invoke(prompt)
    keywords = response.content.split("\n")
    print(f"📊 트렌드 키워드 {len(keywords)}개 추출")
    return {"trend_keywords": keywords}


def trend_copywriter_node(state: TrendCopyState) -> dict:
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


def quality_evaluator_node(state: TrendCopyState) -> dict:
    prompt = f"""
    아래 광고 카피의 품질을 1-10점으로 평가해주세요.
    
    [광고 카피]
    {state['ad_copy']}
    
    평가 기준:
    1. 타겟 적합성 (타겟 오디언스의 관심사/니즈 반영)
    2. 트렌드 반영도 (최신 트렌드가 자연스럽게 녹아있는지)
    3. 클릭 유도력 (CTR을 높일 수 있는 후킹 요소)
    4. 메시지 명확성 (USP가 명확히 전달되는지)
    
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


# ========== 4. 조건부 엣지 ==========
def should_retry(state: TrendCopyState) -> str:
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


# ========== 5. Graph 조립 ==========
graph_builder = StateGraph(TrendCopyState)

graph_builder.add_node("search_trends", search_trends_node)
graph_builder.add_node("extract_trends", extract_trends_node)
graph_builder.add_node("trend_copywriter", trend_copywriter_node)
graph_builder.add_node("quality_evaluator", quality_evaluator_node)

graph_builder.add_edge(START, "search_trends")
graph_builder.add_edge("search_trends", "extract_trends")
graph_builder.add_edge("extract_trends", "trend_copywriter")
graph_builder.add_edge("trend_copywriter", "quality_evaluator")

graph_builder.add_conditional_edges(
    "quality_evaluator",
    should_retry,
    {
        "pass": END,
        "retry": "trend_copywriter"
    }
)

graph = graph_builder.compile()

# ========== 6. 실행 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 3교시: 검색 기반 트렌드 카피 에이전트")
    print("=" * 50)
    
    result = graph.invoke({
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
        "iteration_count": 0
    })
    
    print("\n" + "=" * 50)
    print(f"🎯 최종 카피 (품질: {result['quality_score']}/10, "
          f"반복: {result['iteration_count']}회)")
    print("=" * 50)
    print(result["ad_copy"])
    print("\n✅ 3교시 완료!")

    # ========== 실습 과제 1: 다른 제품으로 실행 ==========
    print("\n" + "=" * 50)
    print("🏋️ 과제 1: 다른 제품으로 실행")
    print("=" * 50)

    result_ex1 = graph.invoke({
        "product_name": "스마트 러닝화 에어플로우",
        "target_audience": "20-40대 러닝 입문자, 편한 신발 선호",
        "tone": "활기차고 도전적인, 스포츠 감성",
        "usp": "AI 쿠셔닝 기술, 러닝 자세 분석 앱 연동",
        "ad_copy": "",
        "search_query": "",
        "search_results": [],
        "trend_keywords": [],
        "quality_score": 0,
        "feedback": "",
        "iteration_count": 0
    })

    print(f"\n🎯 최종 카피 (품질: {result_ex1['quality_score']}/10)")
    print(result_ex1["ad_copy"])

    # ========== 실습 과제 2: 평가 기준 커스터마이징 ==========
    print("\n" + "=" * 50)
    print("🏋️ 과제 2: 평가 기준 커스터마이징")
    print("=" * 50)

    def quality_evaluator_custom(state: TrendCopyState) -> dict:
        prompt = f"""
        아래 광고 카피의 품질을 1-10점으로 평가해주세요.
        
        [광고 카피]
        {state['ad_copy']}
        
        평가 기준:
        1. 타겟 적합성
        2. 트렌드 반영도
        3. 클릭 유도력
        4. 메시지 명확성
        5. 브랜드 가이드라인 준수
        
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
            score = 5
        return {
            "quality_score": score,
            "feedback": response.content,
            "iteration_count": state.get("iteration_count", 0) + 1
        }

    def should_retry_custom(state: TrendCopyState) -> str:
        if state["quality_score"] >= 7:  # 7점으로 변경
            print(f"✅ 품질 통과! (점수: {state['quality_score']})")
            return "pass"
        elif state["iteration_count"] >= 5:  # 5회로 변경
            print(f"⚠️ 최대 반복 도달 (점수: {state['quality_score']})")
            return "pass"
        else:
            print(f"🔄 재작성 필요 (점수: {state['quality_score']}, "
                  f"반복: {state['iteration_count']})")
            return "retry"

    # 커스텀 그래프 조립
    graph_custom = StateGraph(TrendCopyState)
    graph_custom.add_node("search_trends", search_trends_node)
    graph_custom.add_node("extract_trends", extract_trends_node)
    graph_custom.add_node("trend_copywriter", trend_copywriter_node)
    graph_custom.add_node("quality_evaluator", quality_evaluator_custom)
    graph_custom.add_edge(START, "search_trends")
    graph_custom.add_edge("search_trends", "extract_trends")
    graph_custom.add_edge("extract_trends", "trend_copywriter")
    graph_custom.add_edge("trend_copywriter", "quality_evaluator")
    graph_custom.add_conditional_edges(
        "quality_evaluator", should_retry_custom,
        {"pass": END, "retry": "trend_copywriter"}
    )
    graph_ex2 = graph_custom.compile()

    result_ex2 = graph_ex2.invoke({
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
        "iteration_count": 0
    })

    print(f"\n🎯 커스텀 평가 결과 (품질: {result_ex2['quality_score']}/10, "
          f"반복: {result_ex2['iteration_count']}회)")
    print(result_ex2["ad_copy"])
    print("\n✅ 과제 2 완료!")

