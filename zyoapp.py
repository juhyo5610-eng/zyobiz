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
from dotenv import load_dotenv
import google.generativeai as genai

st.set_page_config(page_title="Abomi — 미국주식 & 금융", layout="wide", page_icon="🌱")

# === 환경 변수 ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key")

# === Base64 로고 로더 ===
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

logo_b64 = get_base64_image("abomi_logo.jpg")

# === Base64 웹폰트 로더 (Streamlit 정적 서빙 MIME 타입 문제 우회) ===
@st.cache_data
def get_base64_font(font_path):
    """폰트 파일을 base64로 인코딩하여 CSS data: URL에 직접 내장"""
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return ""

font_regular_b64 = get_base64_font("static/fonts/NotoSansKR-Regular.woff2")
font_bold_b64 = get_base64_font("static/fonts/NotoSansKR-Bold.woff2")

# === 테마 및 세션 상태 초기화 ===
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Light"

if "my_portfolio" not in st.session_state:
    st.session_state["my_portfolio"] = [
        {"Ticker": "NVDA", "종목명": "NVIDIA Corp", "매수가($)": 115.00, "보유주수": 20},
        {"Ticker": "AAPL", "종목명": "Apple Inc", "매수가($)": 210.00, "보유주수": 15},
        {"Ticker": "QQQ", "종목명": "Invesco QQQ Trust", "매수가($)": 460.00, "보유주수": 10},
        {"Ticker": "SCHD", "종목명": "Schwab US Dividend Equity", "매수가($)": 26.50, "보유주수": 50},
    ]

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "assistant", "content": "궁금한 종목이나 투자 전략을 물어보세요 🚀"}
    ]

# === 커스텀 CSS ===
theme_mode = st.session_state["theme_mode"]

if theme_mode == "Light":
    theme_vars = """
    :root {
        --bg-main: #FAFAFA; --bg-card: #FFFFFF; --bg-metric: #F9FAFB;
        --text-main: #111827; --text-sub: #6B7280;
        --border-color: #E5E7EB; --shadow-color: rgba(0, 0, 0, 0.04);
    }
    """
elif theme_mode == "Dark":
    theme_vars = """
    :root {
        --bg-main: #111827; --bg-card: #1F2937; --bg-metric: #1F2937;
        --text-main: #F9FAFB; --text-sub: #9CA3AF;
        --border-color: #374151; --shadow-color: rgba(0, 0, 0, 0.3);
    }
    """
else:
    theme_vars = """
    :root {
        --bg-main: #FAFAFA; --bg-card: #FFFFFF; --bg-metric: #F9FAFB;
        --text-main: #111827; --text-sub: #6B7280;
        --border-color: #E5E7EB; --shadow-color: rgba(0, 0, 0, 0.04);
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #111827; --bg-card: #1F2937; --bg-metric: #1F2937;
            --text-main: #F9FAFB; --text-sub: #9CA3AF;
            --border-color: #374151; --shadow-color: rgba(0, 0, 0, 0.3);
        }
    }
    """

