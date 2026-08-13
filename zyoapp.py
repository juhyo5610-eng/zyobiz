import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import base64
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="아보미 Abomi - 미국주식 & 금융 데이터", layout="wide", page_icon="🌱")

# === Base64 로고 로더 ===
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

logo_b64 = get_base64_image("abomi_logo.jpg")

# === 테마 및 세션 상태 초기화 ===
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "System"

if "my_portfolio" not in st.session_state:
    st.session_state["my_portfolio"] = [
        {"Ticker": "NVDA", "종목명": "NVIDIA Corp", "매수가($)": 115.00, "보유주수": 20},
        {"Ticker": "AAPL", "종목명": "Apple Inc", "매수가($)": 210.00, "보유주수": 15},
        {"Ticker": "QQQ", "종목명": "Invesco QQQ Trust", "매수가($)": 460.00, "보유주수": 10},
        {"Ticker": "SCHD", "종목명": "Schwab US Dividend Equity", "매수가($)": 26.50, "보유주수": 50},
    ]

# === 🎨 커스텀 CSS (나눔고딕 폰트, 테마 모드, #79E963 포인트 컬러, Deploy버튼 제거, 아이콘 폰트 픽스) ===
theme_mode = st.session_state["theme_mode"]

if theme_mode == "Light":
    theme_vars = """
    :root {
        --bg-main: #f7F7F7;
        --bg-card: #FFFFFF;
        --bg-metric: #F8FAFC;
        --text-main: #1F2937;
        --text-sub: #6B7280;
        --border-color: #EBEBEB;
        --shadow-color: rgba(0, 0, 0, 0.03);
    }
    """
elif theme_mode == "Dark":
    theme_vars = """
    :root {
        --bg-main: #1E2022;
        --bg-card: #282A2D;
        --bg-metric: #33373B;
        --text-main: #F3F4F6;
        --text-sub: #9CA3AF;
        --border-color: #383C42;
        --shadow-color: rgba(0, 0, 0, 0.3);
    }
    """
else: # System
    theme_vars = """
    :root {
        --bg-main: #f7F7F7;
        --bg-card: #FFFFFF;
        --bg-metric: #F8FAFC;
        --text-main: #1F2937;
        --text-sub: #6B7280;
        --border-color: #EBEBEB;
        --shadow-color: rgba(0, 0, 0, 0.03);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #1E2022;
            --bg-card: #282A2D;
            --bg-metric: #33373B;
            --text-main: #F3F4F6;
            --text-sub: #9CA3AF;
            --border-color: #383C42;
            --shadow-color: rgba(0, 0, 0, 0.3);
        }
    }
    """

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800;900&display=swap');

{theme_vars}

/* 1. Deploy 버튼 숨기기 & 3줄 사이드바 열기/닫기 가로 메뉴 버튼 활성화 및 스타일링 */
.stAppDeployButton,
[data-testid="stAppDeployButton"] {{
    display: none !important;
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 99999 !important;
}}

/* 3줄 가로 메뉴 아이콘 버튼 (사이드바 열기 / 닫기 컨트롤) */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"] button,
button[data-testid="stBaseButton-header"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}}

/* 기존 모든 화살표 (>>, <<, <, >) SVG 및 내부 하위 요소 완전 제거 */
[data-testid="collapsedControl"] button *,
[data-testid="stSidebarCollapseButton"] button *,
[data-testid="stSidebarHeader"] button *,
button[data-testid="stBaseButton-header"] * {{
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
}}

