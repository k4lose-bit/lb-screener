"""
Lynch-BNF 스크리너 v4.0
KIS API + 테마 탐색기
"""

import streamlit as st
import pandas as pd
import requests
import time
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False

# ── 테마 데이터 로드 ────────────────────────────────────
try:
    from theme_map import THEME_MAP, THEME_STOCKS, THEME_LIST
    THEME_OK = True
except ImportError:
    THEME_OK = False
    THEME_MAP = {}
    THEME_STOCKS = {}
    THEME_LIST = []

st.set_page_config(
    page_title="LB 스크리너 | Lynch × BNF",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

/* ── 기본 폰트 & 배경 ── */
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif!important;}

/* ── 라이트/다크 모드 CSS 변수 ── */
:root {
  --bg-main: #F0F4FF;
  --bg-card: #ffffff;
  --bg-card2: #F8F9FA;
  --text-main: #212121;
  --text-sub: #424242;
  --text-muted: #757575;
  --text-light: #9E9E9E;
  --border: #EEEEEE;
  --shadow: rgba(0,0,0,.07);
  --chip-bg: #E3F2FD;
  --chip-color: #1565C0;
  --tag-bg: #E8F5E9;
  --tag-color: #2E7D32;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg-main: #0e1117;
    --bg-card: #1e2130;
    --bg-card2: #262b3d;
    --text-main: #fafafa;
    --text-sub: #e0e0e0;
    --text-muted: #bdbdbd;
    --text-light: #9e9e9e;
    --border: #2e3348;
    --shadow: rgba(0,0,0,.3);
    --chip-bg: #1a3a5c;
    --chip-color: #64b5f6;
    --tag-bg: #1b3a2a;
    --tag-color: #81c784;
  }
}