st.markdown(f"""
<style>
/* === Base64 내장 웹폰트 (MIME 타입·광고차단기·방화벽 무관, 100% 로딩 보장) === */
@font-face {{
    font-family: 'Noto Sans KR';
    src: url('data:font/woff2;base64,{font_regular_b64}') format('woff2');
    font-weight: 400; font-style: normal; font-display: swap;
}}
@font-face {{
    font-family: 'Noto Sans KR';
    src: url('data:font/woff2;base64,{font_bold_b64}') format('woff2');
    font-weight: 700; font-style: normal; font-display: swap;
}}

{theme_vars}

.stAppDeployButton, [data-testid="stAppDeployButton"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; z-index: 99999 !important; }}

/* 사이드바 토글 */
[data-testid="collapsedControl"] button *,
[data-testid="stSidebarCollapseButton"] button *,
[data-testid="stSidebarHeader"] button *,
button[data-testid="stBaseButton-header"] * {{
    display: none !important; visibility: hidden !important;
    width: 0 !important; height: 0 !important; opacity: 0 !important;
}}
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarHeader"] button,
button[data-testid="stBaseButton-header"] {{
    border-radius: 8px !important; border: 1px solid var(--border-color) !important;
    background-color: var(--bg-card) !important;
    width: 36px !important; height: 36px !important; padding: 0 !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    box-shadow: 0 1px 2px var(--shadow-color) !important;
}}
[data-testid="collapsedControl"] button::before,
[data-testid="stSidebarCollapseButton"] button::before,
[data-testid="stSidebarHeader"] button::before,
button[data-testid="stBaseButton-header"]::before {{
    content: "☰" !important; font-size: 20px !important; font-weight: 900 !important;
    color: var(--text-main) !important; display: block !important; visibility: visible !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}}
[data-testid="collapsedControl"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stSidebarHeader"] button:hover,
button[data-testid="stBaseButton-header"]:hover {{ border-color: #10B981 !important; }}
[data-testid="collapsedControl"] button:hover::before,
[data-testid="stSidebarCollapseButton"] button:hover::before,
[data-testid="stSidebarHeader"] button:hover::before,
button[data-testid="stBaseButton-header"]:hover::before {{ color: #10B981 !important; }}

.block-container {{
    padding-top: 2.5rem !important; padding-bottom: 2rem !important;
    max-width: 95% !important;
}}

body, .stApp, h1, h2, h3, h4, h5, h6, p, label, input, button {{
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}}
[data-testid="stIcon"], [data-testid="stIcon"] *, span[data-testid="stIcon"], i, svg,
summary [data-testid="stIcon"], .material-symbols-outlined, .material-symbols-rounded, .material-icons {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons', sans-serif !important;
}}
.stApp {{ background-color: var(--bg-main) !important; color: var(--text-main) !important; }}

section[data-testid="stSidebar"] {{
    background-color: var(--bg-card) !important; border-right: 1px solid var(--border-color) !important;
}}
section[data-testid="stSidebar"] .stRadio label span {{
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
    font-size: 14px !important; font-weight: 600 !important; color: var(--text-main) !important;
}}

.abomi-brand {{ display: flex; align-items: center; gap: 10px; }}
.abomi-logo {{
    height: 36px; width: auto; border: none !important; outline: none !important;
    box-shadow: none !important; border-radius: 0 !important; background: transparent !important;
}}
.abomi-title {{
    font-size: 22px; font-weight: 800; color: var(--text-main) !important; margin: 0; line-height: 1.2;
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
}}
.abomi-subtitle {{
    font-size: 13px; color: var(--text-sub) !important; margin: 2px 0 0 0;
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
}}

.stButton>button {{
    background-color: #10B981 !important; color: #FFFFFF !important;
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
    font-weight: 600 !important; border: none !important; border-radius: 8px !important;
    padding: 8px 16px !important; box-shadow: none !important;
}}
.stButton>button:hover {{ background-color: #059669 !important; }}

div[data-testid="stExpander"], div[data-testid="stDataFrame"] {{
    background-color: var(--bg-card) !important; border-radius: 12px !important;
    border: 1px solid var(--border-color) !important; box-shadow: 0 1px 3px var(--shadow-color) !important;
}}
div[data-testid="stExpander"] summary {{
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
    font-weight: 600 !important; font-size: 15px !important; color: var(--text-main) !important;
}}
div[data-testid="stMetric"] {{
    background-color: var(--bg-card) !important; border: 1px solid var(--border-color) !important;
    padding: 16px !important; border-radius: 12px !important; box-shadow: 0 1px 3px var(--shadow-color) !important;
}}
.stSlider > div > div > div > div {{ background-color: #10B981 !important; }}
h1, h2, h3, h4, h5, h6, label, p {{
    font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
    color: var(--text-main);
}}

/* 정렬 박스 강조 */
.sort-box {{
    background-color: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 12px 16px;
}}

/* 섹터 카드 */
.sector-card {{
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 14px 16px; text-align: center;
    transition: border-color 0.15s; cursor: pointer;
}}
.sector-card:hover {{ border-color: #10B981; }}
.sector-card .sector-name {{ font-size: 14px; font-weight: 700; margin-bottom: 4px; color: var(--text-main); }}
.sector-card .sector-etf {{ font-size: 12px; color: var(--text-sub); }}
.sector-card .sector-chg {{ font-size: 15px; font-weight: 700; margin: 4px 0; }}
.sector-card .sector-count {{ font-size: 11px; color: var(--text-sub); }}
.chg-up {{ color: #EF4444; }}
.chg-down {{ color: #3B82F6; }}
.chg-flat {{ color: var(--text-sub); }}

/* 섹터 선택 바 */
.sector-etf-bar {{
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 12px 20px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}}
.sector-etf-bar .etf-name {{ font-weight: 700; font-size: 15px; color: var(--text-main); }}
.sector-etf-bar .etf-detail {{ font-size: 13px; color: var(--text-sub); }}
</style>
""", unsafe_allow_html=True)

# === 데이터셋 ===
candidate_tickers = [
    "TQQQ", "SOXL", "NVDL", "CONL", "SQQQ", "FNGU", "SPXL", "TSLL", "LABU", "UPRO",
    "MSTX", "MSTU", "SOXS", "TECL", "WEBL", "DPST", "FAS", "FAZ", "TNA", "TZA",
    "SPY", "QQQ", "IWM", "DIA", "VOO", "IVV", "GLD", "SLV", "SCHD", "JEPI",
    # 섹터별 대표 ETF
    "XLK", "XLV", "XLF", "XLY", "XLP", "XLC", "XLI", "XLE", "XLB", "XLRE", "XLU",
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
    "SPY", "QQQ", "IWM", "DIA", "VOO", "IVV", "GLD", "SLV", "SCHD", "JEPI", "JEPQ",
    "XLK", "XLV", "XLF", "XLY", "XLP", "XLC", "XLI", "XLE", "XLB", "XLRE", "XLU"
])

