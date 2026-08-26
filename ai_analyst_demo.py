import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# 1. .env 파일 환경변수 로드
load_dotenv()

# GEMINI_API_KEY 불러오기 (대소문자 지원)
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key")

st.title("📈 주식 대시보드 - AI 애널리스트")

# 2. 선택된 종목의 재무 데이터 (가상 데이터 예시)
financial_data = {
    "종목명": "삼성전자",
    "ROE (자기자본이익률)": "12.5%",
    "부채비율": "35.2%",
    "PER": "14.2배",
    "PBR": "1.3배",
    "최근 거래량": "15,230,000주",
    "영업이익률": "10.8%"
}

# 재무 데이터 화면 표시
st.subheader(f"📊 {financial_data['종목명']} 주요 재무 지표")
cols = st.columns(4)
cols[0].metric("ROE", financial_data["ROE (자기자본이익률)"])
cols[1].metric("부채비율", financial_data["부채비율"])
cols[2].metric("PER", financial_data["PER"])
cols[3].metric("PBR", financial_data["PBR"])

st.divider()

# 3. 'AI 밸류에이션 요약 보기' 버튼 및 Gemini API 호출
if st.button("🤖 AI 밸류에이션 요약 보기"):
    if not api_key or api_key == "여기에_내API_키_입력":
        st.warning("⚠️ .env 파일에 올바른 GEMINI_API_KEY를 입력해야 AI 분석을 시작할 수 있습니다.")
    else:
        with st.spinner("AI 애널리스트가 재무 지표를 분석 중입니다..."):
            try:
                # Gemini API 설정
                genai.configure(api_key=api_key)
                
                # gemini-3.6-flash 모델 초기화
                try:
                    model = genai.GenerativeModel("gemini-3.6-flash")
                except Exception:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                
                # 프롬프트 생성
                prompt = f"""
다음 재무 지표를 바탕으로 현재 이 기업의 재무 건전성과 투자 포인트를 딱 3줄로 요약해 줘.

[재무 데이터]
{financial_data}
"""
                # AI 답변 생성
                response = model.generate_content(prompt)
                
                # 결과 화면 출력
                st.success("💡 **AI 애널리스트 분석 리포트**")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"❌ AI 분석 요청 중 오류가 발생했습니다: {e}")
