---
theme: default
title: "퍼포먼스 마케팅 AX를 위한 LangGraph 실습"
info: |
  ## 퍼포먼스 마케팅 AX를 위한 LangGraph 실습
  AI 에이전트로 마케팅 워크플로우를 혁신하는 4시간 핸즈온 워크숍
class: text-center
drawings:
  persist: false
transition: slide-left
mdc: true
---

# 퍼포먼스 마케팅 AX를 위한<br>LangGraph 실습

AI 에이전트로 마케팅 워크플로우를 혁신하는 4시간 핸즈온 워크숍

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    시작하기 <carbon:arrow-right class="inline"/>
  </span>
</div>

<style>
h1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>

---

# 강사 소개

<div class="grid grid-cols-[1fr_2fr] gap-8 mt-4 items-center">
<div>
<img src="https://avatars.githubusercontent.com/u/47408490?v=4" class="rounded-full w-48 mx-auto" />
</div>
<div>

### 윤인도

- 서울대학교 기계항공공학부 학/석 졸업
- SAP Labs Korea 백엔드 엔지니어
- 인프런, 클래스101, 베어유 등 온라인클래스 강의

<br>

- https://devbull.xyz
- https://www.linkedin.com/in/indo-yoon-20638a117/

</div>
</div>

---

# 워크숍 개요

<div class="grid grid-cols-2 gap-8">
<div>

### 📋 기본 정보

- ⏱️ **총 소요 시간**: 4시간 (240분)
- 🎯 **대상**: 퍼포먼스 마케터, 그로스 해커
- 📈 **난이도**: 입문 → 중급 (단계적 상승)
- 💻 **사전 준비**: Python 기초, 노트북 지참

</div>
<div>

### 🛠️ 사용 기술

- **LLM**: Google Gemini 2.5 Flash
- **프레임워크**: LangGraph + LangChain
- **검색**: Tavily AI Search
- **언어**: Python 3.14+

</div>
</div>

---

# 커리큘럼

| 교시 | 주제 | 시간 | 핵심 개념 |
|:---:|------|:---:|---------|
| **1교시** | LangGraph 이론 및 환경 설정 | 90분 | State, Node, Edge |
| ☕ | *쉬는 시간* | 10분 | |
| **2교시** | 단일 노드 에이전트: 카피 생성기 | 40분 | StateGraph, 컴파일 |
| ☕ | *쉬는 시간* | 10분 | |
| **3교시** | Tool 연동: 트렌드 카피 기획 | 55분 | Tool, Conditional Edge |
| ☕ | *쉬는 시간* | 10분 | |
| **4교시** | Human-in-the-loop: 최종 승인 | 55분 | Checkpointer, HITL |

> 💡 각 교시마다 **직접 코딩하는 실습**이 포함되어 있습니다.

<style>
table { font-size: 0.9em; }
</style>

---
src: ./session1.md
---

---
src: ./session2.md
---

---
src: ./session3.md
---

---
src: ./session4.md
---