SECTOR_MAP = {
    'NVDA': 'Technology', 'AAPL': 'Technology', 'MSFT': 'Technology', 'AMD': 'Technology',
    'INTC': 'Technology', 'PLTR': 'Technology', 'SMCI': 'Technology', 'AVGO': 'Technology',
    'AMZN': 'Consumer Cyclical', 'TSLA': 'Consumer Cyclical', 'GOOGL': 'Communication Services',
    'META': 'Communication Services', 'JPM': 'Financial Services', 'BAC': 'Financial Services',
    'LLY': 'Healthcare', 'UNH': 'Healthcare', 'WMT': 'Consumer Defensive', 'XOM': 'Energy'
}

# === 섹터 정보 (한글명 + 대표 ETF + 아이콘) ===
SECTOR_INFO = {
    "Technology":             {"kr": "🖥️ 기술",       "etf": "XLK"},
    "Healthcare":             {"kr": "🏥 헬스케어",    "etf": "XLV"},
    "Financial Services":     {"kr": "🏦 금융",       "etf": "XLF"},
    "Consumer Cyclical":      {"kr": "🛒 경기소비재",  "etf": "XLY"},
    "Consumer Defensive":     {"kr": "🛡️ 필수소비재", "etf": "XLP"},
    "Communication Services": {"kr": "📡 커뮤니케이션", "etf": "XLC"},
    "Industrials":            {"kr": "🏭 산업재",      "etf": "XLI"},
    "Energy":                 {"kr": "⛽ 에너지",      "etf": "XLE"},
    "Materials":              {"kr": "🧱 소재",        "etf": "XLB"},
    "Real Estate":            {"kr": "🏠 부동산",      "etf": "XLRE"},
    "Utilities":              {"kr": "💡 유틸리티",    "etf": "XLU"},
    "ETF":                    {"kr": "📦 ETF",         "etf": "SPY"},
    "기타":                   {"kr": "🔷 기타",        "etf": None},
}

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
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
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
            'Ticker': sym, '종목명': q.get('shortName', sym) or sym, '섹터': sector,
            '현재가($)': cp, '등락률(%)': chg, '거래량': vol, '시가총액(B$)': cap_b,
            'PER': pe, 'PBR': pbr, '배당수익률(%)': div_yield,
        })
    df_data = pd.DataFrame(parsed)
    if not df_data.empty:
        df_data = df_data.drop_duplicates(subset=['Ticker']).sort_values(by='거래량', ascending=False).reset_index(drop=True)
    return df_data

# === AI 응답 생성 ===
def get_ai_response(context, user_input, history):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "여기에_내API_키_입력":
        return "⚠️ `.env` 파일에 `GEMINI_API_KEY`를 설정해주세요."
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        sys_prompt = "너는 미국 주식 전문 AI 애널리스트 '아보미 AI'야. 친절하고 명확하게 한국어로 답변해. 투자 최종 책임은 본인에게 있음을 자연스럽게 안내해."
        if context:
            sys_prompt += f"\n\n[사용자가 현재 보고 있는 실시간 데이터]\n{context}"
        try:
            model = genai.GenerativeModel("gemini-3.6-flash", system_instruction=sys_prompt)
        except Exception:
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=sys_prompt)
        h = []
        for m in history:
            h.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
        chat = model.start_chat(history=h)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"❌ 오류: {e}"