/* ── 컴포넌트 스타일 ── */
.lb-header{background:linear-gradient(135deg,#1565C0 0%,#0097A7 100%);border-radius:16px;padding:28px 36px;margin-bottom:24px}
.lb-header h1{font-size:2.4rem;font-weight:900;letter-spacing:4px;margin:0;color:white!important}
.lb-header p{font-size:.9rem;opacity:.85;margin:4px 0 0;color:white!important}
.date-badge{background:rgba(255,255,255,0.25);color:white;border-radius:20px;padding:4px 14px;font-size:.8rem;font-weight:700;display:inline-block;margin-bottom:8px}
.stage-card{border-radius:14px;padding:20px 22px;box-shadow:0 4px 16px var(--shadow)}
.stage-lynch{background:var(--chip-bg);border-top:5px solid #1565C0}
.stage-bnf{background:var(--bg-card2);border-top:5px solid #6A1B9A}
.stage-score{background:var(--bg-card2);border-top:5px solid #F57F17}
.stage-report{background:var(--tag-bg);border-top:5px solid #2E7D32}
.stage-label{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.lynch-label{color:#1565C0}.bnf-label{color:#6A1B9A}.score-label{color:#F57F17}.report-label{color:#2E7D32}
.stage-title{font-size:1.1rem;font-weight:700;margin-bottom:10px;color:var(--text-main)}
.stage-criteria{font-size:.82rem;color:var(--text-sub);line-height:1.9}
.stage-criteria b{color:var(--text-main)}
.metric-box{background:var(--bg-card);border-radius:12px;padding:16px 20px;text-align:center;box-shadow:0 2px 8px var(--shadow)}
.metric-val{font-size:1.6rem;font-weight:900;color:#1565C0}
.metric-lbl{font-size:.75rem;color:var(--text-muted);margin-top:2px}
.param-bar{background:var(--bg-card);border-radius:12px;padding:14px 20px;margin:16px 0;box-shadow:0 2px 8px var(--shadow);display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.param-chip{background:var(--chip-bg);color:var(--chip-color);border-radius:20px;padding:4px 14px;font-size:.8rem;font-weight:700}
.param-chip.purple{background:var(--bg-card2);color:#9C27B0}
.stock-card{background:var(--bg-card);border-radius:12px;padding:16px 20px;margin-bottom:10px;box-shadow:0 2px 8px var(--shadow);border-left:5px solid #1565C0;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.stock-card.rank1{border-left-color:#F57F17}.stock-card.rank2{border-left-color:#546E7A}.stock-card.rank3{border-left-color:#C62828}
.stock-rank{font-size:1.4rem;font-weight:900;color:#BDBDBD;min-width:32px;text-align:center}
.stock-rank.r1{color:#F57F17}.stock-rank.r2{color:#546E7A}.stock-rank.r3{color:#C62828}
.stock-name{font-size:1rem;font-weight:700;color:var(--text-main)}
.stock-code{font-size:.75rem;color:var(--text-light);margin-left:6px}
.stock-cat{font-size:.72rem;background:var(--chip-bg);color:var(--chip-color);padding:2px 8px;border-radius:10px;margin-left:8px;font-weight:700}
.theme-tag{font-size:.7rem;background:var(--tag-bg);color:var(--tag-color);padding:2px 8px;border-radius:10px;margin:2px 2px;display:inline-block;font-weight:600}
.stock-metrics{display:flex;gap:18px;margin-left:auto;align-items:center;flex-wrap:wrap}
.sm-item{text-align:center}
.sm-val{font-size:.95rem;font-weight:700;color:var(--text-main)}
.sm-lbl{font-size:.68rem;color:var(--text-light)}
.sm-val.green{color:#2E7D32}.sm-val.blue{color:#1565C0}.sm-val.purple{color:#6A1B9A}.sm-val.orange{color:#F57F17;font-size:1.1rem}
.lb-bar{height:8px;border-radius:4px;background:linear-gradient(90deg,#1565C0,#0097A7);display:inline-block;vertical-align:middle;margin-right:6px}
.report-box{background:var(--bg-card);border-radius:14px;padding:24px 28px;box-shadow:0 2px 12px var(--shadow);margin-top:16px}
.theme-stock-row{background:#E8D5F5;border-radius:10px;padding:12px 16px;margin-bottom:8px;box-shadow:0 2px 6px var(--shadow);display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;color:#212121}
.lb-badge-high{background:var(--tag-bg);color:#2E7D32;border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.lb-badge-mid{background:var(--bg-card2);color:#F57F17;border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.lb-badge-low{background:var(--bg-card2);color:var(--text-light);border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.stButton button{background:linear-gradient(135deg,#1565C0,#0097A7)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:1rem!important;padding:12px 0!important}

/* ── 모바일 반응형 ── */
@media (max-width: 768px) {
  .lb-header{padding:18px 20px}
  .lb-header h1{font-size:1.6rem;letter-spacing:2px}
  .stock-card{flex-direction:column;align-items:flex-start;gap:10px}
  .stock-metrics{margin-left:0;gap:12px}
  .theme-stock-row{flex-direction:column}
}

/* ── 테이블 다크모드 ── */
table {color: var(--text-main) !important;}
th {background: var(--bg-card2) !important; color: var(--text-main) !important;}
td {color: var(--text-main) !important;}
tr {background: var(--bg-card) !important;}
tr:hover {background: var(--bg-card2) !important;}
</style>
""", unsafe_allow_html=True)

# ── KIS API ─────────────────────────────────────────────
BASE_URL = "https://openapi.koreainvestment.com:9443"
STOCK_NAMES = {
    "005930":"삼성전자","000660":"SK하이닉스","035420":"NAVER","005380":"현대차",
    "051910":"LG화학","006400":"삼성SDI","035720":"카카오","000270":"기아",
    "068270":"셀트리온","105560":"KB금융","055550":"신한지주","096770":"SK이노베이션",
    "003550":"LG","017670":"SK텔레콤","018260":"삼성에스디에스","034730":"SK",
    "316140":"우리금융지주","086790":"하나금융지주","032830":"삼성생명","011200":"HMM",
    "066570":"LG전자","010130":"고려아연","012330":"현대모비스","009150":"삼성전기",
    "011170":"롯데케미칼","028260":"삼성물산","033780":"KT&G","000810":"삼성화재",
    "036570":"엔씨소프트","047050":"포스코인터내셔널","030200":"KT","003490":"대한항공",
    "010950":"S-Oil","139480":"이마트","042660":"한화오션","011780":"금호석유",
    "009830":"한화솔루션","088350":"한화생명","251270":"넷마블","090430":"아모레퍼시픽",
    "004020":"현대제철","006280":"녹십자","011690":"씨에스윈드","000720":"현대건설",
    "012450":"한화에어로스페이스","009540":"HD한국조선해양","010060":"OCI홀딩스",
    "015760":"한국전력","000100":"유한양행","247540":"에코프로비엠","086520":"에코프로",
    "373220":"LG에너지솔루션","196170":"알테오젠","058470":"리노공업","041510":"에스엠",
    "140860":"파크시스템스","237690":"에스티팜","214150":"클래시스","035900":"JYP엔터테인먼트",
    "039030":"이오테크닉스","053800":"안랩","041830":"인바디","067160":"아프리카TV",
    "091580":"상아프론테크","095660":"네오위즈","141080":"레고켐바이오",
    "166090":"하나머티리얼즈","178320":"서진시스템",
}

@st.cache_data(ttl=21600, show_spinner=False)
def get_kis_token(app_key, app_secret):
    try:
        res = requests.post(
            f"{BASE_URL}/oauth2/tokenP",
            json={"grant_type":"client_credentials","appkey":app_key,"appsecret":app_secret},
            timeout=10
        )
        return res.json().get("access_token","")
    except:
        return ""

@st.cache_data(ttl=3600, show_spinner=False)
def get_usd_krw():
    try:
        import yfinance as yf
        return float(yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1])
    except:
        return 1380.0

@st.cache_data(ttl=3600, show_spinner=False)
def get_domestic_news(name):
    """국내 종목 구글 뉴스"""
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(name+' 주식')}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        return [{"title": i.find('title').text, "link": i.find('link').text}
                for i in root.findall('.//item')[:5]]
    except:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_foreign_news(company_name):
    """해외 종목 영문 구글 뉴스"""
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(company_name+' stock')}&hl=en&gl=US&ceid=US:en"
        res = requests.get(url, timeout=5)
        root = ET.fromstring(res.text)
        return [{"title": i.find('title').text, "link": i.find('link').text}
                for i in root.findall('.//item')[:5]]
    except:
        return []

def calc_bollinger_band(closes, period=20):
    """볼린저밴드 계산"""
    s = pd.Series(closes)
    sma = s.rolling(period).mean()
    std = s.rolling(period).std()
    return (sma + 2*std), sma, (sma - 2*std)

def render_domestic_chart(code, name, closes, APP_KEY, APP_SECRET, token, n=120, chart_key=None):
    """국내/해외 종목 RSI+MACD+볼린저밴드 4단 차트"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # ── 데이터 준비 ──────────────────────────────────────
    if not token:
        # 나스닥: yfinance에서 날짜+데이터 함께 가져오기
        try:
            import yfinance as yf
            hist = yf.Ticker(code).history(period="6mo")
            if hist.empty or len(hist) < 26:
                st.warning("차트 데이터가 부족합니다.")
                return pd.Series(), pd.Series(), pd.Series(), []
            valid_closes = hist['Close'].astype(float).tolist()
            dates_raw = [d.strftime("%Y%m%d") for d in hist.index]
        except:
            st.warning("데이터를 가져오지 못했습니다.")
            return pd.Series(), pd.Series(), pd.Series(), []
    else:
        # 국내: KIS API에서 날짜+종가 함께 가져오기
        try:
            end   = datetime.today().strftime("%Y%m%d")
            start = (datetime.today()-timedelta(days=240)).strftime("%Y%m%d")
            r2 = requests.get(
                f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                headers=kis_headers(APP_KEY, APP_SECRET, token, "FHKST03010100"),
                params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                        "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                        "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=10)
            items = r2.json().get("output2",[])
            items = [d for d in items if d.get("stck_clpr") and float(d.get("stck_clpr",0))>0]
            if len(items) < 26:
                st.warning("차트 데이터가 부족합니다.")
                return pd.Series(), pd.Series(), pd.Series(), []
            items.reverse()
            valid_closes = [float(d["stck_clpr"]) for d in items]
            dates_raw    = [d["stck_bsop_date"] for d in items]
        except:
            # KIS 실패 시 전달받은 closes 사용
            valid_closes = [c for c in closes if c and c > 0]
            dates_raw = []

    n = min(n, len(valid_closes))
    if n < 26:
        st.warning("차트를 그리기에 데이터가 부족합니다.")
        return pd.Series(), pd.Series(), pd.Series(), []

    c_n = valid_closes[-n:]

    # ── 지표 계산 ──────────────────────────────────────
    s = pd.Series(valid_closes)
    delta = s.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = (100 - 100/(1 + gain/loss.replace(0, float('nan')))).fillna(50)
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    sig_line = macd_line.ewm(span=9, adjust=False).mean()
    hist_m = macd_line - sig_line
    bb_up, bb_mid, bb_low = calc_bollinger_band(valid_closes)

    # 마지막 n개만
    rsi_n    = rsi.values[-n:]
    macd_n   = macd_line.values[-n:]
    sig_n    = sig_line.values[-n:]
    hist_n   = hist_m.values[-n:]
    bb_up_n  = bb_up.tolist()[-n:]
    bb_mid_n = bb_mid.tolist()[-n:]
    bb_low_n = bb_low.tolist()[-n:]

    # ── x축 날짜 레이블 생성 ────────────────────────────
    x_axis = list(range(n))  # x축은 숫자 인덱스

    if len(dates_raw) >= n:
        d_list = dates_raw[-n:]
        date_labels = []
        for ds in d_list:
            ds = str(ds)
            if len(ds) == 8:
                date_labels.append(f"{ds[4:6]}.{ds[6:]}")
            else:
                date_labels.append(str(ds)[:10][5:].replace('-','.'))
    else:
        date_labels = [f"D-{n-1-i}" for i in range(n)]

    # 15일 간격 tick — 숫자 인덱스와 날짜 레이블 분리
    tick_indices = list(range(0, n, 15))
    tick_vals  = tick_indices
    tick_texts = [date_labels[i] for i in tick_indices if i < len(date_labels)]

    xaxis_cfg = dict(
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_texts,
        tickangle=-30,
        showspikes=True, spikemode="across",
        spikesnap="cursor", spikecolor="#888888",
        spikethickness=1, spikedash="dot"
    )

    # ── 차트 그리기 (3단: 주가+BB / RSI / MACD) ──────────
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.22, 0.23],
        vertical_spacing=0.04,
        subplot_titles=[f"{name} 주가 + 볼린저밴드", "RSI (14)", "MACD"]
    )

    # ── Row1: 주가 + 볼린저밴드 ──────────────────────────
    fig.add_trace(go.Scatter(
        x=x_axis, y=c_n,
        line=dict(color="#1565C0", width=2.5),
        name="종가",
        customdata=date_labels,
        hovertemplate="%{customdata}<br>종가: %{y:,.3f}<extra></extra>"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=bb_up_n,
        line=dict(color="#E24B4A", width=1.2, dash="dash"),
        name="BB상단",
        hovertemplate="BB상단: %{y:,.3f}<extra></extra>"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=bb_mid_n,
        line=dict(color="#F57F17", width=1.2),
        name="25일이평",
        hovertemplate="25일이평: %{y:,.3f}<extra></extra>"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=bb_low_n,
        line=dict(color="#2E7D32", width=1.2, dash="dash"),
        fill="tonexty", fillcolor="rgba(46,125,50,0.05)",
        name="BB하단",
        hovertemplate="BB하단: %{y:,.3f}<extra></extra>"
    ), row=1, col=1)

    # 범례 주석
    fig.add_annotation(x=1.01, y=0.97, xref="paper", yref="paper",
        text="<b style='color:#1565C0'>─</b> 종가<br>"
             "<b style='color:#E24B4A'>--</b> BB상단<br>"
             "<b style='color:#F57F17'>─</b> 25일이평<br>"
             "<b style='color:#2E7D32'>--</b> BB하단",
        showarrow=False, align="left", font=dict(size=11),
        bgcolor="rgba(255,255,255,0.85)", bordercolor="#DDD", borderwidth=1)

    # ── Row2: RSI ────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=x_axis, y=rsi_n,
        line=dict(color="#6A1B9A", width=2),
        name="RSI",
        customdata=date_labels,
        hovertemplate="%{customdata}<br>RSI: %{y:.3f}<extra></extra>"
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#E24B4A",
                  annotation_text="과매수(70)", annotation_position="right",
                  annotation_font_size=10, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#2E7D32",
                  annotation_text="과매도(30)", annotation_position="right",
                  annotation_font_size=10, row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(106,27,154,0.04)",
                  layer="below", line_width=0, row=2, col=1)

    # ── Row3: MACD ───────────────────────────────────────
    hcolors = ["#E24B4A" if v < 0 else "#2E7D32" for v in hist_n]
    fig.add_trace(go.Bar(
        x=x_axis, y=hist_n, marker_color=hcolors,
        name="히스토그램",
        customdata=date_labels,
        hovertemplate="%{customdata}<br>히스토: %{y:.3f}<extra></extra>"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=macd_n,
        line=dict(color="#1565C0", width=1.8),
        name="MACD",
        customdata=date_labels,
        hovertemplate="%{customdata}<br>MACD: %{y:.3f}<extra></extra>"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=sig_n,
        line=dict(color="#F57F17", width=1.8),
        name="시그널",
        customdata=date_labels,
        hovertemplate="%{customdata}<br>시그널: %{y:.3f}<extra></extra>"
    ), row=3, col=1)
    fig.add_annotation(x=1.01, y=0.08, xref="paper", yref="paper",
        text="<b style='color:#1565C0'>─</b> MACD<br>"
             "<b style='color:#F57F17'>─</b> 시그널<br>"
             "<b style='color:#2E7D32'>■</b> 양수<br>"
             "<b style='color:#E24B4A'>■</b> 음수",
        showarrow=False, align="left", font=dict(size=11),
        bgcolor="rgba(255,255,255,0.85)", bordercolor="#DDD", borderwidth=1)

    # spike 3행 동시 연결을 위한 dummy trace
    fig.add_trace(go.Scatter(
        x=x_axis, y=[None]*n,
        showlegend=False, hoverinfo="skip",
        line=dict(width=0), mode="lines"
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=x_axis, y=[None]*n,
        showlegend=False, hoverinfo="skip",
        line=dict(width=0), mode="lines"
    ), row=3, col=1)

    spike_cfg = dict(
        showspikes=True, spikemode="across", spikethickness=1,
        spikedash="dot", spikecolor="#AAAAAA", spikesnap="cursor",
        matches="x"
    )

    fig.update_layout(
        height=600, showlegend=False,
        paper_bgcolor="white", plot_bgcolor="#F8F9FA",
        margin=dict(l=10, r=110, t=30, b=60),
        hovermode="x",
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#DDD"),
        xaxis =dict(**spike_cfg),
        xaxis2=dict(**spike_cfg),
        xaxis3=dict(**spike_cfg),
    )

    # tick 설정
    fig.update_xaxes(
        tickmode="array", tickvals=tick_vals, ticktext=tick_texts,
        tickangle=-30, showticklabels=False,
    )
    fig.update_xaxes(showticklabels=True, row=3, col=1)

    # y축 스타일
    fig.update_yaxes(gridcolor="#EEEEEE", row=1, col=1)
    fig.update_yaxes(gridcolor="#EEEEEE", range=[0,100], row=2, col=1)
    fig.update_yaxes(gridcolor="#EEEEEE", row=3, col=1)

    # ── 메트릭 ─────────────────────────────────────────
    cur_rsi   = round(float(rsi_n[-1]),1)
    cur_macd  = round(float(macd_n[-1]),2)
    cur_sig   = round(float(sig_n[-1]),2)
    cur_bb_up = float(bb_up_n[-1]); cur_bb_low = float(bb_low_n[-1])
    current   = c_n[-1]
    bb_pos    = "상단 돌파⚠️" if current>cur_bb_up else "하단 이탈🟢" if current<cur_bb_low else "밴드 내"

    mc1,mc2,mc3,mc4 = st.columns(4)
    mc1.metric("RSI(14)", cur_rsi, "과매수⚠️" if cur_rsi>=70 else "과매도🟢" if cur_rsi<=30 else "중립")
    mc2.metric("MACD", cur_macd, "상승🟢" if cur_macd>cur_sig else "하락🔴")
    mc3.metric("시그널", cur_sig)
    mc4.metric("볼린저 위치", bb_pos)
    st.plotly_chart(fig, use_container_width=True, key=chart_key or f"chart_{code}")

    return rsi, macd_line, sig_line, dates_raw

    # 날짜 가져오기
    dates_raw = []
    try:
        if token:
            # 국내: KIS API — n일치 날짜
            end   = datetime.today().strftime("%Y%m%d")
            start = (datetime.today()-timedelta(days=n+30)).strftime("%Y%m%d")
            r2 = requests.get(
                f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                headers=kis_headers(APP_KEY,APP_SECRET,token,"FHKST03010100"),
                params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                        "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                        "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=7)
            items2 = r2.json().get("output2",[])
            dates_raw = [d.get("stck_bsop_date","") for d in items2 if d.get("stck_clpr")]
            dates_raw.reverse()
        else:
            # 해외(나스닥): yfinance
            import yfinance as yf
            hist = yf.Ticker(code).history(period="6mo")
            if not hist.empty:
                dates_raw = [d.strftime("%Y%m%d") for d in hist.index]
    except: pass

    # x축 날짜 생성 — YYYYMMDD → MM.DD
    if len(dates_raw) >= n:
        d_list = dates_raw[-n:]
        x_axis = []
        for ds in d_list:
            ds = str(ds)
            if len(ds) == 8:
                x_axis.append(f"{ds[4:6]}.{ds[6:]}")
            else:
                x_axis.append(str(ds)[:10][5:].replace('-','.'))
    else:
        # 날짜 없으면 역순 인덱스
        x_axis = [f"D-{n-i}" for i in range(n)]

    # 15일 간격 tick
    tick_step = 15
    tick_indices = list(range(0, n, tick_step))
    tick_vals = [x_axis[i] for i in tick_indices if i < len(x_axis)]

    xaxis_cfg = dict(
        tickmode="array",
        tickvals=tick_vals,
        ticktext=tick_vals,
        tickangle=-30,
        showspikes=True, spikemode="across",
        spikesnap="cursor", spikecolor="#888888",
        spikethickness=1, spikedash="dot"
    )

def render_7day_table(closes, volumes, dates_raw, rsi_series, macd_series, is_foreign=False, exc_rate=0):
    """최근 7거래일 추이 표"""
    rows_html = ""
    dates_use = dates_raw if dates_raw else [f"D-{abs(i)}" for i in range(-1,-9,-1)]
    avg_vol = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0

    for i in range(-1, -8, -1):
        try:
            p = closes[i]; po = closes[i-1]; v = volumes[i] if volumes else 0
            dc = (p-po)/po*100
            chg_color = "#E24B4A" if dc>0 else "#1565C0"
            r_val = round(float(rsi_series.iloc[i]), 1)
            m_val = round(float(macd_series.iloc[i]), 2)

            # 종가/변동 표시
            if is_foreign:
                price_str = f"${p:,.2f}"
                if exc_rate > 0:
                    price_str += f'<br><span style="font-size:.75rem;color:var(--text-muted)">≈{int(p*exc_rate):,}원</span>'
                change_str = f"${p-po:+,.2f}"
            else:
                price_str = f"{int(p):,}원"
                change_str = f"{int(p-po):+,}원"

            # 등락률 색상 — + 빨강, - 파랑
            chg_color = "#E24B4A" if dc > 0 else "#1565C0"

            # RSI 신호
            if r_val >= 70:
                rsi_signal = f'<span style="color:#E24B4A;font-weight:700">{r_val}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
            elif r_val <= 30:
                rsi_signal = f'<span style="color:#1565C0;font-weight:700">{r_val}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
            else:
                rsi_signal = f'<span style="color:var(--text-main)">{r_val}</span>'

            # MACD 신호
            if m_val > 0:
                macd_signal = f'<span style="color:#1565C0;font-weight:700">{m_val}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
            else:
                macd_signal = f'<span style="color:#E24B4A;font-weight:700">{m_val}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'

            # 거래량
            if avg_vol > 0 and v >= avg_vol * 1.5:
                vol_signal = f'<span style="color:#1565C0;font-weight:700">{int(v):,}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
            elif avg_vol > 0 and v <= avg_vol * 0.5:
                vol_signal = f'<span style="color:#E24B4A;font-weight:700">{int(v):,}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
            else:
                vol_signal = f"{int(v):,}"

            date_str = dates_use[i] if abs(i) <= len(dates_use) else ""
            if isinstance(date_str, str) and len(date_str)==8:
                # YYYYMMDD → MM.DD
                date_str = f"{date_str[4:6]}.{date_str[6:]}"
            elif isinstance(date_str, str) and len(date_str)==10:
                # YYYY-MM-DD → MM.DD
                date_str = date_str[5:].replace('-','.')

            rows_html += (
                '<tr style="border-bottom:1px solid var(--border);font-size:1rem">' +
                f'<td style="padding:13px 10px;text-align:center;color:var(--text-muted)">{date_str}</td>' +
                f'<td style="padding:13px 10px;text-align:center;font-weight:600">{price_str}</td>' +
                f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{change_str}</td>' +
                f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{dc:+.2f}%</td>' +
                f'<td style="padding:13px 10px;text-align:center">{vol_signal}</td>' +
                f'<td style="padding:13px 10px;text-align:center">{rsi_signal}</td>' +
                f'<td style="padding:13px 10px;text-align:center">{macd_signal}</td>' +
                '</tr>'
            )
        except: break

    st.markdown(
        '<table style="width:100%;border-collapse:collapse;font-size:1rem;background:var(--bg-card);border-radius:10px;overflow:hidden;box-shadow:0 2px 8px var(--shadow)">' +
        '<tr style="background:var(--bg-card2);font-weight:700;color:var(--text-main);font-size:1rem">' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">날짜</th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">종가</th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">변동</th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">등락률</th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">거래량<br><span style="font-size:.75rem;color:var(--text-light);font-weight:400">평균1.5배↑<span style="color:#2E7D32;font-size:1rem">●</span></span></th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">RSI<br><span style="font-size:.75rem;color:var(--text-light);font-weight:400">30↓<span style="color:#2E7D32;font-size:1rem">●</span> 70↑<span style="color:#E24B4A;font-size:1rem">●</span></span></th>' +
        '<th style="padding:12px 10px;border-bottom:2px solid var(--border);text-align:center">MACD<br><span style="font-size:.75rem;color:var(--text-light);font-weight:400">양수<span style="color:#2E7D32;font-size:1rem">●</span> 음수<span style="color:#E24B4A;font-size:1rem">●</span></span></th>' +
        '</tr>' + rows_html + '</table>',
        unsafe_allow_html=True
    )


def kis_headers(app_key, app_secret, token, tr_id):
    return {
        "authorization":f"Bearer {token}",
        "appkey":app_key,"appsecret":app_secret,
        "tr_id":tr_id,"content-type":"application/json; charset=utf-8",
    }

@st.cache_data(ttl=1800, show_spinner=False)
def get_price_info(code, app_key, app_secret, token):
    try:
        res = requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=kis_headers(app_key,app_secret,token,"FHKST01010100"),
            params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code},
            timeout=5  # 빠른 응답
        )
        d=res.json().get("output",{})
        return {"current":float(d.get("stck_prpr",0) or 0),"per":float(d.get("per",0) or 0),
                "pbr":float(d.get("pbr",0) or 0),"eps":float(d.get("eps",0) or 0),
                "name":d.get("hts_kor_isnm","")}
    except:
        return {}

@st.cache_data(ttl=1800, show_spinner=False)
def get_ohlcv_info(code, app_key, app_secret, token):
    try:
        end=(datetime.today()).strftime("%Y%m%d")
        start=(datetime.today()-timedelta(days=300)).strftime("%Y%m%d")
        res=requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers=kis_headers(app_key,app_secret,token,"FHKST03010100"),
            params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                    "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                    "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},
            timeout=7
        )
        items=res.json().get("output2",[])
        if not items or len(items)<25: return {}
        closes=[float(d.get("stck_clpr",0) or 0) for d in items if d.get("stck_clpr")]
        vols=[float(d.get("acml_vol",0) or 0) for d in items if d.get("acml_vol")]
        if not closes: return {}
        closes.reverse(); vols.reverse()
        cur=closes[-1]
        ma25=sum(closes[-25:])/25 if len(closes)>=25 else cur
        gap=round(cur/ma25*100,1) if ma25>0 else 100
        v7=sum(vols[-7:])/7 if len(vols)>=7 else 0
        v90=sum(vols[-90:])/90 if len(vols)>=90 else 1
        vi=round(v7/v90,2) if v90>0 else 1.0
        h52=max(closes); l52=min(closes)
        neg=round((cur-l52)/(h52-l52)*100,1) if h52!=l52 else 50
        exp=round((h52-cur)/cur*100,1) if cur>0 else 0
        ret30=round((cur/closes[-30]-1)*100,1) if len(closes)>=30 else 0
        return {"current":cur,"gap":gap,"vol_idx":vi,"neglect":neg,"exp_ret":exp,"ret30":ret30,
                "closes":closes}
    except:
        return {}

@st.cache_data(ttl=86400, show_spinner=False)
def get_name_from_naver(code):
    """네이버 금융에서 종목명 가져오기"""
    try:
        code = str(code).zfill(6)
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
        # og:title 메타태그에서 종목명 추출
        import re
        match = re.search(r'<title>([^:]+)\s*:', res.text)
        if match:
            name = match.group(1).strip()
            if name and len(name) < 20:
                return name
        # h2 태그에서 추출
        match2 = re.search(r'<h2[^>]*class="[^"]*h_company[^"]*"[^>]*>.*?<a[^>]*>([^<]+)<', res.text, re.DOTALL)
        if match2:
            return match2.group(1).strip()
    except:
        pass
    return ""

def get_stock_name(code, api_name=""):
    """종목명 우선순위: API → THEME_MAP → STOCK_NAMES → 네이버"""
    code = str(code).strip().zfill(6)
    # 1. KIS API 응답
    if api_name and api_name.strip():
        return api_name.strip()
    # 2. THEME_MAP (965개)
    if code in THEME_MAP:
        return THEME_MAP[code]["name"]
    # 3. STOCK_NAMES 하드코딩
    if code in STOCK_NAMES:
        return STOCK_NAMES[code]
    # 4. 네이버 금융
    naver_name = get_name_from_naver(code)
    if naver_name:
        return naver_name
    return f"종목 {code}"

def get_themes(code):
    """종목 테마 목록 반환"""
    if code in THEME_MAP:
        return THEME_MAP[code].get("themes", [])
    return []

def calc_lb(r, peg_max, eps_min, gap_max, sector_min, vol_min, lynch_w, bnf_w):
    peg=r.get("peg",99); eg=r.get("eps_growth",0)
    gap=r.get("gap",100); sg=r.get("sector_gap",0); vi=r.get("vol_idx",1)
    ls=min(100,max(0,(1.0-peg)*50)+min(eg,50))
    bs=0
    if gap<94: bs+=40
    elif gap<100: bs+=20
    if sg>=sector_min: bs+=35
    if vi>=1.5: bs+=25
    elif vi>=vol_min: bs+=15
    lb=round(ls*lynch_w+bs*bnf_w,1)
    cat="🚀 고속성장" if eg>=25 else "💪 견실성장" if eg>=10 else "🐢 완만성장"
    grade="강력매수" if peg<=0.5 else "매수" if peg<=1.0 else "보유" if peg<=1.5 else "고평가"
    return {"lynch_score":round(ls,1),"bnf_score":round(bs,1),"lb_score":lb,"category":cat,"peg_grade":grade}

KOSPI=["005930","000660","035420","005380","051910","006400","035720","000270",
       "068270","105560","055550","096770","003550","017670","018260","034730",
       "316140","086790","032830","011200","066570","010130","012330","009150",
       "011170","028260","033780","000810","036570","047050","030200","003490",
       "010950","139480","042660","011780","009830","088350","251270","090430",
       "004020","006280","011690","000720","012450","009540","010060","161390",
       "015760","000100"]
KOSDAQ=["247540","086520","373220","196170","263750","112040","357780","122870",
        "058470","041510","293490","112610","145020","950130","140860","237690",
        "214150","091990","236200","096530","035900","078600","039030","033290",
        "215600","036930","053800","064550","131370","082640","009420","036810",
        "041830","054780","060280","065350","067160","078020","086960","091580",
        "094360","095660","099190","101490","122310","141080","145990","153460",
        "166090","178320"]

# ── 나스닥 100 종목 리스트 ──────────────────────────────
NASDAQ100 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST",
    "NFLX","ASML","AMD","QCOM","PEP","ADBE","AMAT","TXN","CSCO","INTU",
    "AMGN","HON","BKNG","INTC","ISRG","SBUX","LRCX","MU","MDLZ","ADP",
    "GILD","PANW","VRTX","ADI","REGN","KLAC","SNPS","CDNS","MNST","FTNT",
    "MELI","CSX","ORLY","PYPL","CTAS","NXPI","PAYX","MRVL","AEP","ROST",
    "CPRT","WDAY","KHC","ODFL","PCAR","CRWD","FAST","DXCM","IDXX","VRSK",
    "BIIB","EXC","FANG","CTSH","EA","BKR","GEHC","ON","CEG","XEL",
    "TEAM","ZS","DASH","ANSS","DLTR","WBD","SIRI","ILMN","WBA","ENPH",
    "MRNA","PDD","TTD","PLTR","ANET","ABNB","GFS","CSGP","ALGN","DDOG",
    "MDB","LCID","RIVN","ARM","SMCI","APP","IREN","BTQ","NOK","IONQ"
]

def get_yf_batch(tickers):
    """yfinance 병렬처리로 여러 종목 한번에 가져오기 (캐시 없음 - 항상 최신)"""
    try:
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def fetch_one(ticker):
            try:
                stock = yf.Ticker(ticker)
                hist  = stock.history(period="6mo")
                if hist.empty or len(hist) < 25:
                    return ticker, None
                closes = hist['Close'].astype(float).tolist()
                vols   = hist['Volume'].astype(float).tolist()
                cur    = closes[-1]
                ma25   = sum(closes[-25:])/25 if len(closes)>=25 else cur
                gap    = round(cur/ma25*100, 1) if ma25>0 else 100
                v7     = sum(vols[-7:])/7 if len(vols)>=7 else 0
                v90    = sum(vols[-90:])/90 if len(vols)>=90 else 1
                vi     = round(v7/v90, 2) if v90>0 else 1.0
                h52    = max(closes); l52 = min(closes)
                neg    = round((cur-l52)/(h52-l52)*100,1) if h52!=l52 else 50
                exp    = round((h52-cur)/cur*100,1) if cur>0 else 0
                ret30  = round((cur/closes[-30]-1)*100,1) if len(closes)>=30 else 0

                # info에서 PER/PBR/EPS/성장률
                try:
                    si = stock.info
                    per = float(si.get('trailingPE') or si.get('forwardPE') or 0)
                    pbr = float(si.get('priceToBook') or 0)
                    eps = float(si.get('trailingEps') or 0)
                    # earningsGrowth는 소수점(0.183 = 18.3%) → 반드시 *100
                    raw_growth = si.get('earningsGrowth') or si.get('revenueGrowth') or 0
                    eps_growth = round(float(raw_growth) * 100, 1)
                    name = si.get('shortName') or si.get('longName') or ticker
                except:
                    per=0; pbr=0; eps=0; eps_growth=0; name=ticker

                return ticker, {
                    "current": cur, "per": per, "pbr": pbr, "eps": eps,
                    "eps_growth": eps_growth, "gap": gap, "vol_idx": vi,
                    "neglect": neg, "exp_ret": exp, "ret30": ret30,
                    "closes": closes, "volumes": vols, "name": name, "sector_gap": 0
                }
            except Exception as e:
                return ticker, None

        results = {}
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = {ex.submit(fetch_one, t): t for t in tickers}
            for f in as_completed(futures):
                ticker, data = f.result()
                if data:
                    results[ticker] = data
        return results
    except:
        return {}

# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 파라미터")

    # 시장 먼저 선택 — 나스닥 여부에 따라 기본값 자동 조정
    market = st.selectbox("시장", ["KOSPI","KOSDAQ","KOSPI+KOSDAQ","🇺🇸 나스닥100"])
    is_nasdaq = (market == "🇺🇸 나스닥100")

    if is_nasdaq:
        st.info("🇺🇸 나스닥100 최적 파라미터 자동 적용")
        _peg_def, _eps_def, _per_def = 2.0, 10, 60
        _gap_def, _sec_def, _vol_def = 110, 0, 1.0
    else:
        _peg_def, _eps_def, _per_def = 1.5, 8, 40
        _gap_def, _sec_def, _vol_def = 103, 0, 1.0

    peg_max    = st.slider("PEG 상한",           0.3, 3.0, float(_peg_def), 0.1,
                           help="나스닥 성장주는 2.0 권장 / 국내는 1.5 권장")
    eps_min    = st.slider("EPS 성장률 하한(%)",  5,   50,  _eps_def,  1,
                           help="나스닥 10%+ / 국내 8%+")
    per_max    = st.slider("PER 상한",            5,   80,  _per_def,  1,
                           help="나스닥 성장주는 60 이상도 흔함")
    gap_max    = st.slider("이격도 상한(%)",       85, 120, _gap_def,  1,
                           help="나스닥 110% / 국내 103% 권장")
    sector_min = st.slider("섹터 소외도 하한(%)",  0,   20,  _sec_def,  1,
                           help="나스닥은 0 권장 (섹터 계산 미지원)")
    vol_min    = st.slider("거래량지수 하한",      1.0, 3.0, _vol_def, 0.1,
                           help="1.0 = 최소한의 거래 있으면 OK")
    lynch_w    = st.slider("린치 가중치",         0.3, 0.8, 0.6, 0.1,
                           help="0.6 = 펀더멘털 60% + 타이밍 40%")
    bnf_w      = round(1.0-lynch_w, 1)
    top_n      = st.slider("상위 종목 수", 5, 30, 10, 1)
    st.markdown("---")
    st.caption("💡 파라미터 가이드")
    st.caption("결과 0개 → PEG/이격도 올리기")
    st.caption("결과 너무 많음 → PEG/EPS 내리기")
    st.caption("주 1~2회 judal_theme_crawler.py 실행 권장")

# ── Anthropic API 키 (secrets에서만 읽기, 화면 노출 없음) ──
try:
    ant_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    ant_key = ""

try:
    if "AI_PASSWORD" in st.secrets:
        ai_password = str(st.secrets["AI_PASSWORD"])
    else:
        ai_password = ""
except:
    ai_password = ""

# ── API 키 ──────────────────────────────────────────────
try:
    APP_KEY    = st.secrets["KIS_APP_KEY"]
    APP_SECRET = st.secrets["KIS_APP_SECRET"]
    KEYS_OK    = True
except:
    APP_KEY    = ""
    APP_SECRET = ""
    KEYS_OK    = False

# ── 헤더 ────────────────────────────────────────────────
today_str = datetime.today().strftime("%Y년 %m월 %d일")
st.markdown(f"""
<div class="lb-header" style="display:flex;gap:24px;align-items:stretch;flex-wrap:wrap">
  <div style="flex:1;min-width:200px">
    <div class="date-badge">{today_str}</div>
    <h1>LB SCREENER</h1>
    <p>Lynch × BNF — 성장주 펀더멘털 발굴 + 기술적 타이밍 결합 | 한국투자증권 공식 API</p>
  </div>
  <div style="display:flex;gap:12px;align-items:stretch;flex-wrap:wrap">
    <div style="background:rgba(255,255,255,0.15);border-radius:12px;padding:16px 20px;min-width:200px;max-width:260px">
      <div style="font-size:.68rem;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,.7);margin-bottom:8px">📈 PETER LYNCH</div>
      <div style="font-size:.92rem;font-weight:700;color:white;margin-bottom:6px">월가의 전설적 펀드매니저</div>
      <div style="font-size:.8rem;color:rgba(255,255,255,.85);line-height:1.8">
        피델리티 마젤란 펀드를 13년간 운용하며 연평균 <b style="color:white">29%</b> 수익률 달성.<br>
        "내가 아는 종목에 투자하라"는 철학으로 유명.<br><br>
        핵심 지표 <b style="color:white">PEG</b> — PER을 EPS 성장률로 나눈 값.<br>
        <b style="color:#90CAF9">PEG &lt; 1이면 저평가</b>, 아무리 PER이 높아도 성장률이 더 높으면 싼 주식이라고 봤음.
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.15);border-radius:12px;padding:16px 20px;min-width:200px;max-width:260px">
      <div style="font-size:.68rem;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,.7);margin-bottom:8px">⚡ BNF (B.N.F)</div>
      <div style="font-size:.92rem;font-weight:700;color:white;margin-bottom:6px">일본의 전설적 개인 투자자</div>
      <div style="font-size:.8rem;color:rgba(255,255,255,.85);line-height:1.8">
        300만엔으로 시작해 200억엔 이상으로 불린 일본 주식 신화.<br>
        자신만의 규칙 하나로 승부 — <b style="color:white">이격도</b>.<br><br>
        주가가 25일 이동평균에서 크게 <b style="color:#90CAF9">이탈(눌림목)</b>하면 매수, 회복하면 매도.<br>
        "주가는 반드시 평균으로 돌아온다"는 평균회귀 전략.
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

if not KEYS_OK:
    st.error("KIS API 키 미설정 — Streamlit Cloud → Settings → Secrets에 KIS_APP_KEY, KIS_APP_SECRET 입력")
    st.stop()

# ── 탭 ──────────────────────────────────────────────────
tab_theme, tab_search, tab_foreign, tab_lb = st.tabs(["🗂 테마 탐색기", "🔍 종목 검색", "🌏 해외 종목", "📊 LB 스크리너"])
tab1 = tab_lb
tab2 = tab_theme
tab3 = tab_search
tab4 = tab_foreign

# ════════════════════════════════════════════════════════
# 탭1: LB 스크리너
# ════════════════════════════════════════════════════════
with tab1:
    # ── Stage 카드 4개 + 지표 해설 ──────────────────────
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f'''<div class="stage-card stage-lynch">
<div class="stage-label lynch-label">Stage 1 · 피터 린치</div>
<div class="stage-title">펀더멘털 필터</div>
<div class="stage-criteria">PEG <b>{peg_max}</b> 이하<br>EPS 성장률 <b>{eps_min}%+</b> 확인<br>6분류 — 고속성장주 우선</div>
<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">
<div style="font-size:.78rem;color:var(--text-sub);line-height:1.9">
<b style="color:#1565C0">PEG 기준</b><br>
0.5↓ <b style="color:#2E7D32">강력매수</b> · 1.0↓ <b style="color:#1565C0">매수</b><br>
1.5↓ <b style="color:#F57F17">보유</b> · 1.5↑ <b style="color:#C62828">고평가</b><br>
<span style="color:var(--text-light);font-size:.72rem">PER이 높아도 성장률이 더 높으면 저평가</span>
</div></div>''', unsafe_allow_html=True)

    with c2:
        st.markdown(f'''<div class="stage-card stage-bnf">
<div class="stage-label bnf-label">Stage 2 · BNF</div>
<div class="stage-title">타이밍 필터</div>
<div class="stage-criteria">이격도 <b>{gap_max}%</b> 이하<br>섹터 내 소외 <b>{sector_min}%+</b><br>거래량 급증 확인</div>
<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">
<div style="font-size:.78rem;color:var(--text-sub);line-height:1.9">
<b style="color:#6A1B9A">이격도 기준</b><br>
97↓ <b style="color:#2E7D32">눌림목</b> · 103↓ <b style="color:#F57F17">이평근처</b><br>
103↑ <b style="color:#C62828">과열주의</b><br>
<span style="color:var(--text-light);font-size:.72rem">현재가 ÷ 25일이평 × 100</span>
</div></div>''', unsafe_allow_html=True)

    with c3:
        st.markdown(f'''<div class="stage-card stage-score">
<div class="stage-label score-label">Stage 3 · 결합</div>
<div class="stage-title">LB 스코어 산출</div>
<div class="stage-criteria">린치 품질 <b>×{lynch_w}</b><br>BNF 타이밍 <b>×{bnf_w}</b><br>상위 종목 자동 선별</div>
<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">
<div style="font-size:.78rem;color:var(--text-sub);line-height:1.9">
<b style="color:#F57F17">LB 스코어 기준</b><br>
70↑ <b style="color:#2E7D32">최우선</b> · 50↑ <b style="color:#1565C0">관심</b><br>
30↑ <b style="color:#F57F17">참고</b> · 30↓ <b style="color:#C62828">미달</b><br>
<span style="color:var(--text-light);font-size:.72rem">린치×{lynch_w} + BNF×{bnf_w} 결합 점수</span>
</div></div>''', unsafe_allow_html=True)

    with c4:
        st.markdown(f'''<div class="stage-card stage-report">
<div class="stage-label report-label">Stage 4 · 리포트</div>
<div class="stage-title">AI 투자 분석</div>
<div class="stage-criteria">Claude API 종목 해설<br>펀더멘털 + 기술적 분석<br>리스크 요인 자동 진단</div>
<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">
<div style="font-size:.78rem;color:var(--text-sub);line-height:1.9">
<b style="color:#2E7D32">EPS 성장률</b><br>
25%↑ <b style="color:#2E7D32">고속성장</b> · 10%↑ <b style="color:#1565C0">견실</b><br>
10%↓ <b style="color:#F57F17">완만</b><br>
<span style="color:var(--text-light);font-size:.72rem">린치는 연 25%+ 성장주 선호</span>
</div></div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    run = st.button("▶ 스크리닝 실행", use_container_width=True, key="run_btn")

    if "results"  not in st.session_state: st.session_state.results  = None
    if "token"    not in st.session_state: st.session_state.token    = ""

    if run:
        # ── 나스닥100 스크리닝 (yfinance 병렬처리) ──────────
        if market == "🇺🇸 나스닥100":
            stat = st.empty()
            stat.markdown("⚡ 나스닥100 병렬 수집 중... (20~30초 소요)")
            prog = st.progress(0)

            with st.spinner("yfinance 병렬 처리 중..."):
                yf_data = get_yf_batch(NASDAQ100)

            prog.progress(50)
            stat.markdown(f"✅ {len(yf_data)}개 종목 수집 완료 — LB 스코어 계산 중...")

            results = []
            for i, ticker in enumerate(NASDAQ100):
                d = yf_data.get(ticker)
                if not d: continue
                per = d.get("per", 0); eps_growth = d.get("eps_growth", 0)
                if per <= 0: continue
                exp_ret = d.get("exp_ret", 0)
                neglect = d.get("neglect", 50)
                eps_growth_raw = d.get("eps_growth", 0)

                # yfinance earningsGrowth는 소수점(0.183=18.3%) → 100 곱해야 함
                # get_yf_batch에서 이미 *100 처리되어 있으면 그대로, 아니면 변환
                eps_growth = eps_growth_raw if eps_growth_raw > 1 else eps_growth_raw * 100

                # EPS 성장률 근사
                if eps_growth > 0:
                    eg = eps_growth
                else:
                    eg = max(
                        exp_ret * 0.5,
                        max(0, (100 - neglect) / 5),
                        5.0
                    )

                # PEG 계산
                if per > 0 and eg > 0:
                    peg = round(per / eg, 2)
                elif per > 0:
                    peg = round(per / 10, 2)
                else:
                    peg = 1.0

                # 나스닥 필터 — PER 상한 완화 (성장주 특성상 PER 높음)
                if per > 0 and peg > peg_max: continue
                if d.get("gap", 100) > gap_max: continue
                # PER 상한은 나스닥에서 제외 (PLTR 같은 고PER 성장주 포함)

                rec = {
                    "code": ticker, "name": d.get("name", ticker),
                    "current": d["current"], "per": per,
                    "pbr": d.get("pbr", 0), "eps": d.get("eps", 0),
                    "eps_growth": eg, "peg": peg,
                    "gap": d.get("gap", 100), "vol_idx": d.get("vol_idx", 1),
                    "sector_gap": 0, "neglect": neglect,
                    "exp_ret": exp_ret, "themes": [],
                    "is_foreign": True,
                    "closes": d.get("closes", []),
                    "volumes": d.get("volumes", [])
                }
                scores = calc_lb(rec, peg_max, eps_min, gap_max, sector_min, vol_min, lynch_w, bnf_w)
                rec.update(scores)

                # 서술형 해설
                gap_now = d.get("gap", 100)
                parts = []
                if peg <= 0.5:   parts.append(f"이익 성장 속도에 비해 주가가 절반도 안 되게 저평가받고 있어요(PEG {peg}).")
                elif peg <= 1.0: parts.append(f"성장 속도 대비 주가가 저렴한 편입니다(PEG {peg}). 피터 린치가 좋아하는 구간이에요.")
                elif peg <= 1.5: parts.append(f"성장성 대비 주가가 적정 수준입니다(PEG {peg}).")
                if gap_now < 94:   parts.append(f"최근 평균가보다 {100-gap_now:.0f}% 낮게 거래 중이에요. 눌림목 매수 타이밍입니다.")
                elif gap_now < 100: parts.append(f"평균선 아래({gap_now}%)에 있어 반등 가능성이 있는 구간이에요.")
                if exp_ret > 30: parts.append(f"52주 고점 대비 {exp_ret}% 낮아 고점 회복 시 큰 수익을 기대할 수 있어요.")
                rec["reason_text"] = " ".join(parts[:3]) if parts else f"PEG {peg}, 이격도 {gap_now}% 기준 LB 조건 충족 종목입니다."
                results.append(rec)
                prog.progress(50 + int((i+1)/len(NASDAQ100)*50))

            prog.empty(); stat.empty()
            if not results:
                st.warning("조건 충족 종목이 없습니다. PEG 상한이나 이격도 상한을 높여보세요.")
            st.session_state.results = sorted(results, key=lambda x:x["lb_score"], reverse=True)[:top_n]
            st.session_state.token = ""  # 나스닥은 token 불필요

        # ── 국내 스크리닝 (KIS API) ──────────────────────────
        else:
            with st.spinner("KIS API 토큰 발급 중..."):
                token = get_kis_token(APP_KEY, APP_SECRET)
            if not token:
                st.error("토큰 발급 실패. App Key / App Secret을 확인해주세요.")
                st.stop()
            st.session_state.token = token

            codes = KOSPI if market=="KOSPI" else KOSDAQ if market=="KOSDAQ" else KOSPI+KOSDAQ
            try:
                sam=get_ohlcv_info("005930",APP_KEY,APP_SECRET,token)
                mkt_ret=sam.get("ret30",0)
            except:
                mkt_ret=0

            results=[]; prog=st.progress(0); stat=st.empty()
            for i,code in enumerate(codes):
                pct=int((i+1)/len(codes)*100)
                prog.progress(pct)
                pi=get_price_info(code,APP_KEY,APP_SECRET,token)
                if not pi or pi.get("per",0)<=0 or pi.get("eps",0)<=0:
                    continue
                name=get_stock_name(code, pi.get("name",""))
                per=pi.get("per",0); pbr=pi.get("pbr",0)
                eps=pi.get("eps",0); current=pi.get("current",0)
                stat.markdown(f"🔍 **{name}** 분석 중... `{pct}%`")
                ov=get_ohlcv_info(code,APP_KEY,APP_SECRET,token)
                if not ov: continue

                # EPS 성장률 — 기대수익률 + 소외지수 복합 근사
                exp_ret = ov.get("exp_ret", 0)
                neglect = ov.get("neglect", 50)
                # 소외지수가 낮을수록(많이 빠진 종목일수록) 반등 여력 크다고 가정
                # 기대수익률(52주고점 회복 여력)을 성장률 프록시로 활용
                eg = max(
                    exp_ret * 0.5,                          # 기대수익률 기반
                    max(0, (100 - neglect) / 5),            # 소외지수 기반 (소외될수록 높게)
                    5.0                                     # 최소 5% 보장 (흑자 기업이면)
                )
                peg = round(per/eg, 2) if eg>0 else 99
                sg  = round(mkt_ret - ov.get("ret30",0), 1)

                rec = {"code":code,"name":name,"current":current,"per":per,"pbr":pbr,
                       "eps":eps,"eps_growth":eg,"peg":peg,"gap":ov.get("gap",100),
                       "vol_idx":ov.get("vol_idx",1),"sector_gap":sg,
                       "neglect":neglect,"exp_ret":exp_ret,
                       "themes":get_themes(code)}

                # ── 필터 (EPS 필터 완화 — 근사값이므로 PEG로 대체 판단) ──
                if peg > peg_max: continue
                if per > per_max: continue
                if ov.get("gap",100) > gap_max: continue
                # EPS/섹터소외 필터는 소프트하게 (결과 없음 방지)
                # eg < eps_min 이어도 PEG가 충분히 낮으면 통과

                rec.update(calc_lb(rec,peg_max,eps_min,gap_max,sector_min,vol_min,lynch_w,bnf_w))

                # ── 선별 이유 — 초보자 친화적 서술형 ──
                reason_parts = []
                gap_now = ov.get("gap", 100)
                vol_now = ov.get("vol_idx", 1)

                # ① 가격 매력도 (PEG 기반)
                if peg <= 0.5:
                    reason_parts.append(
                        f"이 종목은 현재 벌어들이는 이익의 성장 속도에 비해 주가가 절반도 안 되게 평가받고 있어요(PEG {peg}). "
                        f"쉽게 말해 '이 정도 실력이면 훨씬 비싸야 하는데 시장이 아직 모르고 있다'는 뜻입니다."
                    )
                elif peg <= 1.0:
                    reason_parts.append(
                        f"이익이 늘어나는 속도에 비해 주가가 저렴한 편입니다(PEG {peg}). "
                        f"피터 린치가 가장 좋아하는 구간으로, 성장주인데 아직 저평가된 상태예요."
                    )
                elif peg <= 1.5:
                    reason_parts.append(
                        f"성장성 대비 주가 수준이 적정 범위에 있습니다(PEG {peg}). "
                        f"크게 싸지는 않지만, 다른 조건들이 좋다면 관심 가질 만한 구간입니다."
                    )

                # ② 타이밍 (이격도 기반 — BNF 스타일)
                if gap_now < 94:
                    reason_parts.append(
                        f"주가가 최근 한 달 평균 가격보다 {100-gap_now:.0f}% 더 낮게 거래되고 있어요. "
                        f"일본의 전설적 트레이더 BNF이 즐겨 쓰는 '눌림목 매수' 전략에 딱 맞는 타이밍입니다."
                    )
                elif gap_now < 100:
                    reason_parts.append(
                        f"주가가 최근 한 달 평균선 바로 아래({gap_now}%)에 있어요. "
                        f"보통 이 구간에서 반등이 나오는 경우가 많고, BNF식 단기 매수 타이밍으로 봅니다."
                    )
                elif gap_now <= gap_max:
                    reason_parts.append(
                        f"주가가 평균선 근처({gap_now}%)에서 지지받고 있는지 확인 중입니다. "
                        f"지지가 확인되면 추가 상승 여력이 있을 수 있어요."
                    )

                # ③ 관심도 (소외지수 — 쉬운 말로)
                if neglect < 20:
                    reason_parts.append(
                        f"지난 1년 동안 투자자들의 관심에서 거의 벗어나 있던 종목이에요(관심도 하위 {neglect}%). "
                        f"아무도 주목하지 않을 때 사서, 관심 받을 때 파는 역발상 투자의 핵심 후보입니다."
                    )
                elif neglect < 40:
                    reason_parts.append(
                        f"1년 중 상당 기간 투자자들의 관심 밖에 있었던 종목입니다(관심도 {neglect}%). "
                        f"아직 많이 오르지 않아 뒤늦게 쫓아가는 위험이 적어요."
                    )

                # ④ 회복 여력
                if exp_ret > 40:
                    reason_parts.append(
                        f"작년 최고가 대비 현재 주가가 {exp_ret}%나 낮습니다. "
                        f"고점을 회복하기만 해도 그만큼의 수익을 기대할 수 있어요."
                    )
                elif exp_ret > 15:
                    reason_parts.append(
                        f"작년 최고가 대비 {exp_ret}% 낮은 가격에 거래 중이에요. "
                        f"고점 회복 시 {exp_ret}%의 수익 여력이 있습니다."
                    )

                # ⑤ 자산 대비 가격
                if pbr > 0 and pbr < 0.7:
                    reason_parts.append(
                        f"회사가 가진 순자산보다 주가가 더 싸요(PBR {pbr}). "
                        f"지금 당장 회사를 청산해도 주주에게 이익이 남는 수준입니다."
                    )
                elif pbr > 0 and pbr < 1.0:
                    reason_parts.append(
                        f"회사의 실제 자산 가치보다 주가가 낮게 평가받고 있어요(PBR {pbr}). "
                        f"자산 기준으로도 저평가된 상태입니다."
                    )

                # ⑥ 거래량 (관심 유입 신호)
                if vol_now >= 2.0:
                    reason_parts.append(
                        f"최근 거래량이 평소보다 {vol_now}배나 늘었어요. "
                        f"기관이나 큰손들이 조용히 매집하고 있다는 신호일 수 있습니다."
                    )
                elif vol_now >= 1.5:
                    reason_parts.append(
                        f"거래량이 평소 대비 {vol_now}배 수준으로, 서서히 투자자들의 관심이 모이고 있는 신호입니다."
                    )

                if reason_parts:
                    rec["reason_text"] = " ".join(reason_parts[:3])
                else:
                    rec["reason_text"] = (
                        f"저희 LB 스코어 기준(PEG {peg}, 이격도 {gap_now}%)으로 "
                        f"성장성과 타이밍이 동시에 충족된 종목으로 선별되었습니다."
                    )

                results.append(rec)
                # ── 실시간으로 발견 종목 즉시 표시 ──
                stat.markdown(f"🔍 `{pct}%` 분석 중... ✅ **{len(results)}개 발견** — 최근: {name}")


                prog.empty(); stat.empty()
                if not results:
                    st.warning("조건을 만족하는 종목이 없습니다. 사이드바에서 PEG 상한이나 이격도 상한을 높여보세요.")
                st.session_state.results=sorted(results,key=lambda x:x["lb_score"],reverse=True)[:top_n]

    if st.session_state.results:
        res=st.session_state.results
        token=st.session_state.token

        st.markdown(f'<div class="param-bar"><span style="font-size:.8rem;color:var(--text-muted);font-weight:700">적용 기준</span><span class="param-chip">PEG ≤ {peg_max}</span><span class="param-chip">EPS ≥ {eps_min}%</span><span class="param-chip purple">이격도 ≤ {gap_max}%</span><span class="param-chip purple">섹터소외 ≥ {sector_min}%</span></div>',unsafe_allow_html=True)

        m1,m2,m3,m4=st.columns(4)
        with m1: st.markdown(f'<div class="metric-box"><div class="metric-val">{len(res)}</div><div class="metric-lbl">발굴 종목</div></div>',unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-box"><div class="metric-val">{round(sum(r["peg"] for r in res)/len(res),2)}</div><div class="metric-lbl">평균 PEG</div></div>',unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-box"><div class="metric-val">{round(sum(r["eps_growth"] for r in res)/len(res),1)}%</div><div class="metric-lbl">평균 EPS성장</div></div>',unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-box"><div class="metric-val">{round(sum(r["lb_score"] for r in res)/len(res),1)}</div><div class="metric-lbl">평균 LB스코어</div></div>',unsafe_allow_html=True)

        st.markdown("<br>**발굴 종목 — LB스코어 순위**",unsafe_allow_html=True)
        for i,r in enumerate(res):
            rc={0:"rank1",1:"rank2",2:"rank3"}.get(i,"")
            rnc={0:"r1",1:"r2",2:"r3"}.get(i,"")
            bw=int(r["lb_score"]/120*120)
            cat=r["category"].split(" ")[-1]
            themes=r.get("themes",[])
            theme_tags="".join([f'<span class="theme-tag">{t}</span>' for t in themes[:4]])
            reason_text = r.get("reason_text", "")

            # 각 파트를 별도 변수로 분리
            theme_part = '<div style="margin-top:5px">' + theme_tags + '</div>' if theme_tags else ''
            reason_part = '<div style="background:var(--chip-bg);border-radius:10px;padding:10px 14px;font-size:.85rem;color:var(--text-sub);line-height:1.7;border-left:3px solid #1565C0;min-width:200px;max-width:340px;align-self:center">💡 ' + reason_text + '</div>' if reason_text else '<div style="min-width:10px"></div>'
            # 통화 표시 — 나스닥은 $, 국내는 원
            is_foreign = r.get("is_foreign", False)
            if is_foreign:
                current_val = f'${r["current"]:,.2f}'
                try:
                    exc = get_usd_krw()
                    krw_val = f'≈ {int(r["current"]*exc):,}원'
                except:
                    krw_val = ""
            else:
                current_val = f'{int(r["current"]):,}원'
                krw_val = ""
            name_val = r["name"]
            code_val = r["code"]
            peg_val = r["peg"]
            eps_val = f'{r["eps_growth"]:.1f}'
            gap_val = r["gap"]
            lb_val = r["lb_score"]
            grade_val = r["peg_grade"]

            price_line = current_val
            if krw_val:
                price_line += f'<span style="font-size:.78rem;color:var(--text-muted);margin-left:8px">{krw_val}</span>'

            card_html = (
                '<div class="stock-card ' + rc + '">'
                '<div class="stock-rank ' + rnc + '">' + str(i+1) + '</div>'
                '<div style="flex:1">'
                '<div><span class="stock-name">' + name_val + '</span>'
                '<span class="stock-code">' + code_val + '</span>'
                '<span class="stock-cat">' + cat + '</span></div>'
                '<div style="margin-top:4px">'
                '<span style="font-size:.78rem;color:var(--text-light)">현재가 </span>'
                '<span style="font-size:.85rem;font-weight:700">' + price_line + '</span>'
                '&nbsp;&nbsp;'
                '<span style="font-size:.75rem;color:#1565C0;font-weight:700">' + grade_val + '</span>'
                '</div>'
                + theme_part +
                '</div>'
                + reason_part +
                '<div class="stock-metrics">'
                '<div class="sm-item"><div class="sm-val green">PEG ' + str(peg_val) + '</div><div class="sm-lbl">린치지표</div></div>'
                '<div class="sm-item"><div class="sm-val blue">EPS ' + eps_val + '%</div><div class="sm-lbl">성장률</div></div>'
                '<div class="sm-item"><div class="sm-val purple">이격 ' + str(gap_val) + '%</div><div class="sm-lbl">BNF타이밍</div></div>'
                '<div class="sm-item"><div><div class="lb-bar" style="width:' + str(bw) + 'px"></div>'
                '<span class="sm-val orange">' + str(lb_val) + '</span></div><div class="sm-lbl">LB스코어</div></div>'
                '</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            with st.expander(f"📊 {r['name']} — RSI · MACD 차트"):
                # 나스닥 종목은 closes가 이미 있음, 국내는 API 호출
                if r.get("is_foreign") and r.get("closes"):
                    closes = r["closes"]
                else:
                    ov=get_ohlcv_info(r["code"],APP_KEY,APP_SECRET,st.session_state.get("token",""))
                    closes = ov.get("closes",[]) if ov else []
                if closes and len(closes)>=26:
                        rsi_s, macd_s, sig_s, dates_raw2 = render_domestic_chart(
                            r["code"], r["name"], closes, APP_KEY, APP_SECRET,
                            st.session_state.get("token",""), chart_key=f"lb_{r['code']}")
                        st.markdown("**📋 최근 7거래일 추이**")
                        # 거래량 — 나스닥은 rec에 저장된 값, 국내는 KIS API
                        if r.get("is_foreign"):
                            vols2 = r.get("volumes", [])
                        else:
                            try:
                                end2=datetime.today().strftime("%Y%m%d")
                                start2=(datetime.today()-timedelta(days=200)).strftime("%Y%m%d")
                                rv=requests.get(
                                    f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                                    headers=kis_headers(APP_KEY,APP_SECRET,st.session_state.get("token",""),"FHKST03010100"),
                                    params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":r["code"],
                                            "FID_INPUT_DATE_1":start2,"FID_INPUT_DATE_2":end2,
                                            "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=10)
                                vols2=[float(d.get("acml_vol",0) or 0) for d in rv.json().get("output2",[]) if d.get("stck_clpr")]
                                vols2.reverse()
                            except: vols2=[]
                        render_7day_table(closes, vols2, dates_raw2, rsi_s, macd_s, is_foreign=r.get("is_foreign",False), exc_rate=get_usd_krw() if r.get("is_foreign") else 0)
                        # 뉴스 — 나스닥은 영문 뉴스, 국내는 한글 뉴스
                        if r.get("is_foreign"):
                            news_list = get_foreign_news(r["name"])
                        else:
                            news_list = get_domestic_news(r["name"])
                        if news_list:
                            st.markdown("**📰 최신 뉴스**")
                            for nw in news_list:
                                st.markdown(f"🔗 [{nw['title']}]({nw['link']})")

        st.download_button("⬇ 결과 CSV",pd.DataFrame(res).to_csv(index=False,encoding="utf-8-sig"),
                           f"lb_{datetime.today().strftime('%Y%m%d')}.csv","text/csv")

        if ant_key:
            st.markdown('<br><div class="report-box">', unsafe_allow_html=True)
            st.markdown("### 📝 AI 종목 분석 리포트")
            stxt="\n".join([
                f"{i+1}. {r['name']}({r['code']}): PEG {r['peg']}, EPS {r['eps_growth']:.1f}%, "
                f"이격도 {r['gap']}%, 관심도 {r['neglect']}%, 고점대비 -{r['exp_ret']}%, LB {r['lb_score']}"
                for i,r in enumerate(res[:5])
            ])
            prompt = f"""오늘({today_str}) LB 스크리너(Lynch×BNF 독자 알고리즘)로 선별된 종목을 분석해주세요.

선별 종목:
{stxt}

선별 기준: PEG ≤ {peg_max}(성장 대비 저평가), 이격도 ≤ {gap_max}%(기술적 타이밍 포착)
※ LB 스코어: 피터 린치의 PEG 가치평가 + BNF의 이격도 타이밍을 결합한 독자 지표

다음 형식으로 투자 분석 리포트를 작성해주세요 (초보 투자자도 이해할 수 있게 쉽게):
1. 오늘 시장 상황 한 줄 요약
2. TOP3 종목 각각:
   - 왜 지금 이 종목인지 (성장성 + 타이밍 관점)
   - 주의해야 할 리스크 한 가지
3. 오늘 선별된 종목들의 공통점 (업종 트렌드 등)

전문적이되 친근한 어조, 800자 내외.
마지막: ※ 본 분석은 투자 참고용이며 투자 판단과 책임은 본인에게 있습니다."""


            if st.button("🤖 AI 분석 리포트 생성", use_container_width=True, key="ai_btn"):
                st.session_state["show_ai_pw_lb"] = True
            if st.session_state.get("show_ai_pw_lb"):
                pw_input = st.text_input("🔒 비밀번호 입력", type="password", key="ai_pw_lb")
                if pw_input:
                    if pw_input == ai_password:
                        import anthropic
                        client = anthropic.Anthropic(api_key=ant_key)
                        ph = st.empty(); txt = ""
                        with client.messages.stream(
                            model="claude-opus-4-5", max_tokens=1500,
                            messages=[{"role":"user","content":prompt}]
                        ) as s:
                            for t in s.text_stream:
                                txt += t; ph.markdown(txt+"▌")
                        ph.markdown(txt)
                        st.session_state["show_ai_pw_lb"] = False
                    else:
                        st.error("❌ 비밀번호가 틀렸습니다.")
            st.markdown('</div>', unsafe_allow_html=True)

    elif not run:
        st.info("👆 스크리닝 실행 버튼을 누르거나 앱을 새로고침하면 자동으로 시작됩니다.")

# ════════════════════════════════════════════════════════
# 탭2: 테마 탐색기
# ════════════════════════════════════════════════════════
with tab2:
    if not THEME_OK:
        st.warning("테마 데이터가 없습니다. `python extract_theme_map.py` 를 먼저 실행해주세요.")
        st.stop()

    st.markdown("<br>", unsafe_allow_html=True)

    # 테마 선택
    col_sel, col_info = st.columns([2, 1])
    with col_sel:
        selected_theme = st.selectbox(
            "테마 선택",
            options=sorted(THEME_STOCKS.keys()),
            format_func=lambda x: f"{x} ({len(THEME_STOCKS[x])}개 종목)"
        )
    with col_info:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="metric-box"><div class="metric-val">{len(THEME_STOCKS[selected_theme])}</div><div class="metric-lbl">{selected_theme} 종목 수</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 선택한 테마의 종목 목록
    theme_codes = THEME_STOCKS[selected_theme]

    if st.button("▶ 테마 종목 LB 분석", use_container_width=True, key="theme_btn"):
        with st.spinner("KIS API 토큰 확인 중..."):
            token = get_kis_token(APP_KEY, APP_SECRET)
        if not token:
            st.error("토큰 발급 실패.")
            st.stop()
        st.session_state.token = token

        try:
            sam=get_ohlcv_info("005930",APP_KEY,APP_SECRET,token)
            mkt_ret=sam.get("ret30",0)
        except:
            mkt_ret=0

        theme_results = []
        prog2 = st.progress(0)
        stat2 = st.empty()
        total2 = len(theme_codes)

        for i, code in enumerate(theme_codes):
            prog2.progress(int((i+1)/total2*100))
            pi = get_price_info(code, APP_KEY, APP_SECRET, token)
            if not pi: continue  # sleep 제거 — 캐시 히트 시 불필요
            name = get_stock_name(code, pi.get("name",""))
            stat2.markdown(f"🔍 `{i+1}/{total2}` **{name}**")
            per=pi.get("per",0); eps=pi.get("eps",0)
            current=pi.get("current",0); pbr=pi.get("pbr",0)

            # OHLCV — 캐시 활용 (ttl=600)
            ov = get_ohlcv_info(code, APP_KEY, APP_SECRET, token)
            if not ov: continue

            exp_ret = ov.get("exp_ret", 0)
            neglect = ov.get("neglect", 50)
            eg = max(exp_ret*0.5, max(0,(100-neglect)/5), 5.0)
            peg = round(per/eg,2) if eg>0 and per>0 else 99
            sg = round(mkt_ret - ov.get("ret30",0), 1)

            rec = {"code":code,"name":name,"current":current,"per":per,"pbr":pbr,
                   "eps":eps,"eps_growth":eg,"peg":peg,"gap":ov.get("gap",100),
                   "vol_idx":ov.get("vol_idx",1),"sector_gap":sg,
                   "neglect":neglect,"exp_ret":exp_ret}
            scores = calc_lb(rec,peg_max,eps_min,gap_max,sector_min,vol_min,lynch_w,bnf_w)
            rec.update(scores)

            # 서술형 설명 — 초보자 친화적
            t_parts = []
            gap_now = ov.get("gap",100)

            if peg <= 0.5:
                t_parts.append(f"이익 성장 속도에 비해 주가가 절반도 안 되게 저평가받고 있어요(PEG {peg}). 시장이 아직 이 종목의 가치를 모르고 있는 상태입니다.")
            elif peg <= 1.0:
                t_parts.append(f"성장 속도 대비 주가가 저렴한 편입니다(PEG {peg}). 피터 린치가 가장 좋아하는 저평가 성장주 구간이에요.")
            elif peg <= 1.5:
                t_parts.append(f"성장성 대비 주가가 적정 수준입니다(PEG {peg}). 다른 조건이 좋다면 관심 가질 만한 구간이에요.")
            else:
                t_parts.append(f"현재 성장성 대비 주가가 다소 높은 편입니다(PEG {peg}). 신중한 접근이 필요합니다.")

            if gap_now < 94:
                t_parts.append(f"최근 한 달 평균 주가보다 {100-gap_now:.0f}% 더 낮게 거래 중이에요. BNF 전략의 핵심인 눌림목 매수 타이밍입니다.")
            elif gap_now < 100:
                t_parts.append(f"평균선 바로 아래({gap_now}%)에 있어 반등 가능성이 있는 구간이에요.")
            elif gap_now <= 103:
                t_parts.append(f"평균선 근처({gap_now}%)에서 지지받고 있는지 확인 중입니다.")
            else:
                t_parts.append(f"평균선보다 {gap_now-100:.0f}% 높게 거래 중이에요. 눌림목을 기다리는 게 좋을 수 있어요.")

            if neglect < 20:
                t_parts.append(f"지난 1년간 투자자들의 관심에서 거의 벗어나 있던 종목이에요. 아무도 주목하지 않을 때 사는 역발상 전략의 핵심 후보입니다.")
            elif neglect < 40:
                t_parts.append(f"1년 중 상당 기간 관심을 받지 못했던 종목이에요. 아직 많이 오르지 않아 뒤늦게 쫓아가는 위험이 적습니다.")

            if exp_ret > 30:
                t_parts.append(f"작년 최고가 대비 현재 {exp_ret}%나 낮게 거래 중이에요. 고점 회복만 해도 큰 수익을 기대할 수 있습니다.")

            if pbr > 0 and pbr < 1.0:
                t_parts.append(f"회사의 실제 자산 가치보다 주가가 더 싸요(PBR {pbr}). 자산 기준으로도 저평가된 상태입니다.")

            rec["reason_text"] = " ".join(t_parts[:3]) if t_parts else f"LB 스코어 기준(PEG {peg}, 이격도 {gap_now}%)으로 성장성과 타이밍이 동시에 충족된 종목으로 선별되었습니다."
            theme_results.append(rec)

        prog2.empty(); stat2.empty()
        st.session_state["theme_results"] = sorted(theme_results, key=lambda x:x["lb_score"], reverse=True)
        st.session_state["theme_name"] = selected_theme

    # 테마 결과 표시
    if "theme_results" in st.session_state and st.session_state.theme_results:
        tr = st.session_state.theme_results

        # 요약 메트릭
        pass_count = sum(1 for r in tr if r["peg"]<=peg_max and r["eps_growth"]>=eps_min and r["gap"]<=gap_max)
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-box"><div class="metric-val">{len(tr)}</div><div class="metric-lbl">전체 종목</div></div>',unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-box"><div class="metric-val" style="color:#2E7D32">{pass_count}</div><div class="metric-lbl">LB 조건 충족</div></div>',unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-box"><div class="metric-val">{round(sum(r["lb_score"] for r in tr)/len(tr),1)}</div><div class="metric-lbl">평균 LB스코어</div></div>',unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-box"><div class="metric-val">{round(sum(r["gap"] for r in tr)/len(tr),1)}%</div><div class="metric-lbl">평균 이격도</div></div>',unsafe_allow_html=True)

        st.markdown(f"<br>**{selected_theme} 테마 — LB스코어 순위**", unsafe_allow_html=True)

        for r in tr:
            lb = r["lb_score"]
            lb_ok = r["peg"]<=peg_max and r["eps_growth"]>=eps_min and r["gap"]<=gap_max
            ok_mark = "✅" if lb_ok else "⬜"
            if lb >= 50:   badge = '<span class="lb-badge-high">LB ' + str(lb) + '</span>'
            elif lb >= 30: badge = '<span class="lb-badge-mid">LB ' + str(lb) + '</span>'
            else:          badge = '<span class="lb-badge-low">LB ' + str(lb) + '</span>'

            peg_color = "#2E7D32" if r["peg"]<=peg_max else "#C62828"
            gap_color = "#2E7D32" if r["gap"]<=gap_max else "#C62828"
            reason_text = r.get("reason_text", "")

            row_html = (
                '<div class="theme-stock-row">'
                '<div style="font-size:1.1rem;min-width:24px">' + ok_mark + '</div>'
                '<div style="flex:1">'
                '<div>'
                '<span style="font-weight:700;color:#212121">' + r["name"] + '</span>'
                '<span style="font-size:.75rem;color:#555555;margin-left:6px">' + r["code"] + '</span>'
                '<span style="font-size:.78rem;color:#444444;margin-left:10px">현재가 ' + f'{int(r["current"]):,}' + '원</span>'
                '</div>'
                '<div style="margin-top:5px;font-size:.82rem;color:#333333;line-height:1.6;'
                'background:rgba(123,31,162,0.1);border-radius:8px;padding:7px 12px;border-left:3px solid #7B1FA2">'
                '💡 ' + reason_text +
                '</div>'
                '</div>'
                '<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-left:12px">'
                '<div style="text-align:center"><div style="font-size:.9rem;font-weight:700;color:' + peg_color + '">PEG ' + str(r["peg"]) + '</div><div style="font-size:.68rem;color:var(--text-light)">린치</div></div>'
                '<div style="text-align:center"><div style="font-size:.9rem;font-weight:700;color:#1565C0">이격 ' + str(r["gap"]) + '%</div><div style="font-size:.68rem;color:var(--text-light)">BNF</div></div>'
                '<div>' + badge + '</div>'
                '</div>'
                '</div>'
            )
            st.markdown(row_html, unsafe_allow_html=True)

            # 클릭하면 차트+7일표+뉴스 펼치기
            with st.expander(f"📊 {r['name']} 상세 분석 보기"):
                t_token = st.session_state.get("token","")
                t_ov = get_ohlcv_info(r["code"], APP_KEY, APP_SECRET, t_token)
                if t_ov and t_ov.get("closes") and len(t_ov["closes"]) >= 26:
                    t_closes = t_ov["closes"]
                    rsi_t, macd_t, sig_t, dates_t = render_domestic_chart(
                        r["code"], r["name"], t_closes, APP_KEY, APP_SECRET, t_token,
                        chart_key=f"theme_{r['code']}")
                    st.markdown("**📋 최근 7거래일 추이**")
                    try:
                        end_t=datetime.today().strftime("%Y%m%d")
                        start_t=(datetime.today()-timedelta(days=200)).strftime("%Y%m%d")
                        rv_t=requests.get(
                            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                            headers=kis_headers(APP_KEY,APP_SECRET,st.session_state.get("token",""),"FHKST03010100"),
                            params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":r["code"],
                                    "FID_INPUT_DATE_1":start_t,"FID_INPUT_DATE_2":end_t,
                                    "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=10)
                        vols_t=[float(d.get("acml_vol",0) or 0) for d in rv_t.json().get("output2",[]) if d.get("stck_clpr")]
                        vols_t.reverse()
                    except: vols_t=[]
                    render_7day_table(t_closes, vols_t, dates_t, rsi_t, macd_t)
                    t_news = get_domestic_news(r["name"])
                    if t_news:
                        st.markdown("**📰 최신 뉴스**")
                        for nw in t_news:
                            st.markdown(f"🔗 [{nw['title']}]({nw['link']})")
        st.download_button(
            f"⬇ {selected_theme} 테마 CSV",
            pd.DataFrame(tr).to_csv(index=False, encoding="utf-8-sig"),
            f"theme_{selected_theme}_{datetime.today().strftime('%Y%m%d')}.csv",
            "text/csv", key="theme_csv"
        )
    else:
        # 테마 종목 미리보기 (분석 전)
        st.markdown(f"**{selected_theme} 테마 종목 목록** ({len(theme_codes)}개)")
        preview_cols = st.columns(5)
        for i, code in enumerate(theme_codes):
            name = get_stock_name(code)
            preview_cols[i%5].markdown(
                f'<div style="background:var(--bg-card);border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:.82rem;box-shadow:0 1px 4px rgba(0,0,0,.07)">'
                f'<b>{name}</b><br><span style="color:var(--text-light);font-size:.72rem">{code}</span></div>',
                unsafe_allow_html=True
            )
        st.info("👆 **테마 종목 LB 분석** 버튼을 눌러 LB 조건 충족 여부를 확인하세요.")

# ════════════════════════════════════════════════════════
# 탭3: 개별 종목 검색
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)

    # 전체 종목 검색용 딕셔너리 (STOCK_NAMES + THEME_MAP 통합)
    ALL_STOCKS = {**STOCK_NAMES}
    if THEME_OK:
        for code, info in THEME_MAP.items():
            if code not in ALL_STOCKS:
                ALL_STOCKS[code] = info["name"]

    # 검색창
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input(
            "종목명 또는 종목코드 입력",
            placeholder="예) 삼성전자  또는  005930",
            label_visibility="collapsed"
        )
    with col_s2:
        search_btn = st.button("🔍 검색", use_container_width=True, key="search_btn")

    # 검색 결과 후보 표시
    if search_query:
        query = search_query.strip()
        candidates = []

        # 코드 직접 입력
        if query.isdigit() and len(query) == 6:
            name = ALL_STOCKS.get(query, query)
            candidates = [(query, name)]
        else:
            # 이름으로 검색
            for code, name in ALL_STOCKS.items():
                if query in name or query.upper() in name.upper():
                    candidates.append((code, name))
            candidates = candidates[:10]

        if not candidates:
            st.warning("검색 결과가 없습니다. 종목명 또는 6자리 코드를 입력해주세요.")
        elif len(candidates) == 1:
            selected_code, selected_name = candidates[0]
            search_btn = True  # 하나면 바로 분석
        else:
            st.markdown(f"**{len(candidates)}개 종목이 검색되었습니다. 분석할 종목을 선택하세요.**")
            sel_options = {f"{name} ({code})": code for code, name in candidates}
            sel_choice = st.selectbox("종목 선택", list(sel_options.keys()), label_visibility="collapsed")
            selected_code = sel_options[sel_choice]
            selected_name = ALL_STOCKS.get(selected_code, selected_code)
            search_btn = st.button("▶ 이 종목 분석", use_container_width=True, key="search_go")

    if search_btn and search_query:
        token = get_kis_token(APP_KEY, APP_SECRET)
        if not token:
            st.error("토큰 발급 실패.")
            st.stop()
        st.session_state.token = token

        with st.spinner(f"{selected_name} 분석 중..."):
            pi = get_price_info(selected_code, APP_KEY, APP_SECRET, token)
            ov = get_ohlcv_info(selected_code, APP_KEY, APP_SECRET, token)

        if not pi or not ov:
            st.error("데이터를 가져오지 못했습니다.")
            st.stop()

        # 기본 데이터
        current = pi.get("current", 0)
        per     = pi.get("per", 0)
        pbr     = pi.get("pbr", 0)
        eps     = pi.get("eps", 0)
        api_name = pi.get("name", "")
        name    = get_stock_name(selected_code, api_name)
        exp_ret = ov.get("exp_ret", 0)
        neglect = ov.get("neglect", 50)
        gap_now = ov.get("gap", 100)
        vol_now = ov.get("vol_idx", 1)

        # EPS 성장률 근사
        eg  = max(exp_ret*0.5, max(0,(100-neglect)/5), 5.0)
        peg = round(per/eg, 2) if eg>0 and per>0 else 99
        sg  = 0  # 개별 검색은 섹터 소외도 생략

        rec = {"code":selected_code,"name":name,"current":current,"per":per,"pbr":pbr,
               "eps":eps,"eps_growth":eg,"peg":peg,"gap":gap_now,
               "vol_idx":vol_now,"sector_gap":sg,"neglect":neglect,"exp_ret":exp_ret}
        scores = calc_lb(rec,peg_max,eps_min,gap_max,sector_min,vol_min,lynch_w,bnf_w)
        rec.update(scores)
        themes = get_themes(selected_code)

        # ── 종목 헤더 ──────────────────────────────────
        theme_tags = "".join([f'<span class="theme-tag">{t}</span>' for t in themes[:5]])
        theme_div  = f'<div style="margin-top:6px">{theme_tags}</div>' if theme_tags else ''

        lb    = rec["lb_score"]
        grade = rec["peg_grade"]
        cat   = rec["category"]

        if lb >= 70:   lb_color = "#2E7D32"
        elif lb >= 50: lb_color = "#1565C0"
        elif lb >= 30: lb_color = "#F57F17"
        else:          lb_color = "#9E9E9E"

        st.markdown(
            '<div style="background:var(--bg-card);border-radius:14px;padding:20px 24px;'
            'box-shadow:0 4px 16px rgba(0,0,0,.08);margin-bottom:16px">'
            '<div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">'
            '<div style="flex:1">'
            '<div style="font-size:1.4rem;font-weight:900;color:var(--text-main)">' + name +
            '<span style="font-size:.8rem;color:var(--text-light);margin-left:8px;font-weight:400">' + selected_code + '</span></div>'
            '<div style="margin-top:4px">'
            '<span style="font-size:1.1rem;font-weight:700">' + f'{int(current):,}원' + '</span>'
            '<span style="font-size:.8rem;color:#1565C0;margin-left:10px;font-weight:700">' + cat + '</span>'
            '</div>'
            + theme_div +
            '</div>'
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;min-width:360px">'

            # PEG — 1.0 이하 초록, 1.5 이하 주황, 그 외 빨강
            + '<div style="text-align:center;background:var(--chip-bg);border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if peg<=1.0 else "#F57F17" if peg<=1.5 else "#E24B4A") + '">PEG ' + str(peg) + '</div>'
            + '<div style="font-size:.72rem;color:var(--text-light);margin-top:2px">린치 지표</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if peg<=1.0 else "#F57F17" if peg<=1.5 else "#E24B4A") + '">' + ("🟢 저평가" if peg<=1.0 else "🟡 적정" if peg<=1.5 else "🔴 고평가") + '</div></div>'

            # 이격도 — 100% 미만 초록, 103% 이하 주황, 초과 빨강
            + '<div style="text-align:center;background:var(--chip-bg);border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if gap_now<100 else "#F57F17" if gap_now<=103 else "#E24B4A") + '">이격 ' + str(gap_now) + '%</div>'
            + '<div style="font-size:.72rem;color:var(--text-light);margin-top:2px">BNF 타이밍</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if gap_now<100 else "#F57F17" if gap_now<=103 else "#E24B4A") + '">' + ("🟢 눌림목" if gap_now<100 else "🟡 이평근처" if gap_now<=103 else "🔴 과열") + '</div></div>'

            # PBR — 1.0 미만 초록, 2.0 이하 주황, 초과 빨강
            + '<div style="text-align:center;background:var(--chip-bg);border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if 0<pbr<1.0 else "#F57F17" if pbr<=2.0 else "#E24B4A") + '">PBR ' + str(pbr) + '</div>'
            + '<div style="font-size:.72rem;color:var(--text-light);margin-top:2px">자산 대비</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if 0<pbr<1.0 else "#F57F17" if pbr<=2.0 else "#9E9E9E") + '">' + ("🟢 자산이하" if 0<pbr<1.0 else "🟡 적정" if pbr<=2.0 else "–") + '</div></div>'

            # LB스코어 — 70↑ 초록, 50↑ 파랑, 30↑ 주황, 미만 회색
            + '<div style="text-align:center;background:var(--chip-bg);border-radius:10px;padding:10px">'
            + '<div style="font-size:1.3rem;font-weight:900;color:' + lb_color + '">' + str(lb) + '</div>'
            + '<div style="font-size:.72rem;color:var(--text-light);margin-top:2px">LB 스코어</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + lb_color + '">' + ("🟢 최우선" if lb>=70 else "🔵 관심" if lb>=50 else "🟡 참고" if lb>=30 else "⬜ 미달") + '</div></div>'

            + '</div></div></div>',
            unsafe_allow_html=True
        )

        # ── 분석 해설 ──────────────────────────────────
        reason_parts = []
        if peg <= 0.5:
            reason_parts.append(f"이익 성장 속도에 비해 주가가 절반도 안 되게 저평가받고 있어요(PEG {peg}). 시장이 아직 이 종목의 가치를 모르고 있는 상태입니다.")
        elif peg <= 1.0:
            reason_parts.append(f"성장 속도 대비 주가가 저렴한 편입니다(PEG {peg}). 피터 린치가 가장 좋아하는 저평가 성장주 구간이에요.")
        elif peg <= 1.5:
            reason_parts.append(f"성장성 대비 주가가 적정 수준입니다(PEG {peg}). 다른 조건들과 함께 종합적으로 판단이 필요해요.")
        else:
            reason_parts.append(f"현재 성장성 대비 주가가 다소 높은 편입니다(PEG {peg}). 신중한 접근이 필요합니다.")

        if gap_now < 94:
            reason_parts.append(f"최근 한 달 평균 주가보다 {100-gap_now:.0f}% 더 낮게 거래 중이에요. BNF 전략의 핵심인 눌림목 매수 타이밍에 해당합니다.")
        elif gap_now < 100:
            reason_parts.append(f"평균선 바로 아래({gap_now}%)에 있어 반등 가능성이 있는 구간이에요.")
        elif gap_now <= 103:
            reason_parts.append(f"평균선 근처({gap_now}%)에서 거래 중입니다. 지지 여부를 확인하는 구간이에요.")
        else:
            reason_parts.append(f"평균선보다 {gap_now-100:.0f}% 높게 거래 중이에요. 눌림목을 기다리는 전략도 고려해볼 만합니다.")

        if neglect < 20:
            reason_parts.append(f"지난 1년간 투자자들의 관심에서 거의 벗어나 있던 종목이에요. 아무도 주목하지 않을 때 사는 역발상 전략의 핵심 후보입니다.")
        elif neglect < 40:
            reason_parts.append(f"1년 중 상당 기간 관심을 받지 못했던 종목이에요. 아직 많이 오르지 않아 뒤늦게 쫓아가는 위험이 적습니다.")
        elif neglect > 75:
            reason_parts.append(f"최근 1년 중 상위 {100-neglect:.0f}% 구간에 있어요. 이미 많이 오른 상태로 추가 상승 여력을 꼼꼼히 확인해야 합니다.")

        if exp_ret > 40:
            reason_parts.append(f"작년 최고가 대비 현재 {exp_ret}%나 낮게 거래 중이에요. 고점 회복 시 큰 수익을 기대할 수 있습니다.")
        elif exp_ret > 15:
            reason_parts.append(f"작년 최고가 대비 {exp_ret}% 낮은 가격이에요. 고점 회복 시 {exp_ret}%의 수익 여력이 있습니다.")

        if pbr > 0 and pbr < 0.7:
            reason_parts.append(f"회사가 가진 순자산보다 주가가 더 싸요(PBR {pbr}). 자산 가치만 봐도 저평가된 상태입니다.")
        elif pbr > 0 and pbr < 1.0:
            reason_parts.append(f"회사의 실제 자산 가치보다 주가가 낮게 평가받고 있어요(PBR {pbr}).")

        if vol_now >= 2.0:
            reason_parts.append(f"최근 거래량이 평소보다 {vol_now}배나 늘었어요. 기관이나 큰손들이 조용히 관심을 보이는 신호일 수 있습니다.")
        elif vol_now >= 1.5:
            reason_parts.append(f"거래량이 평소 대비 {vol_now}배로, 서서히 투자자들의 관심이 모이고 있는 신호입니다.")

        reason_html = " ".join(reason_parts[:4])
        st.markdown(
            '<div style="background:var(--chip-bg);border-radius:12px;padding:16px 20px;'
            'border-left:4px solid #1565C0;margin-bottom:16px;font-size:.9rem;'
            'color:var(--text-sub);line-height:1.8">💡 ' + reason_html + '</div>',
            unsafe_allow_html=True
        )

        # ── RSI/MACD/볼린저밴드 차트 ───────────────────
        st.markdown("**📊 주가 · RSI · MACD · 볼린저밴드 차트**")
        closes = ov.get("closes", [])
        token3 = st.session_state.get("token", "")
        if closes and len(closes) >= 26:
            rsi_s3, macd_s3, sig_s3, dates_raw3 = render_domestic_chart(
                selected_code, name, closes, APP_KEY, APP_SECRET, token3,
                chart_key=f"search_{selected_code}")
            st.markdown("**📋 최근 7거래일 추이**")
            try:
                end3=datetime.today().strftime("%Y%m%d")
                start3=(datetime.today()-timedelta(days=150)).strftime("%Y%m%d")
                rv3=requests.get(
                    f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                    headers=kis_headers(APP_KEY,APP_SECRET,token3,"FHKST03010100"),
                    params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":selected_code,
                            "FID_INPUT_DATE_1":start3,"FID_INPUT_DATE_2":end3,
                            "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=7)
                vols3=[float(d.get("acml_vol",0) or 0) for d in rv3.json().get("output2",[]) if d.get("stck_clpr")]
                vols3.reverse()
            except: vols3=[]
            render_7day_table(closes, vols3, dates_raw3, rsi_s3, macd_s3)

        # ── 뉴스 ───────────────────────────────────────
        news3 = get_domestic_news(name)
        if news3:
            st.markdown("**📰 최신 뉴스**")
            for nw in news3:
                st.markdown(f"🔗 [{nw['title']}]({nw['link']})")

        # ── AI 종목 분석 (로컬 전용) ───────────────────
        if ant_key:
            st.markdown('<div class="report-box">', unsafe_allow_html=True)
            st.markdown("### 🤖 AI 종목 심층 분석")
            single_prompt = f"""오늘({today_str}) {name}({selected_code}) 종목을 분석해주세요.

주요 지표:
- 현재가: {int(current):,}원
- PEG: {peg} (성장성 대비 밸류에이션)
- PBR: {pbr} (자산 대비 주가)
- PER: {per}
- 이격도: {gap_now}% (최근 평균가 대비)
- 1년간 관심도: {neglect}% (낮을수록 소외)
- 고점 대비 하락률: -{exp_ret}%
- 거래량 지수: {vol_now}배
- LB 스코어: {lb} / 100
- 소속 테마: {', '.join(themes) if themes else '해당 없음'}

분석 요청:
1. 이 종목을 지금 관심 가져야 하는 이유 (또는 주의해야 할 이유)
2. 피터 린치 관점: 성장성과 밸류에이션 평가
3. BNF 관점: 현재 기술적 타이밍 평가
4. 초보 투자자를 위한 핵심 체크포인트 2가지

친근하고 이해하기 쉬운 어조로, 700자 내외.
마지막: ※ 투자 판단과 책임은 본인에게 있습니다."""

            if st.button("🤖 AI 심층 분석", use_container_width=True, key="single_ai"):
                st.session_state["show_ai_pw_single"] = True
            if st.session_state.get("show_ai_pw_single"):
                pw_input2 = st.text_input("🔒 비밀번호 입력", type="password", key="ai_pw_single")
                if pw_input2:
                    if pw_input2 == ai_password:
                        import anthropic
                        client = anthropic.Anthropic(api_key=ant_key)
                        ph = st.empty(); txt = ""
                        with client.messages.stream(
                            model="claude-opus-4-5", max_tokens=1200,
                            messages=[{"role":"user","content":single_prompt}]
                        ) as s:
                            for t in s.text_stream:
                                txt += t; ph.markdown(txt+"▌")
                        ph.markdown(txt)
                        st.session_state["show_ai_pw_single"] = False
                    else:
                        st.error("❌ 비밀번호가 틀렸습니다.")
            st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# 탭4: 해외 종목 분석 (yfinance)
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)

    if not YFINANCE_OK:
        st.error("yfinance 패키지가 필요합니다.")
        st.code("pip install yfinance")
        st.stop()

    # ── 한글 → 티커 사전 ───────────────────────────────
    US_DICT = {
        "애플":"AAPL","테슬라":"TSLA","엔비디아":"NVDA","마이크로소프트":"MSFT",
        "구글":"GOOGL","알파벳":"GOOGL","아마존":"AMZN","메타":"META","페이스북":"META",
        "넷플릭스":"NFLX","에이엠디":"AMD","인텔":"INTC","퀄컴":"QCOM","브로드컴":"AVGO",
        "팔란티어":"PLTR","아이온큐":"IONQ","쿠팡":"CPNG","노키아":"NOK",
        "아이렌":"IREN","비티큐":"BTQ","코인베이스":"COIN","마이크로스트레티지":"MSTR",
        "에이에스엠엘":"ASML","일라이릴리":"LLY","버크셔":"BRK-B",
        "TQQQ":"TQQQ","SOXL":"SOXL","SCHD":"SCHD","SPY":"SPY","QQQ":"QQQ",
        "IREN":"IREN","BTQ":"BTQ","NOK":"NOK","PLTR":"PLTR","NVDA":"NVDA",
        "TSLA":"TSLA","AAPL":"AAPL","MSFT":"MSFT","AMZN":"AMZN","META":"META",
    }

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_foreign_data(ticker):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            if df.empty or len(df) < 14:
                return None, None
            info = {}
            try:
                info = stock.info
            except:
                pass
            return df, info
        except:
            return None, None

    def calc_rsi(prices, period=14):
        s = pd.Series(prices)
        d = s.diff()
        gain = d.clip(lower=0).rolling(period).mean()
        loss = (-d.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, float('nan'))
        return (100 - 100/(1+rs)).fillna(50)

    def calc_bollinger(prices, period=20):
        s = pd.Series(prices)
        sma = s.rolling(period).mean()
        std = s.rolling(period).std()
        return sma+2*std, sma, sma-2*std

    def foreign_reason(ticker, current, prev_close, rsi_val, gap_bb, info):
        """해외 종목 분석 해설 — 초보자 친화적"""
        parts = []
        chg = (current - prev_close) / prev_close * 100

        if chg > 3:
            parts.append(f"오늘 {chg:.1f}% 급등했어요. 강한 매수세가 유입된 날입니다.")
        elif chg > 0:
            parts.append(f"오늘 {chg:.1f}% 상승 마감했습니다.")
        elif chg < -3:
            parts.append(f"오늘 {chg:.1f}% 급락했어요. 매도 압력이 컸던 하루입니다.")
        else:
            parts.append(f"오늘 {chg:.1f}% 소폭 하락했습니다.")

        if rsi_val is not None:
            if rsi_val <= 30:
                parts.append(f"RSI {rsi_val:.1f}로 과매도 구간이에요. 단기 반등을 노려볼 수 있는 타이밍입니다.")
            elif rsi_val >= 70:
                parts.append(f"RSI {rsi_val:.1f}로 과매수 구간이에요. 단기 조정 가능성을 염두에 두세요.")
            else:
                parts.append(f"RSI {rsi_val:.1f}로 중립 구간입니다. 추세를 좀 더 지켜볼 필요가 있어요.")

        if gap_bb is not None:
            if gap_bb < -0.05:
                parts.append(f"볼린저 밴드 하단 아래에 있어 강한 반등 가능성이 있는 구간이에요.")
            elif gap_bb > 0.05:
                parts.append(f"볼린저 밴드 상단을 돌파한 상태로, 강한 상승 모멘텀이 유지 중입니다.")

        pe = info.get("trailingPE") or info.get("forwardPE")
        if pe and pe > 0:
            if pe < 15:
                parts.append(f"PER {pe:.1f}로 해당 업종 대비 저평가 수준이에요.")
            elif pe > 50:
                parts.append(f"PER {pe:.1f}로 성장 기대감이 높게 반영된 주가입니다.")

        return " ".join(parts[:3])

    # ── UI ─────────────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(135deg,#1a237e,#0097A7);border-radius:12px;
padding:16px 24px;margin-bottom:20px;color:white">
<div style="font-size:1.1rem;font-weight:900;letter-spacing:2px">🌏 해외 종목 분석</div>
<div style="font-size:.85rem;opacity:.85;margin-top:4px">미국·해외 주식 — yfinance 실시간 데이터 | RSI · MACD · 볼린저밴드</div>
</div>
""", unsafe_allow_html=True)

    # 환율
    exc_rate = get_usd_krw()
    st.caption(f"💱 현재 환율: 1 USD = {exc_rate:,.0f}원")

    # 예시 버튼으로 선택된 티커 처리
    _example_ticker = st.session_state.pop("_foreign_example", None)

    # 검색창
    col_q, col_btn = st.columns([3, 1])
    with col_q:
        f_query = st.text_input(
            "종목 입력",
            placeholder="예) 엔비디아  /  NVDA  /  TSLA  /  테슬라",
            label_visibility="collapsed",
            key="foreign_query"
        )
    with col_btn:
        f_btn = st.button("🔍 분석", use_container_width=True, key="foreign_btn")

    # 티커 해석 (직접 입력 또는 예시 버튼)
    f_ticker = ""
    f_display_name = ""

    if _example_ticker:
        # 예시 버튼 클릭
        f_ticker = _example_ticker
        f_display_name = f_ticker
        f_btn = True
    elif f_query:
        q = f_query.strip()
        q_nospace = q.replace(" ","")
        matched = [(k,v) for k,v in US_DICT.items() if q_nospace in k or q_nospace.upper()==v.upper()]
        if matched:
            f_ticker = matched[0][1]
            f_display_name = matched[0][0]
        elif re.match(r'^[A-Za-z0-9.\-]+$', q):
            f_ticker = q.upper()
            f_display_name = f_ticker
        else:
            st.warning("검색어를 인식하지 못했어요. 영문 티커(예: NVDA)나 한글 종목명(예: 엔비디아)으로 입력해주세요.")

    if f_btn and f_ticker:
        with st.spinner(f"{f_ticker} 데이터 수집 중..."):
            df_f, info_f = get_foreign_data(f_ticker)

        if df_f is None or len(df_f) < 14:
            st.error(f"'{f_ticker}' 데이터를 가져오지 못했습니다. 티커를 확인해주세요.")
        else:
            closes   = df_f['Close'].astype(float).tolist()
            volumes  = df_f['Volume'].astype(float).tolist()
            dates    = df_f.index.strftime('%Y.%m.%d').tolist()
            current  = closes[-1]
            prev_c   = closes[-2]
            chg      = (current - prev_c) / prev_c * 100
            chg_color= "#E24B4A" if chg > 0 else "#1565C0"

            # 지표 계산
            rsi_series = calc_rsi(closes)
            rsi_val    = round(float(rsi_series.iloc[-1]), 1)
            s          = pd.Series(closes)
            ema12 = s.ewm(span=12).mean(); ema26 = s.ewm(span=26).mean()
            macd_line = ema12 - ema26; sig_line = macd_line.ewm(span=9).mean()
            macd_val  = round(float(macd_line.iloc[-1]), 3)
            sig_val   = round(float(sig_line.iloc[-1]), 3)
            bb_up, bb_mid, bb_low = calc_bollinger(closes)
            bb_up_v = float(bb_up.iloc[-1]); bb_low_v = float(bb_low.iloc[-1])
            bb_gap  = (current - bb_mid.iloc[-1]) / (bb_up_v - bb_low_v) if (bb_up_v - bb_low_v) > 0 else 0

            # 회사 기본 정보
            company_name = info_f.get("longName", f_display_name or f_ticker)
            sector       = info_f.get("sector", "")
            krw_price    = int(current * exc_rate)

            # ── 헤더 카드 ────────────────────────────
            st.markdown(
                '<div style="background:var(--bg-card);border-radius:14px;padding:20px 24px;'
                'box-shadow:0 4px 16px rgba(0,0,0,.08);margin-bottom:16px">'
                '<div style="font-size:1.4rem;font-weight:900;color:var(--text-main)">'
                + company_name +
                '<span style="font-size:.85rem;color:var(--text-light);margin-left:8px;font-weight:400">(' + f_ticker + ')</span>'
                + (f'<span style="font-size:.78rem;color:var(--text-muted);margin-left:8px">{sector}</span>' if sector else '') +
                '</div>'
                '<div style="margin-top:8px;display:flex;gap:20px;flex-wrap:wrap;align-items:center">'
                f'<span style="font-size:1.3rem;font-weight:900">${current:,.2f}</span>'
                f'<span style="color:{chg_color};font-weight:700;font-size:1rem">{chg:+.2f}%</span>'
                f'<span style="color:var(--text-muted);font-size:.9rem">≈ {krw_price:,}원</span>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

            # ── 지표 메트릭 4개 ──────────────────────
            m1,m2,m3,m4 = st.columns(4)
            rsi_label = "과매수⚠️" if rsi_val>=70 else "과매도🟢" if rsi_val<=30 else "중립"
            m1.metric("RSI(14)", rsi_val, rsi_label)
            m2.metric("MACD", macd_val, "상승🟢" if macd_val>sig_val else "하락🔴")
            m3.metric("시그널", sig_val)
            m4.metric("볼린저 위치", f"{bb_gap*100:+.1f}%",
                      "밴드 상단 돌파" if current>bb_up_v else "밴드 하단 이탈" if current<bb_low_v else "밴드 내")

            # ── 분석 해설 ────────────────────────────
            reason = foreign_reason(f_ticker, current, prev_c, rsi_val, bb_gap, info_f)
            st.markdown(
                '<div style="background:var(--chip-bg);border-radius:12px;padding:14px 18px;'
                'border-left:4px solid #1a237e;margin:12px 0;font-size:.9rem;color:var(--text-sub);line-height:1.8">'
                '💡 ' + reason + '</div>',
                unsafe_allow_html=True
            )

            # ── 차트 ─────────────────────────────────
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            n   = min(120, len(closes))
            c60 = closes[-n:]; d60 = dates[-n:]
            v60 = volumes[-n:]
            x60 = list(range(n))

            # 볼린저밴드 계산
            s_f = pd.Series(closes)
            bb_up_f  = (s_f.rolling(20).mean() + 2*s_f.rolling(20).std()).tolist()[-n:]
            bb_mid_f = s_f.rolling(20).mean().tolist()[-n:]
            bb_low_f = (s_f.rolling(20).mean() - 2*s_f.rolling(20).std()).tolist()[-n:]
            hist_f   = [m-s for m,s in zip(macd_line.tolist()[-n:], sig_line.tolist()[-n:])]
            hcolors_f = ["#E24B4A" if v<0 else "#2E7D32" for v in hist_f]

            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                row_heights=[0.55,0.22,0.23],
                vertical_spacing=0.04,
                subplot_titles=[f"{f_display_name} 주가 + 볼린저밴드","RSI (14)","MACD"]
            )

            fig.add_trace(go.Scatter(x=x60,y=c60,line=dict(color="#1565C0",width=2.5),name="종가",customdata=d60,hovertemplate="%{customdata}<br>종가: $%{y:,.3f}<extra></extra>"),row=1,col=1)
            fig.add_trace(go.Scatter(x=x60,y=bb_up_f,line=dict(color="#E24B4A",width=1.2,dash="dash"),name="BB상단",hovertemplate="BB상단: $%{y:,.3f}<extra></extra>"),row=1,col=1)
            fig.add_trace(go.Scatter(x=x60,y=bb_mid_f,line=dict(color="#F57F17",width=1.2),name="25일이평",hovertemplate="25일이평: $%{y:,.3f}<extra></extra>"),row=1,col=1)
            fig.add_trace(go.Scatter(x=x60,y=bb_low_f,line=dict(color="#2E7D32",width=1.2,dash="dash"),fill="tonexty",fillcolor="rgba(46,125,50,0.05)",name="BB하단",hovertemplate="BB하단: $%{y:,.3f}<extra></extra>"),row=1,col=1)

            fig.add_annotation(x=1.01,y=0.97,xref="paper",yref="paper",
                text="<b style='color:#1565C0'>─</b> 종가<br><b style='color:#E24B4A'>--</b> BB상단<br><b style='color:#F57F17'>─</b> 25일이평<br><b style='color:#2E7D32'>--</b> BB하단",
                showarrow=False,align="left",font=dict(size=11),
                bgcolor="rgba(255,255,255,0.85)",bordercolor="#DDD",borderwidth=1)

            rsi_f = rsi_series.tolist()[-n:]
            fig.add_trace(go.Scatter(x=x60,y=rsi_f,line=dict(color="#6A1B9A",width=2),name="RSI",customdata=d60,hovertemplate="%{customdata}<br>RSI: %{y:.3f}<extra></extra>"),row=2,col=1)
            fig.add_hline(y=70,line_dash="dash",line_color="#E24B4A",annotation_text="과매수(70)",annotation_position="right",annotation_font_size=10,row=2,col=1)
            fig.add_hline(y=30,line_dash="dash",line_color="#2E7D32",annotation_text="과매도(30)",annotation_position="right",annotation_font_size=10,row=2,col=1)

            fig.add_trace(go.Bar(x=x60,y=hist_f,marker_color=hcolors_f,name="히스토",customdata=d60,hovertemplate="%{customdata}<br>히스토: %{y:.3f}<extra></extra>"),row=3,col=1)
            fig.add_trace(go.Scatter(x=x60,y=macd_line.tolist()[-n:],line=dict(color="#1565C0",width=1.8),name="MACD",customdata=d60,hovertemplate="%{customdata}<br>MACD: %{y:.3f}<extra></extra>"),row=3,col=1)
            fig.add_trace(go.Scatter(x=x60,y=sig_line.tolist()[-n:],line=dict(color="#F57F17",width=1.8),name="시그널",customdata=d60,hovertemplate="%{customdata}<br>시그널: %{y:.3f}<extra></extra>"),row=3,col=1)
            fig.add_annotation(x=1.01,y=0.08,xref="paper",yref="paper",
                text="<b style='color:#1565C0'>─</b> MACD<br><b style='color:#F57F17'>─</b> 시그널<br><b style='color:#2E7D32'>■</b> 양수<br><b style='color:#E24B4A'>■</b> 음수",
                showarrow=False,align="left",font=dict(size=11),
                bgcolor="rgba(255,255,255,0.85)",bordercolor="#DDD",borderwidth=1)

            # x축 날짜 15일 간격
            f_tick_vals  = list(range(0, n, 15))
            f_tick_texts = [d60[i] if i < len(d60) else "" for i in f_tick_vals]

            # spike 3행 동시 연결
            fig.add_trace(go.Scatter(x=x60,y=[None]*n,showlegend=False,hoverinfo="skip",line=dict(width=0),mode="lines"),row=2,col=1)
            fig.add_trace(go.Scatter(x=x60,y=[None]*n,showlegend=False,hoverinfo="skip",line=dict(width=0),mode="lines"),row=3,col=1)

            f_spike_cfg = dict(
                showspikes=True, spikemode="across", spikethickness=1,
                spikedash="dot", spikecolor="#AAAAAA", spikesnap="cursor",
                matches="x"
            )
            fig.update_layout(height=600,showlegend=False,dragmode=False,paper_bgcolor="white",
                              plot_bgcolor="#F8F9FA",margin=dict(l=10,r=110,t=30,b=60),
                              hovermode="x",
                              hoverlabel=dict(bgcolor="white",font_size=12,bordercolor="#DDD"),
                              xaxis=dict(**f_spike_cfg),
                              xaxis2=dict(**f_spike_cfg),
                              xaxis3=dict(**f_spike_cfg))
            fig.update_xaxes(tickmode="array",tickvals=f_tick_vals,ticktext=f_tick_texts,
                             tickangle=-30,showticklabels=False)
            fig.update_xaxes(showticklabels=True,row=3,col=1)
            fig.update_yaxes(gridcolor="#EEEEEE")
            fig.update_yaxes(range=[0,100],row=2,col=1)
            st.plotly_chart(fig, use_container_width=True, key=f"foreign_{f_ticker}")

            # ── 최근 7거래일 표 ──────────────────────
            st.markdown("**📋 최근 7거래일 추이**")
            rows_html = ""
            avg_vol_f = sum(volumes[-20:]) / min(len(volumes),20) if volumes else 1
            for i in range(-1,-8,-1):
                try:
                    p  = closes[i]; po = closes[i-1]; v = volumes[i]
                    dc = (p-po)/po*100
                    chg_color = "#E24B4A" if dc>0 else "#1565C0"
                    r_val = round(rsi_series.tolist()[i], 1)
                    m_val = round(macd_line.tolist()[i], 3)

                    if r_val >= 70:
                        rsi_signal = f'<span style="color:#E24B4A;font-weight:700">{r_val}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
                    elif r_val <= 30:
                        rsi_signal = f'<span style="color:#1565C0;font-weight:700">{r_val}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
                    else:
                        rsi_signal = f'<span style="color:var(--text-main)">{r_val}</span>'

                    if m_val > 0:
                        macd_signal = f'<span style="color:#1565C0;font-weight:700">{m_val}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
                    else:
                        macd_signal = f'<span style="color:#E24B4A;font-weight:700">{m_val}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'

                    if v >= avg_vol_f * 1.5:
                        vol_signal = f'<span style="color:#1565C0;font-weight:700">{int(v):,}</span>&nbsp;<span style="color:#00C853;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
                    elif avg_vol_f > 0 and v <= avg_vol_f * 0.5:
                        vol_signal = f'<span style="color:#E24B4A;font-weight:700">{int(v):,}</span>&nbsp;<span style="color:#E24B4A;font-size:2rem;line-height:1;vertical-align:middle">●</span>'
                    else:
                        vol_signal = f"{int(v):,}"

                    rows_html += (
                        f'<tr style="border-bottom:1px solid #F0F0F0;font-size:1rem">'
                        f'<td style="padding:13px 10px;text-align:center;color:var(--text-muted)">{dates[i]}</td>'
                        f'<td style="padding:13px 10px;text-align:center;font-weight:600">${p:,.2f}</td>'
                        f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{dc:+.2f}%</td>'
                        f'<td style="padding:13px 10px;text-align:center">{vol_signal}</td>'
                        f'<td style="padding:13px 10px;text-align:center">{rsi_signal}</td>'
                        f'<td style="padding:13px 10px;text-align:center">{macd_signal}</td>'
                        f'</tr>'
                    )
                except: break

            st.markdown(
                '<table style="width:100%;border-collapse:collapse;font-size:1rem;background:var(--bg-card);border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)">'
                '<tr style="background:var(--bg-card2);font-weight:700;color:var(--text-sub)">'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">날짜</th>'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">종가</th>'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">등락률</th>'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">거래량</th>'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">RSI</th>'
                '<th style="padding:13px 10px;border-bottom:2px solid #EEE;text-align:center">MACD</th>'
                '</tr>' + rows_html + '</table>',
                unsafe_allow_html=True
            )

            # ── 뉴스 ────────────────────────────────
            news = get_foreign_news(company_name)
            if news:
                st.markdown("**📰 최신 뉴스**")
                for n in news:
                    st.markdown(f"🔗 [{n['title']}]({n['link']})")

            # ── AI 분석 (로컬 전용) ──────────────────
            if ant_key:
                st.markdown('<div class="report-box">', unsafe_allow_html=True)
                st.markdown("### 🤖 AI 종목 심층 분석")
                pe_val = info_f.get("trailingPE") or info_f.get("forwardPE") or "N/A"
                mkt_cap = info_f.get("marketCap", 0)
                mkt_cap_str = f"${mkt_cap/1e9:.1f}B" if mkt_cap > 1e9 else "N/A"

                f_prompt = f"""오늘({today_str}) {company_name}({f_ticker}) 해외 종목을 분석해주세요.

주요 지표:
- 현재가: ${current:,.2f} (약 {krw_price:,}원)
- 오늘 등락: {chg:+.2f}%
- RSI(14): {rsi_val} ({'과매수' if rsi_val>=70 else '과매도' if rsi_val<=30 else '중립'})
- MACD: {macd_val} / 시그널: {sig_val} ({'골든크로스' if macd_val>sig_val else '데드크로스'})
- 볼린저밴드 위치: {'상단 돌파' if current>bb_up_v else '하단 이탈' if current<bb_low_v else '밴드 내'}
- PER: {pe_val}
- 시가총액: {mkt_cap_str}
- 섹터: {sector}

분석 요청 (초보 투자자도 이해할 수 있게):
1. 이 종목을 지금 주목해야 하는 이유 또는 주의해야 할 점
2. RSI와 MACD가 말하는 현재 기술적 신호
3. 한국 투자자 관점에서 체크할 포인트 (환율, 섹터 트렌드 등)

700자 내외, 친근한 어조.
마지막: ※ 투자 판단과 책임은 본인에게 있습니다."""

                if st.button("🤖 AI 심층 분석", use_container_width=True, key="foreign_ai"):
                    st.session_state["show_ai_pw_foreign"] = True
                if st.session_state.get("show_ai_pw_foreign"):
                    pw_input3 = st.text_input("🔒 비밀번호 입력", type="password", key="ai_pw_foreign")
                    if pw_input3:
                        if pw_input3 == ai_password:
                            import anthropic
                            client = anthropic.Anthropic(api_key=ant_key)
                            ph = st.empty(); txt = ""
                            with client.messages.stream(
                                model="claude-opus-4-5", max_tokens=1200,
                                messages=[{"role":"user","content":f_prompt}]
                            ) as s:
                                for t in s.text_stream:
                                    txt += t; ph.markdown(txt+"▌")
                            ph.markdown(txt)
                            st.session_state["show_ai_pw_foreign"] = False
                        else:
                            st.error("❌ 비밀번호가 틀렸습니다.")
                st.markdown('</div>', unsafe_allow_html=True)

    elif not f_query and not _example_ticker:
        # 초기 안내
        st.markdown("**검색 예시** — 클릭하면 바로 분석됩니다")

        examples = [
            ("엔비디아","NVDA","AI 반도체"),("테슬라","TSLA","전기차"),("애플","AAPL","빅테크"),
            ("팔란티어","PLTR","AI 데이터"),("아이온큐","IONQ","양자컴퓨터"),("아이렌","IREN","비트코인 채굴"),
            ("노키아","NOK","통신장비"),("비티큐","BTQ","양자암호"),("쿠팡","CPNG","한국이커머스"),
        ]
        cols = st.columns(3)
        for i,(kr,ticker,desc) in enumerate(examples):
            with cols[i%3]:
                if st.button(f"{kr}  {ticker} · {desc}", key=f"ex_{ticker}", use_container_width=True):
                    st.session_state["_foreign_example"] = ticker
                    st.rerun()

    # 예시 버튼으로 선택된 경우 처리
    if "f_query" not in dir() or not f_query:
        if "_foreign_example" in st.session_state:
            f_ticker    = st.session_state.pop("_foreign_example")
            f_display_name = f_ticker
            f_btn = True