[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarHeader"] button,
button[data-testid="stBaseButton-header"] {{
    border-radius: 8px !important;
    border: 1px solid var(--border-color) !important;
    background-color: var(--bg-card) !important;
    color: var(--text-main) !important;
    width: 38px !important;
    height: 38px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 8px var(--shadow-color) !important;
    transition: all 0.2s ease !important;
}}

/* 열림/닫힘 상관없이 오직 3줄 직선 (한자 셋 삼 三 형태) ☰ 아이콘 단 하나만 렌더링 */
[data-testid="collapsedControl"] button::before,
[data-testid="stSidebarCollapseButton"] button::before,
[data-testid="stSidebarHeader"] button::before,
button[data-testid="stBaseButton-header"]::before {{
    content: "☰" !important;
    font-size: 22px !important;
    font-weight: 900 !important;
    color: var(--text-main) !important;
    display: block !important;
    visibility: visible !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    line-height: 1 !important;
    text-align: center !important;
}}

[data-testid="collapsedControl"] button:hover::before,
[data-testid="stSidebarCollapseButton"] button:hover::before,
[data-testid="stSidebarHeader"] button:hover::before,
button[data-testid="stBaseButton-header"]:hover::before {{
    color: #79E963 !important;
}}

[data-testid="collapsedControl"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarHeader"] button:hover,
button[data-testid="stBaseButton-header"]:hover {{
    border-color: #79E963 !important;
}}

/* 2. 상단 패딩 여유 공간 확보 */
.block-container {{
    padding-top: 3.2rem !important;
    padding-bottom: 3rem !important;
    max-width: 95% !important;
}}

/* 3. 기본 글꼴 설정 (icon / symbol 요소는 제외하여 text 겹침 버그 차단) */
body, .stApp, h1, h2, h3, h4, h5, h6, p, label, input, button {{
    font-family: 'Nanum Gothic', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}

/* Streamlit 내장 머티리얼 아이콘 폰트 보존 */
[data-testid="stIcon"],
[data-testid="stIcon"] *,
span[data-testid="stIcon"],
i, 
svg,
summary [data-testid="stIcon"],
.material-symbols-outlined,
.material-symbols-rounded,
.material-icons {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
}}

/* 전체 배경 및 기본 글자색 */
.stApp {{
    background-color: var(--bg-main) !important;
    color: var(--text-main) !important;
}}

/* 사이드바 스타일링 */
section[data-testid="stSidebar"] {{
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border-color) !important;
}}

section[data-testid="stSidebar"] .stRadio label span {{
    font-family: 'Nanum Gothic', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    color: var(--text-main) !important;
}}

/* 상단 브랜딩 헤더 영역 */
.abomi-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 2px 0;
}}

.abomi-logo {{
    height: 44px;
    width: auto;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    object-fit: contain;
}}

.abomi-title-group {{
    display: flex;
    flex-direction: column;
}}

.abomi-title {{
    font-size: 26px;
    font-weight: 900;
    color: var(--text-main) !important;
    margin: 0;
    line-height: 1.1;
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Nanum Gothic', sans-serif !important;
    letter-spacing: -0.5px;
}}

.abomi-sub-tag {{
    font-size: 15px;
    font-weight: 600;
    color: var(--text-sub) !important;
    margin-left: 6px;
    font-family: 'Nanum Gothic', sans-serif !important;
}}

.abomi-tag {{
    background-color: #79E963;
    color: #0F3805 !important;
    font-size: 13px;
    font-weight: 800;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'Nanum Gothic', sans-serif !important;
}}

.abomi-subtitle {{
    font-size: 14px;
    color: var(--text-sub) !important;
    margin: 4px 0 0 0;
    font-family: 'Nanum Gothic', sans-serif !important;
}}

/* 버튼 스타일링 (#79E963 강조) */
.stButton>button {{
    background-color: #79E963 !important;
    color: #0F3805 !important;
    font-family: 'Nanum Gothic', sans-serif !important;
    font-weight: 700 !important;
    border: 1px solid #62d64c !important;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 2px 8px rgba(121, 233, 99, 0.3) !important;
}}

.stButton>button:hover {{
    background-color: #66d650 !important;
    box-shadow: 0 4px 14px rgba(121, 233, 99, 0.5) !important;
    transform: translateY(-1px) !important;
}}

/* 카드 컨테이너 요소들 */
div[data-testid="stExpander"], 
div[data-testid="stDataFrame"] {{
    background-color: var(--bg-card) !important;
    border-radius: 16px !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: 0 4px 16px var(--shadow-color) !important;
}}

div[data-testid="stExpander"] summary {{
    font-family: 'Nanum Gothic', sans-serif !important;
    font-weight: 700 !important;
    font-size: 17px !important;
    color: var(--text-main) !important;
}}

/* 지표 메트릭 박스 */
div[data-testid="stMetric"] {{
    background-color: var(--bg-metric) !important;
    border: 1px solid var(--border-color) !important;
    padding: 14px 18px !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 6px var(--shadow-color) !important;
}}

/* 슬라이더 컬러 (#79E963) */
.stSlider > div > div > div > div {{
    background-color: #79E963 !important;
}}