# === 사이드바 ===
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div class="abomi-brand"><img src="data:image/jpeg;base64,{logo_b64}" class="abomi-logo" alt="Abomi"><span class="abomi-title">Abomi</span></div>', unsafe_allow_html=True)
    else:
        st.markdown("<span class='abomi-title'>Abomi</span>", unsafe_allow_html=True)
    st.markdown("---")
    selected_page = st.radio("메뉴", ["📊 실시간 주가", "💼 내 보유 주식", "💱 국제 환율", "🗺️ 등락률 트리맵"], index=0, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    theme_choice = st.selectbox("테마", ["Light", "Dark", "System"], index=["Light", "Dark", "System"].index(st.session_state.get("theme_mode", "Light")))
    if theme_choice != st.session_state["theme_mode"]:
        st.session_state["theme_mode"] = theme_choice
        st.rerun()

# === 상단 헤더 ===
if logo_b64:
    st.markdown(f'<div class="abomi-brand" style="margin-bottom:6px;"><img src="data:image/jpeg;base64,{logo_b64}" class="abomi-logo" style="height:40px;" alt="Abomi"><div><div class="abomi-title" style="font-size:24px;">Abomi</div><p class="abomi-subtitle">아는 만큼 보이는 미국 주식</p></div></div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="margin-bottom:6px;"><div class="abomi-title" style="font-size:24px;">Abomi</div><p class="abomi-subtitle">아는 만큼 보이는 미국 주식</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# 메인 레이아웃: 좌측 콘텐츠 (70%) + 우측 AI 챗봇 (30%)
# ═══════════════════════════════════════════════════
ai_context = ""
context_label = ""

main_col, chat_col = st.columns([7, 3])

with main_col:

    # =============================================
    # PAGE 1: 📊 실시간 주가
    # =============================================
    if selected_page == "📊 실시간 주가":
        df = load_all_data()

        # --- 세션: 선택된 섹터 ---
        if "selected_sector" not in st.session_state:
            st.session_state["selected_sector"] = "전체"

        # === 섹터 개요 카드 (항상 표시) ===
        # 섹터별 종목 수 + ETF 등락률 계산
        sector_stats = {}
        for sec_name, sec_info in SECTOR_INFO.items():
            sec_df = df[df["섹터"] == sec_name] if sec_name != "전체" else df
            count = len(sec_df)
            if count == 0 and sec_name not in ["ETF", "기타"]:
                continue
            etf_ticker = sec_info["etf"]
            etf_chg = 0.0
            etf_price = 0.0
            if etf_ticker and not df.empty:
                etf_row = df[df["Ticker"] == etf_ticker]
                if not etf_row.empty:
                    etf_chg = float(etf_row.iloc[0]["등락률(%)"])
                    etf_price = float(etf_row.iloc[0]["현재가($)"])
            sector_stats[sec_name] = {"count": count, "chg": etf_chg, "price": etf_price, "etf": etf_ticker, "kr": sec_info["kr"]}

        # 섹터 카드 그리드 (2행 × 6열)
        visible_sectors = [s for s in sector_stats if sector_stats[s]["count"] > 0]
        row_size = 6
        for row_start in range(0, len(visible_sectors), row_size):
            row_sectors = visible_sectors[row_start:row_start + row_size]
            cols = st.columns(len(row_sectors))
            for i, sec_name in enumerate(row_sectors):
                s = sector_stats[sec_name]
                chg_class = "chg-up" if s["chg"] > 0 else ("chg-down" if s["chg"] < 0 else "chg-flat")
                chg_sign = "+" if s["chg"] > 0 else ""
                etf_label = s["etf"] if s["etf"] else "-"
                with cols[i]:
                    if st.button(f"{s['kr']}\n{etf_label} {chg_sign}{s['chg']:.2f}%\n{s['count']}개", key=f"sec_{sec_name}", use_container_width=True):
                        st.session_state["selected_sector"] = sec_name
                        st.rerun()

        # --- 전체 보기 버튼 ---
        bc1, bc2, bc3 = st.columns([2, 1, 2])
        with bc2:
            if st.button("🔄 전체 보기" if st.session_state["selected_sector"] != "전체" else "✅ 전체 보기 중", use_container_width=True, disabled=(st.session_state["selected_sector"] == "전체")):
                st.session_state["selected_sector"] = "전체"
                st.rerun()

        current_sector = st.session_state["selected_sector"]

        # === 선택된 섹터 ETF 정보 바 ===
        if current_sector != "전체" and current_sector in SECTOR_INFO:
            sinfo = SECTOR_INFO[current_sector]
            etf_t = sinfo["etf"]
            if etf_t and not df.empty:
                etf_match = df[df["Ticker"] == etf_t]
                if not etf_match.empty:
                    ep = float(etf_match.iloc[0]["현재가($)"])
                    ec = float(etf_match.iloc[0]["등락률(%)"])
                    chg_cls = "chg-up" if ec > 0 else ("chg-down" if ec < 0 else "chg-flat")
                    chg_s = "+" if ec > 0 else ""
                    sec_count = len(df[df["섹터"] == current_sector])
                    avg_chg = df[df["섹터"] == current_sector]["등락률(%)"].mean()
                    avg_cls = "chg-up" if avg_chg > 0 else ("chg-down" if avg_chg < 0 else "chg-flat")
                    avg_s = "+" if avg_chg > 0 else ""
                    st.markdown(f"""
                    <div class="sector-etf-bar">
                        <span class="etf-name">{sinfo['kr']}</span>
                        <span class="etf-detail">대표 ETF: <b>{etf_t}</b> ${ep:.2f} <span class="{chg_cls}">({chg_s}{ec:.2f}%)</span></span>
                        <span class="etf-detail">{sec_count}개 종목 · 평균 <span class="{avg_cls}">{avg_s}{avg_chg:.2f}%</span></span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")

        # === 섹터 필터 적용 ===
        if current_sector == "전체":
            sector_df = df.copy()
        else:
            sector_df = df[df["섹터"] == current_sector].copy()

        # --- 필터 + 정렬 ---
        filter_zone, sort_zone = st.columns([7, 3])

        with filter_zone:
            with st.expander("🔍 상세 필터", expanded=False):
                f1, f2, f3 = st.columns(3)
                with f1:
                    max_cap_val = float(sector_df["시가총액(B$)"].max()) if not sector_df.empty else 5000.0
                    min_cap, max_cap = st.slider("시가총액 (B$)", 0.0, max_cap_val, (0.0, max_cap_val), step=10.0)
                    max_per = st.number_input("최대 PER (0=무시)", min_value=0, value=0)
                with f2:
                    max_price_val = float(sector_df["현재가($)"].max()) if not sector_df.empty else 2000.0
                    min_price, max_price = st.slider("주가 ($)", 0.0, max_price_val, (0.0, max_price_val))
                    max_pbr = st.number_input("최대 PBR (0=무시)", min_value=0.0, value=0.0, step=0.5)
                with f3:
                    min_volume = st.number_input("최소 거래량", min_value=0, value=0, step=100000)
                    min_dividend = st.number_input("최소 배당률 (%)", min_value=0.0, value=0.0, step=0.1)

        with sort_zone:
            st.markdown('<div class="sort-box">', unsafe_allow_html=True)
            sort_option = st.selectbox("📌 정렬", [
                "거래량 많은순", "시가총액 높은순",
                "상승률 높은순", "하락률 높은순",
                "PER 낮은순", "배당률 높은순", "이름순 (A-Z)"
            ])
            st.markdown('</div>', unsafe_allow_html=True)

        # --- 필터 적용 ---
        filtered_df = sector_df.copy()
        if not filtered_df.empty:
            filtered_df = filtered_df[
                (filtered_df["시가총액(B$)"] >= min_cap) & (filtered_df["시가총액(B$)"] <= max_cap) &
                (filtered_df["현재가($)"] >= min_price) & (filtered_df["현재가($)"] <= max_price) &
                (filtered_df["거래량"] >= min_volume) & (filtered_df["배당수익률(%)"] >= min_dividend)
            ]
            if max_per > 0:
                filtered_df = filtered_df[(filtered_df["PER"] > 0) & (filtered_df["PER"] <= max_per)]
            if max_pbr > 0:
                filtered_df = filtered_df[(filtered_df["PBR"] > 0) & (filtered_df["PBR"] <= max_pbr)]

        # --- 정렬 ---
        if sort_option == "거래량 많은순":
            filtered_df = filtered_df.sort_values(by="거래량", ascending=False)
        elif sort_option == "시가총액 높은순":
            filtered_df = filtered_df.sort_values(by="시가총액(B$)", ascending=False)
        elif sort_option == "상승률 높은순":
            filtered_df = filtered_df.sort_values(by="등락률(%)", ascending=False)
        elif sort_option == "하락률 높은순":
            filtered_df = filtered_df.sort_values(by="등락률(%)", ascending=True)
        elif sort_option == "PER 낮은순":
            pv = filtered_df[filtered_df["PER"] > 0]
            pz = filtered_df[filtered_df["PER"] <= 0]
            filtered_df = pd.concat([pv.sort_values(by="PER", ascending=True), pz])
        elif sort_option == "배당률 높은순":
            filtered_df = filtered_df.sort_values(by="배당수익률(%)", ascending=False)
        elif sort_option == "이름순 (A-Z)":
            filtered_df = filtered_df.sort_values(by="종목명", ascending=True)

        # --- 결과 카운트 ---
        sector_label = SECTOR_INFO.get(current_sector, {}).get("kr", "전체") if current_sector != "전체" else "전체"
        if len(filtered_df) < len(sector_df):
            st.caption(f"{sector_label} · 필터 적용 **{len(filtered_df):,}**개")
        else:
            st.caption(f"{sector_label} · **{len(filtered_df):,}**개 종목")

        # --- 테이블 + 차트 ---
        table_sub, chart_sub = st.columns([6, 4])

        with table_sub:
            event = st.dataframe(
                filtered_df.style.format({
                    "현재가($)": "${:.2f}", "시가총액(B$)": "${:.2f}",
                    "등락률(%)": "{:.2f}%", "거래량": "{:,.0f}"
                }),
                use_container_width=True, hide_index=True,
                on_select="rerun", selection_mode="single-row", height=500
            )

        with chart_sub:
            if len(event.selection.rows) > 0:
                row_idx = event.selection.rows[0]
                row_data = filtered_df.iloc[row_idx]
                sel_ticker = row_data["Ticker"]

                st.subheader(sel_ticker)
                st.caption(row_data['종목명'])

                mc1, mc2 = st.columns(2)
                with mc1:
                    st.metric("현재가", f"${row_data['현재가($)']:.2f}", f"{row_data['등락률(%)']:+.2f}%")
                    st.markdown(f"**시총** `${row_data['시가총액(B$)']:.2f}B` · **거래량** `{row_data['거래량']:,}`")
                with mc2:
                    st.markdown(f"**섹터** `{row_data['섹터']}`")
                    st.markdown(f"**PER** `{row_data['PER']}` · **PBR** `{row_data['PBR']}`")
                    st.markdown(f"**배당** `{row_data['배당수익률(%)']}%`")

                st.markdown("---")
                chart_data = yf.Ticker(sel_ticker).history(period="max")
                if not chart_data.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=chart_data.index, open=chart_data['Open'], high=chart_data['High'],
                        low=chart_data['Low'], close=chart_data['Close'], name=sel_ticker,
                        increasing_line_color='red', decreasing_line_color='blue'
                    )])
                    is_dark = st.session_state.get("theme_mode") == "Dark"
                    fig.update_layout(
                        title=f"{sel_ticker} 전체 차트", yaxis_title="$",
                        margin=dict(l=10, r=10, t=35, b=10), height=350,
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark" if is_dark else "plotly_white",
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor="#1F2937" if is_dark else "#FFFFFF",
                        font=dict(family="Noto Sans KR, sans-serif", color="#F9FAFB" if is_dark else "#111827")
                    )
                    fig.update_xaxes(rangeselector=dict(
                        buttons=[dict(count=1,label="1M",step="month",stepmode="backward"),
                                 dict(count=6,label="6M",step="month",stepmode="backward"),
                                 dict(count=1,label="1Y",step="year",stepmode="backward"),
                                 dict(count=5,label="5Y",step="year",stepmode="backward"),
                                 dict(step="all",label="전체")],
                        bgcolor="#1F2937" if is_dark else "#F9FAFB", activecolor="#10B981",
                        font=dict(color="#F9FAFB" if is_dark else "#111827")
                    ))
                    st.plotly_chart(fig, use_container_width=True)

                # AI 컨텍스트
                ai_context = f"종목: {sel_ticker} ({row_data['종목명']})\n현재가: ${row_data['현재가($)']:.2f} ({row_data['등락률(%)']:+.2f}%)\n시총: ${row_data['시가총액(B$)']:.2f}B | PER: {row_data['PER']} | PBR: {row_data['PBR']}\n배당: {row_data['배당수익률(%)']}% | 거래량: {row_data['거래량']:,}\n섹터: {row_data['섹터']}"
                context_label = f"📍 {sel_ticker} 조회 중"
            else:
                st.info("👈 종목을 선택하면 차트가 표시됩니다.")
                context_label = f"📍 {sector_label}"

    # =============================================
    # PAGE 2: 💼 내 보유 주식
    # =============================================
    elif selected_page == "💼 내 보유 주식":
        st.subheader("💼 내 포트폴리오")
        df_market = load_all_data()
        port_list = st.session_state["my_portfolio"]
        port_records = []
        total_invested = 0.0
        total_current_val = 0.0
        for item in port_list:
            tick = item["Ticker"]; buy_price = item["매수가($)"]; qty = item["보유주수"]
            match = df_market[df_market["Ticker"] == tick]
            if not match.empty:
                curr_price = float(match.iloc[0]["현재가($)"]); name = str(match.iloc[0]["종목명"])
                sector = str(match.iloc[0]["섹터"]); div_y = float(match.iloc[0]["배당수익률(%)"])
            else:
                curr_price = buy_price; name = item.get("종목명", tick); sector = "기타"; div_y = 0.0
            invested = buy_price * qty; current_val = curr_price * qty
            profit_val = current_val - invested
            profit_pct = ((curr_price - buy_price) / buy_price * 100) if buy_price > 0 else 0.0
            annual_div = current_val * (div_y / 100.0)
            total_invested += invested; total_current_val += current_val
            port_records.append({
                "Ticker": tick, "종목명": name, "섹터": sector, "매수가($)": buy_price,
                "현재가($)": curr_price, "보유주수": qty, "총 투자금($)": invested,
                "평가금액($)": current_val, "평가손익($)": profit_val,
                "수익률(%)": profit_pct, "예상 연배당($)": annual_div
            })
        df_port = pd.DataFrame(port_records)
        total_profit_val = total_current_val - total_invested
        total_profit_pct = ((total_current_val - total_invested) / total_invested * 100) if total_invested > 0 else 0.0
        total_annual_div = df_port["예상 연배당($)"].sum() if not df_port.empty else 0.0

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1: st.metric("총 매수금", f"${total_invested:,.0f}")
        with pc2: st.metric("평가금액", f"${total_current_val:,.0f}")
        with pc3: st.metric("평가손익", f"${total_profit_val:+,.0f}", f"{total_profit_pct:+.1f}%")
        with pc4: st.metric("연간 배당", f"${total_annual_div:,.0f}", f"{(total_annual_div/total_current_val*100):.1f}%" if total_current_val > 0 else "0%")
        st.markdown("---")

        pt1, pt2 = st.columns([6, 4])
        with pt1:
            if not df_port.empty:
                st.dataframe(df_port.style.format({
                    "매수가($)": "${:.2f}", "현재가($)": "${:.2f}", "총 투자금($)": "${:,.0f}",
                    "평가금액($)": "${:,.0f}", "평가손익($)": "${:+,.0f}", "수익률(%)": "{:+.1f}%", "예상 연배당($)": "${:,.0f}"
                }), use_container_width=True, hide_index=True)
            with st.expander("➕ 종목 추가", expanded=False):
                with st.form("add_stock_form"):
                    fc1, fc2, fc3 = st.columns(3)
                    with fc1: new_ticker = st.text_input("티커 (예: NVDA)", value="").strip().upper()
                    with fc2: new_buy_price = st.number_input("매수가 ($)", min_value=0.01, value=100.0, step=1.0)
                    with fc3: new_qty = st.number_input("수량 (주)", min_value=1, value=10, step=1)
                    if st.form_submit_button("저장") and new_ticker:
                        found = False
                        for item in st.session_state["my_portfolio"]:
                            if item["Ticker"] == new_ticker:
                                item["매수가($)"] = new_buy_price; item["보유주수"] = new_qty; found = True; break
                        if not found:
                            st.session_state["my_portfolio"].append({"Ticker": new_ticker, "종목명": new_ticker, "매수가($)": new_buy_price, "보유주수": new_qty})
                        st.success(f"{new_ticker} 반영 완료"); st.rerun()
        with pt2:
            if not df_port.empty:
                fig_pie = px.pie(df_port, values='평가금액($)', names='Ticker', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
                is_dark = st.session_state.get("theme_mode") == "Dark"
                fig_pie.update_layout(template="plotly_dark" if is_dark else "plotly_white", paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Noto Sans KR, sans-serif", color="#F9FAFB" if is_dark else "#111827"), height=350, margin=dict(t=20, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)

        # AI 컨텍스트
        port_summary = ", ".join([f"{p['Ticker']}({p['수익률(%)']:+.1f}%)" for p in port_records])
        ai_context = f"포트폴리오 현황:\n총 투자금: ${total_invested:,.0f} | 평가금액: ${total_current_val:,.0f} | 수익률: {total_profit_pct:+.1f}%\n연간 배당: ${total_annual_div:,.0f}\n보유 종목: {port_summary}"
        context_label = "📍 포트폴리오 분석 중"

    # =============================================
    # PAGE 3: 💱 국제 환율
    # =============================================
    elif selected_page == "💱 국제 환율":
        st.subheader("💱 환율 · 원자재 · 시장 지표")
        fx_map = {"USD/KRW": "KRW=X", "EUR/USD": "EURUSD=X", "JPY/KRW": "JPYKRW=X",
                  "Gold": "GC=F", "WTI 유가": "CL=F", "미 10Y 금리": "^TNX", "BTC/USD": "BTC-USD"}

        @st.cache_data(ttl=30)
        def fetch_fx_data():
            records = []
            try:
                data = yf.Tickers(' '.join(fx_map.values()))
                for name, sym in fx_map.items():
                    try:
                        h = data.tickers[sym].history(period='5d')
                        if not h.empty:
                            cp = float(h['Close'].iloc[-1])
                            prev = float(h['Close'].iloc[-2]) if len(h) > 1 else cp
                            chg = round(((cp - prev) / prev) * 100, 2)
                            records.append({"Symbol": sym, "지표명": name, "현재가": cp, "전일대비(%)": chg})
                    except Exception: pass
            except Exception: pass
            return pd.DataFrame(records)

        df_fx = fetch_fx_data()
        if not df_fx.empty:
            cols = st.columns(4)
            fx_context_parts = []
            for idx, row in df_fx.iterrows():
                symbol = row["Symbol"]
                if symbol == "KRW=X": val_str = f"₩{row['현재가']:,.2f}"
                elif symbol == "^TNX": val_str = f"{row['현재가']:.2f}%"
                elif symbol == "BTC-USD": val_str = f"${row['현재가']:,.0f}"
                else: val_str = f"${row['현재가']:,.2f}"
                with cols[idx % 4]: st.metric(row["지표명"], val_str, f"{row['전일대비(%)']:+.2f}%")
                fx_context_parts.append(f"{row['지표명']}: {val_str} ({row['전일대비(%)']:+.2f}%)")

            ai_context = "환율/원자재 실시간 시세:\n" + "\n".join(fx_context_parts)

        st.markdown("---")
        fx_choice = st.selectbox("상세 차트", list(fx_map.keys()), index=0)
        chosen_sym = fx_map[fx_choice]
        with st.spinner(f"{fx_choice} 로딩 중..."):
            fx_chart_data = yf.Ticker(chosen_sym).history(period="5y")
            if not fx_chart_data.empty:
                fig_fx = go.Figure()
                fig_fx.add_trace(go.Scatter(x=fx_chart_data.index, y=fx_chart_data['Close'], mode='lines', name=fx_choice, line=dict(color='#10B981', width=2)))
                is_dark = st.session_state.get("theme_mode") == "Dark"
                fig_fx.update_layout(title=f"{fx_choice} 5년 추이", yaxis_title="Price / Rate",
                    margin=dict(l=10, r=10, t=35, b=10), height=420,
                    template="plotly_dark" if is_dark else "plotly_white", paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor="#1F2937" if is_dark else "#FFFFFF",
                    font=dict(family="Noto Sans KR, sans-serif", color="#F9FAFB" if is_dark else "#111827"))
                fig_fx.update_xaxes(rangeselector=dict(
                    buttons=[dict(count=1,label="1M",step="month",stepmode="backward"),
                             dict(count=6,label="6M",step="month",stepmode="backward"),
                             dict(count=1,label="1Y",step="year",stepmode="backward"),
                             dict(step="all",label="전체")],
                    bgcolor="#1F2937" if is_dark else "#F9FAFB", activecolor="#10B981",
                    font=dict(color="#F9FAFB" if is_dark else "#111827")))
                st.plotly_chart(fig_fx, use_container_width=True)
        context_label = "📍 환율·원자재 조회 중"

    # =============================================
    # PAGE 4: 🗺️ 등락률 트리맵
    # =============================================
    elif selected_page == "🗺️ 등락률 트리맵":
        st.subheader("🗺️ 섹터별 등락률 히트맵")
        df_tree_raw = load_all_data()
        if not df_tree_raw.empty:
            tc1, tc2 = st.columns([6, 4])
            with tc1:
                selected_sectors = st.multiselect("섹터 필터", options=list(df_tree_raw["섹터"].unique()), default=[])
            with tc2:
                top_n = st.slider("상위 종목 수", 50, len(df_tree_raw), 300, step=50)
            df_ft = df_tree_raw.copy()
            if selected_sectors: df_ft = df_ft[df_ft["섹터"].isin(selected_sectors)]
            df_ft = df_ft.head(top_n)
            fig_tree = px.treemap(df_ft, path=[px.Constant("미국 주식 시장"), '섹터', 'Ticker'],
                values='시가총액(B$)', color='등락률(%)', color_continuous_scale='RdYlGn',
                hover_data=['종목명', '현재가($)', '등락률(%)', 'PER'], color_continuous_midpoint=0)
            is_dark = st.session_state.get("theme_mode") == "Dark"
            fig_tree.update_traces(root_color="#374151" if is_dark else "#E5E7EB")
            fig_tree.update_layout(margin=dict(t=30, l=10, r=10, b=10),
                template="plotly_dark" if is_dark else "plotly_white", paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Noto Sans KR, sans-serif", color="#F9FAFB" if is_dark else "#111827"), height=620)
            st.plotly_chart(fig_tree, use_container_width=True)

            # 상승/하락 TOP 5 컨텍스트
            top5_up = df_tree_raw.nlargest(5, "등락률(%)")
            top5_down = df_tree_raw.nsmallest(5, "등락률(%)")
            ai_context = "오늘 시장 요약:\n상승 TOP 5: " + ", ".join([f"{r['Ticker']}({r['등락률(%)']:+.2f}%)" for _, r in top5_up.iterrows()])
            ai_context += "\n하락 TOP 5: " + ", ".join([f"{r['Ticker']}({r['등락률(%)']:+.2f}%)" for _, r in top5_down.iterrows()])
        context_label = "📍 시장 히트맵"

# ═══════════════════════════════════════════════════
# 우측 AI 챗봇 패널 (모든 페이지에서 상시 표시)
# ═══════════════════════════════════════════════════
with chat_col:
    st.markdown("**💬 AI 어시스턴트**")
    if context_label:
        st.caption(context_label)

    if not GEMINI_API_KEY or GEMINI_API_KEY == "여기에_내API_키_입력":
        st.caption("⚠️ `.env`에 API 키를 설정하면 AI를 사용할 수 있습니다.")

    # 대화 영역 (스크롤 가능 고정 높이)
    chat_box = st.container(height=480)
    with chat_box:
        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 입력
    if prompt := st.chat_input("질문하세요..."):
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with chat_box:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("답변 생성 중..."):
                    reply = get_ai_response(ai_context, prompt, st.session_state["chat_messages"][:-1])
                    st.markdown(reply)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})