/* Heading & Label */
h1, h2, h3, h4, h5, h6, label, p {{
    font-family: 'Nanum Gothic', sans-serif !important;
    color: var(--text-main);
}}
</style>
""", unsafe_allow_html=True)

# === 🌟 데이터셋 후보 종목 리스트 ===
candidate_tickers = [
    "TQQQ", "SOXL", "NVDL", "CONL", "SQQQ", "FNGU", "SPXL", "TSLL", "LABU", "UPRO", 
    "MSTX", "MSTU", "SOXS", "TECL", "WEBL", "DPST", "FAS", "FAZ", "TNA", "TZA", 
    "SPY", "QQQ", "IWM", "DIA", "VOO", "IVV", "GLD", "SLV", "SCHD", "JEPI", 
    "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "AMD", "INTC",
    "PLTR", "SMCI", "COIN", "MSTR", "HOOD", "ROKU", "DKNG", "ARM", "AVGO", "QCOM",
    "MARA", "RIOT", "CLSK", "ASTS", "RKLB", "LUNR", "IONQ", "RIVN", "LCID", "NIO",
    "PYPL", "SQ", "SHOP", "SE", "BABA", "PDD", "UBER", "LYFT", "CRWD", "PANW",
    "LLY", "UNH", "JNJ", "PFE", "ABBV", "MRK", "AMGN", "HIMS", "MRNA", "GILD",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "V", "MA",
    "CAT", "DE", "BA", "LMT", "RTX", "GE", "HON", "XOM", "CVX", "WMT", "COST"
]

known_etfs = set([
    "TQQQ", "SOXL", "NVDL", "CONL", "SQQQ", "FNGU", "SPXL", "TSLL", "LABU", "UPRO", 
    "MSTX", "MSTU", "SOXS", "TECL", "WEBL", "DPST", "FAS", "FAZ", "TNA", "TZA",
    "SPY", "QQQ", "IWM", "DIA", "VOO", "IVV", "GLD", "SLV", "SCHD", "JEPI", "JEPQ"
])

SECTOR_MAP = {
    'NVDA': 'Technology', 'AAPL': 'Technology', 'MSFT': 'Technology', 'AMD': 'Technology',
    'INTC': 'Technology', 'PLTR': 'Technology', 'SMCI': 'Technology', 'AVGO': 'Technology',
    'AMZN': 'Consumer Cyclical', 'TSLA': 'Consumer Cyclical', 'GOOGL': 'Communication Services',
    'META': 'Communication Services', 'JPM': 'Financial Services', 'BAC': 'Financial Services',
    'LLY': 'Healthcare', 'UNH': 'Healthcare', 'WMT': 'Consumer Defensive', 'XOM': 'Energy'
}

# === 🌟 배치 데이터 수집 함수 (SEC 10,000+ 티커) ===
@st.cache_data(ttl=30)
def load_all_data():
    raw_quotes = []
    all_symbols = list(candidate_tickers)
    try:
        sec_resp = requests.get('https://www.sec.gov/files/company_tickers.json', headers={'User-Agent': 'AbomiApp admin@abomi.com'}, timeout=4)
        if sec_resp.status_code == 200:
            sec_data = sec_resp.json()
            sec_tickers = [v['ticker'].replace('.', '-') for v in sec_data.values()]
            all_symbols.extend(sec_tickers)
    except Exception:
        pass
        
    all_symbols = list(dict.fromkeys(all_symbols))
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        })
        session.get('https://fc.yahoo.com', timeout=4)
        crumb_resp = session.get('https://query2.finance.yahoo.com/v1/test/getcrumb', timeout=4)
        crumb = crumb_resp.text.strip()
        
        batch_size = 150
        batches = [all_symbols[i:i+batch_size] for i in range(0, len(all_symbols), batch_size)]
        
        def fetch_batch(b):
            sym_str = ','.join(b)
            url = f'https://query2.finance.yahoo.com/v7/finance/quote?symbols={sym_str}&crumb={crumb}'
            try:
                r = session.get(url, timeout=5)
                if r.status_code == 200:
                    return r.json().get('quoteResponse', {}).get('result', [])
            except Exception:
                pass
            return []

        with ThreadPoolExecutor(max_workers=20) as executor:
            batch_results = executor.map(fetch_batch, batches)
            for res in batch_results:
                raw_quotes.extend(res)
    except Exception:
        raw_quotes = []

    parsed = []
    for q in raw_quotes:
        sym = q.get('symbol')
        if not sym:
            continue
        cp = q.get('regularMarketPrice', 0) or 0
        if cp <= 0:
            continue
        chg = round(q.get('regularMarketChangePercent', 0) or 0.0, 2)
        q_type = q.get('quoteType', '')
        
        if q_type == 'ETF' or sym in known_etfs:
            sector = 'ETF'
        else:
            sector = q.get('sector', SECTOR_MAP.get(sym, '기타'))
            if not sector:
                sector = '기타'
                
        vol = q.get('regularMarketVolume', 0) or 0
        raw_cap = q.get('marketCap') or q.get('netAssets') or 100_000_000
        cap_b = round(raw_cap / 1_000_000_000, 2)
        if cap_b <= 0:
            cap_b = 0.01

        pe = round(q.get('trailingPE', 0) or 0.0, 2)
        pbr = round(q.get('priceToBook', 0) or 0.0, 2)
        div_yield = round((q.get('trailingAnnualDividendYield', 0) or q.get('dividendYield', 0) or 0.0) * 100, 2)

        parsed.append({
            'Ticker': sym,
            '종목명': q.get('shortName', sym) or sym,
            '섹터': sector,
            '현재가($)': cp,
            '등락률(%)': chg,
            '거래량': vol,
            '시가총액(B$)': cap_b,
            'PER': pe,
            'PBR': pbr,
            '배당수익률(%)': div_yield,
        })

    df_data = pd.DataFrame(parsed)
    if not df_data.empty:
        df_data = df_data.drop_duplicates(subset=['Ticker']).sort_values(by='거래량', ascending=False).reset_index(drop=True)
    return df_data

# === 📌 왼쪽 사이드바 메뉴 네비게이션 ===
with st.sidebar:
    if logo_b64:
        st.markdown(f"""
        <div class="abomi-brand">
            <img src="data:image/jpeg;base64,{logo_b64}" class="abomi-logo" style="height: 38px;" alt="Abomi Logo">
            <div class="abomi-title-group">
                <div class="abomi-title" style="font-size: 24px;">
                    Abomi
                </div>
            </div>
        </div>
        <p style="font-size: 13px; color: var(--text-sub); margin: 2px 0 10px 0;">아는 만큼 보이는 미국 주식</p>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='margin:0;'>Abomi</h2><p style='font-size:12px; color:gray;'>아는 만큼 보이는 미국 주식</p>", unsafe_allow_html=True)

    st.markdown("---")
    
    selected_page = st.radio(
        "📌 메인 메뉴",
        [
            "📊 실시간 주가",
            "💼 내 보유 주식",
            "💱 국제 환율",
            "🗺️ 등락률 트리맵"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("#### ⚡ 시세 갱신 설정")
    refresh_mode = st.selectbox(
        "시세 업데이트 방식",
        ["수동 갱신 (핀비즈 기본)", "30초 자동 갱신", "60초 자동 갱신"],
        index=0,
        help="핀비즈(Finviz) 무료 기본형처럼 수동 갱신을 사용하거나, 30초/60초 배경 자동 갱신을 선택할 수 있습니다."
    )
    
    if st.button("🔄 새로고침", use_container_width=True, key="sidebar_refresh_btn"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<p style='font-size:11px; color:var(--text-sub); margin-top:4px; text-align:center;'>💡 실시간 시세를 즉시 받아옵니다.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🎨 화면 테마 설정")
    theme_options = ["System (시스템)", "Light (밝은 화면)", "Dark (어두운 회색)"]
    curr_theme = st.session_state.get("theme_mode", "System")
    t_idx = 0 if curr_theme == "System" else (1 if curr_theme == "Light" else 2)
    chosen_theme = st.radio("테마 선택", theme_options, index=t_idx, key="sidebar_theme_radio")
    
    new_t = "System"
    if "Light" in chosen_theme:
        new_t = "Light"
    elif "Dark" in chosen_theme:
        new_t = "Dark"
        
    if new_t != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = new_t
        st.rerun()

# 상단 헤더 타이틀 바
head_col1, head_col2 = st.columns([7.5, 2.5])
with head_col1:
    if logo_b64:
        st.markdown(f"""
        <div class="abomi-brand">
            <img src="data:image/jpeg;base64,{logo_b64}" class="abomi-logo" alt="Abomi Logo">
            <div class="abomi-title-group">
                <div class="abomi-title">
                    Abomi
                    <span class="abomi-sub-tag">아는 만큼 보이는 미국 주식</span>
                </div>
                <p class="abomi-subtitle">실시간으로 종목을 자유롭게 검색하고 정밀 분석할 수 있습니다.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="abomi-title-group">
            <div class="abomi-title">
                Abomi
                <span class="abomi-sub-tag">아는 만큼 보이는 미국 주식</span>
            </div>
            <p class="abomi-subtitle">실시간으로 종목을 자유롭게 검색하고 정밀 분석할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)

with head_col2:
    st.write("")
    if st.button("🔄 새로고침", use_container_width=True, key="top_refresh_btn"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<p style='font-size:12px; color:var(--text-sub); margin-top:4px; text-align:center;'>💡 실시간 시세를 즉시 받아올 수 있습니다.</p>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# =========================================================
# 📄 PAGE 1: 📊 실시간 주가 (Finviz 스크리너 & IPO 차트)
# =========================================================
if selected_page == "📊 실시간 주가":
    df = load_all_data()

    with st.expander("🔍 필터 검색", expanded=True):
        max_cap_val = float(df["시가총액(B$)"].max()) if not df.empty else 5000.0
        max_price_val = float(df["현재가($)"].max()) if not df.empty else 2000.0

        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            min_cap, max_cap = st.slider(
                "시가총액 범위 (B$)",
                min_value=0.0,
                max_value=max_cap_val,
                value=(0.0, max_cap_val),
                step=10.0
            )
            max_per = st.number_input("최대 PER (0 입력 시 PER 무시)", min_value=0, value=0)

        with f_col2:
            min_price, max_price = st.slider(
                "주가 범위 ($)", 
                min_value=0.0, 
                max_value=max_price_val, 
                value=(0.0, max_price_val)
            )
            min_dividend = st.number_input("최소 배당수익률 (%)", min_value=0.0, value=0.0, step=0.1)

        with f_col3:
            min_volume = st.number_input("최소 거래량 (주)", min_value=0, value=0, step=100000)
            sort_option = st.selectbox(
                "정렬 조건",
                [
                    "거래량 많은순",
                    "시가총액 높은순", 
                    "상승률 높은순 (급등)", 
                    "하락률 높은순 (급락)", 
                    "이름 오름차순 (A-Z)", 
                    "이름 내림차순 (Z-A)"
                ]
            )

    # 필터링 적용
    filtered_df = df[
        (df["시가총액(B$)"] >= min_cap) & 
        (df["시가총액(B$)"] <= max_cap) &
        (df["현재가($)"] >= min_price) & 
        (df["현재가($)"] <= max_price) &
        (df["거래량"] >= min_volume) &
        (df["배당수익률(%)"] >= min_dividend)
    ]

    if max_per > 0:
        filtered_df = filtered_df[(filtered_df["PER"] > 0) & (filtered_df["PER"] <= max_per)]

    if sort_option == "거래량 많은순":
        filtered_df = filtered_df.sort_values(by="거래량", ascending=False)
    elif sort_option == "시가총액 높은순":
        filtered_df = filtered_df.sort_values(by="시가총액(B$)", ascending=False)
    elif sort_option == "상승률 높은순 (급등)":
        filtered_df = filtered_df.sort_values(by="등락률(%)", ascending=False)
    elif sort_option == "하락률 높은순 (급락)":
        filtered_df = filtered_df.sort_values(by="등락률(%)", ascending=True)
    elif sort_option == "이름 오름차순 (A-Z)":
        filtered_df = filtered_df.sort_values(by="종목명", ascending=True)
    elif sort_option == "이름 내림차순 (Z-A)":
        filtered_df = filtered_df.sort_values(by="종목명", ascending=False)

    st.markdown("---")
    st.caption(f"🟢 미국 전체 상장 주식 & ETF 총 {len(df):,}개 종목 실시간 시세 연동 (업데이트 방식: {refresh_mode})")
    st.subheader(f"검색 결과 : 총 {len(filtered_df):,}개 종목")

    table_col, chart_col = st.columns([6, 4])

    with table_col:
        st.caption("👆 아래 표에서 원하는 주식을 클릭하면 우측 창에 상장부터 현재까지 전체 차트가 나타납니다.")
        event = st.dataframe(
            filtered_df.style.format({
                "현재가($)": "${:.2f}", 
                "시가총액(B$)": "${:.2f}", 
                "등락률(%)": "{:.2f}%",
                "거래량": "{:,.0f}"
            }), 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",           
            selection_mode="single-row",
            height=580
        )

    with chart_col:
        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            row_data = filtered_df.iloc[selected_row_index]
            selected_ticker = row_data["Ticker"]
            
            st.subheader(f"📊 {selected_ticker} ({row_data['종목명']})")
            
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric("현재가", f"${row_data['현재가($)']:.2f}", f"{row_data['등락률(%)']:+.2f}%")
                st.markdown(f"**시가총액/자산**: `${row_data['시가총액(B$)']:.2f}B`")
                st.markdown(f"**일일 거래량**: `{row_data['거래량']:,} 주`")
            with m_col2:
                st.markdown(f"**섹터**: `{row_data['섹터']}`")
                st.markdown(f"**PER**: `{row_data['PER']}` | **PBR**: `{row_data['PBR']}`")
                st.markdown(f"**배당수익률**: `{row_data['배당수익률(%)']}%`")

            st.markdown("---")
            
            chart_data = yf.Ticker(selected_ticker).history(period="max")
            
            if not chart_data.empty:
                fig_chart = go.Figure(data=[go.Candlestick(
                    x=chart_data.index,
                    open=chart_data['Open'],
                    high=chart_data['High'],
                    low=chart_data['Low'],
                    close=chart_data['Close'],
                    name=selected_ticker,
                    increasing_line_color='red',
                    decreasing_line_color='blue'
                )])
                
                is_dark_theme = (st.session_state.get("theme_mode") == "Dark")
                plotly_template = "plotly_dark" if is_dark_theme else "plotly_white"
                plotly_plot_bg = "#282A2D" if is_dark_theme else "#FFFFFF"
                plotly_font_color = "#F3F4F6" if is_dark_theme else "#1F2937"

                fig_chart.update_layout(
                    title=f"{selected_ticker} 상장(IPO)부터 현재까지 전체 캔들스틱 차트",
                    yaxis_title="Price ($)",
                    margin=dict(l=10, r=10, t=35, b=10),
                    height=380,
                    xaxis_rangeslider_visible=False,
                    template=plotly_template,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor=plotly_plot_bg,
                    font=dict(family="Nanum Gothic, sans-serif", color=plotly_font_color)
                )
                
                fig_chart.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1M", step="month", stepmode="backward"),
                            dict(count=6, label="6M", step="month", stepmode="backward"),
                            dict(count=1, label="1Y", step="year", stepmode="backward"),
                            dict(count=5, label="5Y", step="year", stepmode="backward"),
                            dict(step="all", label="전체 (IPO부터)")
                        ]),
                        bgcolor="#282A2D" if is_dark_theme else "#F8FAFC",
                        activecolor="#79E963",
                        font=dict(color="#F3F4F6" if is_dark_theme else "#1F2937")
                    )
                )
                st.plotly_chart(fig_chart, use_container_width=True)
            else:
                st.warning(f"{selected_ticker}의 차트 데이터를 불러오지 못했습니다.")
        else:
            st.info("👈 좌측 표에서 주식을 선택하면 우측에 상장부터 현재까지의 전체 캔들스틱 차트와 핵심 지표 요약이 나타납니다.")

# =========================================================
# 📄 PAGE 2: 💼 내 보유 주식 (Portfolio Tracker)
# =========================================================
elif selected_page == "💼 내 보유 주식":
    st.subheader("💼 내 포트폴리오 관리 및 수익률 분석")
    st.caption("실시간 주가와 연동하여 보유 주식의 현재 평가금액, 손익률, 예상 배당금을 자동으로 산출합니다.")

    df_market = load_all_data()

    # 포트폴리오 실시간 계산
    port_list = st.session_state["my_portfolio"]
    port_records = []
    
    total_invested = 0.0
    total_current_val = 0.0
    
    for item in port_list:
        tick = item["Ticker"]
        buy_price = item["매수가($)"]
        qty = item["보유주수"]
        
        # 시장 실시간 가 추출
        match = df_market[df_market["Ticker"] == tick]
        if not match.empty:
            curr_price = float(match.iloc[0]["현재가($)"])
            name = str(match.iloc[0]["종목명"])
            sector = str(match.iloc[0]["섹터"])
            div_y = float(match.iloc[0]["배당수익률(%)"])
        else:
            curr_price = buy_price
            name = item.get("종목명", tick)
            sector = "기타"
            div_y = 0.0
            
        invested = buy_price * qty
        current_val = curr_price * qty
        profit_val = current_val - invested
        profit_pct = ((curr_price - buy_price) / buy_price * 100) if buy_price > 0 else 0.0
        annual_div = current_val * (div_y / 100.0)

        total_invested += invested
        total_current_val += current_val

        port_records.append({
            "Ticker": tick,
            "종목명": name,
            "섹터": sector,
            "매수가($)": buy_price,
            "현재가($)": curr_price,
            "보유주수": qty,
            "총 투자금($)": invested,
            "평가금액($)": current_val,
            "평가손익($)": profit_val,
            "수익률(%)": profit_pct,
            "예상 연배당($)": annual_div
        })

    df_port = pd.DataFrame(port_records)
    total_profit_val = total_current_val - total_invested
    total_profit_pct = ((total_current_val - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
    total_annual_div = df_port["예상 연배당($)"].sum() if not df_port.empty else 0.0

    # 핵심 요약 카드
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        st.metric("총 매수 금액", f"${total_invested:,.2f}")
    with p_col2:
        st.metric("현재 평가 금액", f"${total_current_val:,.2f}")
    with p_col3:
        st.metric("총 평가 손익", f"${total_profit_val:+,.2f}", f"{total_profit_pct:+.2f}%")
    with p_col4:
        st.metric("예상 연간 배당금", f"${total_annual_div:,.2f}", f"{(total_annual_div/total_current_val*100):.2f}%" if total_current_val > 0 else "0.00%")

    st.markdown("---")

    p_tab1, p_tab2 = st.columns([6, 4])

    with p_tab1:
        st.subheader("📋 보유 종목 상세 현황")
        if not df_port.empty:
            st.dataframe(
                df_port.style.format({
                    "매수가($)": "${:.2f}",
                    "현재가($)": "${:.2f}",
                    "총 투자금($)": "${:,.2f}",
                    "평가금액($)": "${:,.2f}",
                    "평가손익($)": "${:+,.2f}",
                    "수익률(%)": "{:+.2f}%",
                    "예상 연배당($)": "${:,.2f}"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("보유 중인 주식이 없습니다. 아래 추가 폼에서 종목을 입력해보세요.")

        with st.expander("➕ 새 보유 종목 추가 / 수정", expanded=False):
            with st.form("add_stock_form"):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    new_ticker = st.text_input("티커 코드 (예: NVDA, TSLA)", value="").strip().upper()
                with f_col2:
                    new_buy_price = st.number_input("매수 단가 ($)", min_value=0.01, value=100.0, step=1.0)
                with f_col3:
                    new_qty = st.number_input("보유 수량 (주)", min_value=1, value=10, step=1)

                submit_btn = st.form_submit_button("포트폴리오에 저장")
                if submit_btn and new_ticker:
                    # 기존 종목 업데이트 또는 새 종목 추가
                    found = False
                    for item in st.session_state["my_portfolio"]:
                        if item["Ticker"] == new_ticker:
                            item["매수가($)"] = new_buy_price
                            item["보유주수"] = new_qty
                            found = True
                            break
                    if not found:
                        st.session_state["my_portfolio"].append({
                            "Ticker": new_ticker,
                            "종목명": new_ticker,
                            "매수가($)": new_buy_price,
                            "보유주수": new_qty
                        })
                    st.success(f"{new_ticker} 종목이 포트폴리오에 반영되었습니다!")
                    st.rerun()

    with p_tab2:
        st.subheader("📊 포트폴리오 자산 비중")
        if not df_port.empty:
            fig_pie = px.pie(
                df_port, 
                values='평가금액($)', 
                names='Ticker', 
                hole=0.4,
                title="종목별 보유 자산 비중",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            is_dark_theme = (st.session_state.get("theme_mode") == "Dark")
            fig_pie.update_layout(
                template="plotly_dark" if is_dark_theme else "plotly_white",
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Nanum Gothic, sans-serif", color="#F3F4F6" if is_dark_theme else "#1F2937"),
                height=380
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# =========================================================
# 📄 PAGE 3: 💱 국제 환율 & 원자재 (Global FX & Commodities)
# =========================================================
elif selected_page == "💱 국제 환율":
    st.subheader("💱 글로벌 환율, 원자재 및 시장 지표")
    st.caption("실시간 국제 외환 시장 환율, 금, 원유, 미국 국채 금리 및 주요 가상자산 시세를 조회합니다.")

    fx_map = {
        "원/달러 환율 (USD/KRW)": "KRW=X",
        "유로/달러 (EUR/USD)": "EURUSD=X",
        "100엔/원 (JPY/KRW)": "JPYKRW=X",
        "금 선물 (Gold)": "GC=F",
        "WTI 유가 (Crude Oil)": "CL=F",
        "미국 10년물 국채 금리": "^TNX",
        "비트코인 (BTC/USD)": "BTC-USD"
    }

    @st.cache_data(ttl=30)
    def fetch_fx_data():
        records = []
        tickers_str = ' '.join(fx_map.values())
        try:
            data = yf.Tickers(tickers_str)
            for name, sym in fx_map.items():
                try:
                    h = data.tickers[sym].history(period='5d')
                    if not h.empty:
                        cp = float(h['Close'].iloc[-1])
                        prev = float(h['Close'].iloc[-2]) if len(h) > 1 else cp
                        chg = round(((cp - prev) / prev) * 100, 2)
                        records.append({
                            "Symbol": sym,
                            "지표명": name,
                            "현재가": cp,
                            "전일대비(%)": chg
                        })
                except Exception:
                    pass
        except Exception:
            pass
        return pd.DataFrame(records)

    df_fx = fetch_fx_data()

    # 메트릭 그리드 배치
    if not df_fx.empty:
        cols = st.columns(4)
        for idx, row in df_fx.iterrows():
            col_idx = idx % 4
            symbol = row["Symbol"]
            val_str = f"{row['현재가']:,.2f}"
            if symbol == "KRW=X":
                val_str = f"₩{row['현재가']:,.2f}"
            elif symbol == "^TNX":
                val_str = f"{row['현재가']:.2f}%"
            elif symbol == "BTC-USD":
                val_str = f"${row['현재가']:,.0f}"
            else:
                val_str = f"${row['현재가']:,.2f}"

            with cols[col_idx]:
                st.metric(row["지표명"], val_str, f"{row['전일대비(%)']:+.2f}%")

    st.markdown("---")

    # 차트 선택
    fx_choice = st.selectbox("📊 상세 차트 조회 지표 선택", list(fx_map.keys()), index=0)
    chosen_sym = fx_map[fx_choice]

    with st.spinner(f"{fx_choice} 실시간 데이터 불러오는 중..."):
        fx_chart_data = yf.Ticker(chosen_sym).history(period="5y")
        if not fx_chart_data.empty:
            fig_fx = go.Figure()
            fig_fx.add_trace(go.Scatter(
                x=fx_chart_data.index,
                y=fx_chart_data['Close'],
                mode='lines',
                name=fx_choice,
                line=dict(color='#79E963', width=2)
            ))
            
            is_dark_theme = (st.session_state.get("theme_mode") == "Dark")
            plotly_template = "plotly_dark" if is_dark_theme else "plotly_white"
            plotly_plot_bg = "#282A2D" if is_dark_theme else "#FFFFFF"
            plotly_font_color = "#F3F4F6" if is_dark_theme else "#1F2937"

            fig_fx.update_layout(
                title=f"{fx_choice} 5년 추이 차트",
                yaxis_title="Price / Rate",
                margin=dict(l=10, r=10, t=35, b=10),
                height=450,
                template=plotly_template,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor=plotly_plot_bg,
                font=dict(family="Nanum Gothic, sans-serif", color=plotly_font_color)
            )

            fig_fx.update_xaxes(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all", label="전체 (5년)")
                    ]),
                    bgcolor="#282A2D" if is_dark_theme else "#F8FAFC",
                    activecolor="#79E963",
                    font=dict(color="#F3F4F6" if is_dark_theme else "#1F2937")
                )
            )
            st.plotly_chart(fig_fx, use_container_width=True)

# =========================================================
# 📄 PAGE 4: 🗺️ 등락률 트리맵 (Market Sector Treemap)
# =========================================================
elif selected_page == "🗺️ 등락률 트리맵":
    st.subheader("🗺️ 미 증시 전 종목 섹터별 등락률 트리맵 (Market Heatmap)")
    st.caption("시가총액 크기 및 일일 주가 등락률을 한눈에 시각적으로 탐색합니다.")

    df_tree_raw = load_all_data()

    if not df_tree_raw.empty:
        t_col1, t_col2 = st.columns([6, 4])
        with t_col1:
            selected_sectors = st.multiselect(
                "필터링 섹터 선택 (전체 보려면 비워두세요)",
                options=list(df_tree_raw["섹터"].unique()),
                default=[]
            )
        with t_col2:
            top_n = st.slider("시가총액 상위 종목 수", min_value=50, max_value=len(df_tree_raw), value=300, step=50)

        df_filtered_tree = df_tree_raw.copy()
        if selected_sectors:
            df_filtered_tree = df_filtered_tree[df_filtered_tree["섹터"].isin(selected_sectors)]
            
        df_filtered_tree = df_filtered_tree.head(top_n)

        fig_tree_full = px.treemap(
            df_filtered_tree, 
            path=[px.Constant("미국 주식 시장"), '섹터', 'Ticker'], 
            values='시가총액(B$)', 
            color='등락률(%)',        
            color_continuous_scale='RdYlGn',  
            hover_data=['종목명', '현재가($)', '등락률(%)', 'PER'], 
            color_continuous_midpoint=0  
        )
        
        is_dark_theme = (st.session_state.get("theme_mode") == "Dark")
        plotly_template = "plotly_dark" if is_dark_theme else "plotly_white"
        plotly_plot_bg = "#282A2D" if is_dark_theme else "#FFFFFF"
        plotly_font_color = "#F3F4F6" if is_dark_theme else "#1F2937"
        plotly_root_color = "#383C42" if is_dark_theme else "#E5E7EB"

        fig_tree_full.update_traces(root_color=plotly_root_color)
        fig_tree_full.update_layout(
            margin=dict(t=30, l=10, r=10, b=10), 
            template=plotly_template,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor=plotly_plot_bg,
            font=dict(family="Nanum Gothic, sans-serif", color=plotly_font_color),
            height=700 
        )
        st.plotly_chart(fig_tree_full, use_container_width=True)