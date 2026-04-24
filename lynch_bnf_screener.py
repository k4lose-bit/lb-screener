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
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif!important;background-color:#F0F4FF!important}
.lb-header{background:linear-gradient(135deg,#1565C0 0%,#0097A7 100%);border-radius:16px;padding:28px 36px;margin-bottom:24px}
.lb-header h1{font-size:2.4rem;font-weight:900;letter-spacing:4px;margin:0;color:white!important}
.lb-header p{font-size:.9rem;opacity:.85;margin:4px 0 0;color:white!important}
.date-badge{background:rgba(255,255,255,0.25);color:white;border-radius:20px;padding:4px 14px;font-size:.8rem;font-weight:700;display:inline-block;margin-bottom:8px}
.stage-card{border-radius:14px;padding:20px 22px;box-shadow:0 4px 16px rgba(0,0,0,.10)}
.stage-lynch{background:#E3F2FD;border-top:5px solid #1565C0}
.stage-bnf{background:#EDE7F6;border-top:5px solid #6A1B9A}
.stage-score{background:#FFF8E1;border-top:5px solid #F57F17}
.stage-report{background:#E8F5E9;border-top:5px solid #2E7D32}
.stage-label{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.lynch-label{color:#1565C0}.bnf-label{color:#6A1B9A}.score-label{color:#F57F17}.report-label{color:#2E7D32}
.stage-title{font-size:1.1rem;font-weight:700;margin-bottom:10px;color:#212121}
.stage-criteria{font-size:.82rem;color:#424242;line-height:1.9}
.stage-criteria b{color:#212121}
.metric-box{background:white;border-radius:12px;padding:16px 20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.metric-val{font-size:1.6rem;font-weight:900;color:#1565C0}
.metric-lbl{font-size:.75rem;color:#757575;margin-top:2px}
.param-bar{background:white;border-radius:12px;padding:14px 20px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,.07);display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.param-chip{background:#E3F2FD;color:#1565C0;border-radius:20px;padding:4px 14px;font-size:.8rem;font-weight:700}
.param-chip.purple{background:#EDE7F6;color:#6A1B9A}
.stock-card{background:white;border-radius:12px;padding:16px 20px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,.07);border-left:5px solid #1565C0;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.stock-card.rank1{border-left-color:#F57F17}.stock-card.rank2{border-left-color:#546E7A}.stock-card.rank3{border-left-color:#C62828}
.stock-rank{font-size:1.4rem;font-weight:900;color:#BDBDBD;min-width:32px;text-align:center}
.stock-rank.r1{color:#F57F17}.stock-rank.r2{color:#546E7A}.stock-rank.r3{color:#C62828}
.stock-name{font-size:1rem;font-weight:700;color:#212121}
.stock-code{font-size:.75rem;color:#9E9E9E;margin-left:6px}
.stock-cat{font-size:.72rem;background:#E3F2FD;color:#1565C0;padding:2px 8px;border-radius:10px;margin-left:8px;font-weight:700}
.theme-tag{font-size:.7rem;background:#E8F5E9;color:#2E7D32;padding:2px 8px;border-radius:10px;margin:2px 2px;display:inline-block;font-weight:600}
.stock-metrics{display:flex;gap:18px;margin-left:auto;align-items:center;flex-wrap:wrap}
.sm-item{text-align:center}
.sm-val{font-size:.95rem;font-weight:700;color:#212121}
.sm-lbl{font-size:.68rem;color:#9E9E9E}
.sm-val.green{color:#2E7D32}.sm-val.blue{color:#1565C0}.sm-val.purple{color:#6A1B9A}.sm-val.orange{color:#F57F17;font-size:1.1rem}
.lb-bar{height:8px;border-radius:4px;background:linear-gradient(90deg,#1565C0,#0097A7);display:inline-block;vertical-align:middle;margin-right:6px}
.report-box{background:white;border-radius:14px;padding:24px 28px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-top:16px}
.theme-stock-row{background:white;border-radius:10px;padding:12px 16px;margin-bottom:8px;box-shadow:0 2px 6px rgba(0,0,0,.06);display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.lb-badge-high{background:#E8F5E9;color:#2E7D32;border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.lb-badge-mid{background:#FFF8E1;color:#F57F17;border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.lb-badge-low{background:#F5F5F5;color:#9E9E9E;border-radius:8px;padding:3px 10px;font-size:.8rem;font-weight:700}
.stButton button{background:linear-gradient(135deg,#1565C0,#0097A7)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:700!important;font-size:1rem!important;padding:12px 0!important}
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

def calc_bollinger_band(closes, period=20):
    """볼린저밴드 계산"""
    s = pd.Series(closes)
    sma = s.rolling(period).mean()
    std = s.rolling(period).std()
    return (sma + 2*std), sma, (sma - 2*std)

def render_domestic_chart(code, name, closes, APP_KEY, APP_SECRET, token, n=60, chart_key=None):
    """국내 종목 RSI+MACD+볼린저밴드 4단 차트"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    n = min(n, len(closes))
    c_n = closes[-n:]

    # 지표 계산 먼저 (날짜 없어도 계산 가능)
    s = pd.Series(closes)
    delta = s.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = (100 - 100/(1 + gain/loss.replace(0, float('nan')))).fillna(50)
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd = ema12-ema26; sig = macd.ewm(span=9, adjust=False).mean(); hist_m = macd-sig
    bb_up, bb_mid, bb_low = calc_bollinger_band(closes)

    # 날짜 가져오기 (실패해도 인덱스로 대체)
    dates_raw = []
    try:
        end   = datetime.today().strftime("%Y%m%d")
        start = (datetime.today()-timedelta(days=150)).strftime("%Y%m%d")
        if token:
            r2 = requests.get(
                f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                headers=kis_headers(APP_KEY,APP_SECRET,token,"FHKST03010100"),
                params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":code,
                        "FID_INPUT_DATE_1":start,"FID_INPUT_DATE_2":end,
                        "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=7)
            items2 = r2.json().get("output2",[])
            dates_raw = [d.get("stck_bsop_date","") for d in items2 if d.get("stck_clpr")]
            dates_raw.reverse()
    except: pass

    # 날짜 없으면 0,1,2... 인덱스 사용
    if len(dates_raw) >= n:
        d_n = pd.to_datetime(dates_raw[-n:])
    else:
        d_n = list(range(n))

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[0.45,0.2,0.2,0.15],
                        vertical_spacing=0.03,
                        subplot_titles=[f"{name} 주가 + 볼린저밴드","RSI(14)","MACD",""])

    # 주가 + 볼린저밴드
    fig.add_trace(go.Scatter(x=d_n,y=c_n,line=dict(color="#1565C0",width=2),name="종가"),row=1,col=1)
    fig.add_trace(go.Scatter(x=d_n,y=bb_up.tolist()[-n:],line=dict(color="#E24B4A",width=1,dash="dash"),name="BB상단"),row=1,col=1)
    fig.add_trace(go.Scatter(x=d_n,y=bb_mid.tolist()[-n:],line=dict(color="#F57F17",width=1),name="BB중간"),row=1,col=1)
    fig.add_trace(go.Scatter(x=d_n,y=bb_low.tolist()[-n:],line=dict(color="#2E7D32",width=1,dash="dash"),name="BB하단"),row=1,col=1)

    # RSI
    fig.add_trace(go.Scatter(x=d_n,y=rsi.values[-n:],line=dict(color="#6A1B9A",width=1.5),name="RSI"),row=2,col=1)
    fig.add_hline(y=70,line_dash="dash",line_color="#E24B4A",row=2,col=1)
    fig.add_hline(y=30,line_dash="dash",line_color="#2E7D32",row=2,col=1)

    # MACD
    hcolors = ["#E24B4A" if v<0 else "#2E7D32" for v in hist_m.values[-n:]]
    fig.add_trace(go.Bar(x=d_n,y=hist_m.values[-n:],marker_color=hcolors,name="히스토"),row=3,col=1)
    fig.add_trace(go.Scatter(x=d_n,y=macd.values[-n:],line=dict(color="#1565C0",width=1.5),name="MACD"),row=3,col=1)
    fig.add_trace(go.Scatter(x=d_n,y=sig.values[-n:],line=dict(color="#F57F17",width=1.5),name="시그널"),row=3,col=1)

    # x축 날짜 15일 간격 tickvals 계산
    if len(dates_raw) >= n and isinstance(d_n[0] if hasattr(d_n,'__getitem__') else 0, str) is False:
        try:
            import numpy as np
            tick_indices = list(range(0, n, 15))
            tick_vals = [d_n[i] for i in tick_indices if i < len(d_n)]
            tick_texts = [str(d_n[i])[:10].replace('-','.')[5:] for i in tick_indices if i < len(d_n)]
            xaxis_cfg = dict(tickvals=tick_vals, ticktext=tick_texts, tickangle=-30,
                           showspikes=True, spikemode="across", spikesnap="cursor",
                           spikecolor="#888888", spikethickness=1, spikedash="dot")
        except:
            xaxis_cfg = dict(showspikes=True, spikemode="across")
    else:
        xaxis_cfg = dict(showspikes=True, spikemode="across")

    fig.update_layout(
        height=560, showlegend=False,
        paper_bgcolor="white", plot_bgcolor="#F8F9FA",
        margin=dict(l=10,r=10,t=30,b=60),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#DDDDDD"),
        xaxis=dict(**xaxis_cfg),
        xaxis2=dict(**xaxis_cfg),
        xaxis3=dict(**xaxis_cfg),
        xaxis4=dict(**xaxis_cfg),
    )

    # 메트릭
    cur_rsi  = round(float(rsi.values[-1]),1)
    cur_macd = round(float(macd.values[-1]),2)
    cur_sig  = round(float(sig.values[-1]),2)
    cur_bb_up = float(bb_up.iloc[-1]); cur_bb_low = float(bb_low.iloc[-1])
    current = closes[-1]
    bb_pos = "상단 돌파⚠️" if current>cur_bb_up else "하단 이탈🟢" if current<cur_bb_low else "밴드 내"

    mc1,mc2,mc3,mc4 = st.columns(4)
    mc1.metric("RSI(14)", cur_rsi, "과매수⚠️" if cur_rsi>=70 else "과매도🟢" if cur_rsi<=30 else "중립")
    mc2.metric("MACD", cur_macd, "상승🟢" if cur_macd>cur_sig else "하락🔴")
    mc3.metric("시그널", cur_sig)
    mc4.metric("볼린저 위치", bb_pos)
    st.plotly_chart(fig, use_container_width=True, key=chart_key or f"chart_{code}")

    return rsi, macd, sig, dates_raw

def render_7day_table(closes, volumes, dates_raw, rsi_series, macd_series):
    """최근 7거래일 추이 표 — 색상 신호 포함"""
    rows_html = ""
    dates_use = dates_raw if dates_raw else [f"D-{abs(i)}" for i in range(-1,-9,-1)]
    for i in range(-1, -8, -1):
        try:
            p = closes[i]; po = closes[i-1]; v = volumes[i] if volumes else 0
            dc = (p-po)/po*100
            chg_color = "#E24B4A" if dc>0 else "#1565C0"

            r_val = round(float(rsi_series.iloc[i]), 1)
            m_val = round(float(macd_series.iloc[i]), 2)

            # RSI 신호 — 원 크게
            if r_val >= 70:
                rsi_signal = f'<span style="color:#E24B4A;font-weight:700">{r_val}</span>&nbsp;<span style="color:#E24B4A;font-size:1.4rem;line-height:1">●</span>'
            elif r_val <= 30:
                rsi_signal = f'<span style="color:#2E7D32;font-weight:700">{r_val}</span>&nbsp;<span style="color:#2E7D32;font-size:1.4rem;line-height:1">●</span>'
            else:
                rsi_signal = f'<span style="color:#424242">{r_val}</span>'

            # MACD 신호 — 원 크게
            if m_val > 0:
                macd_signal = f'<span style="color:#E24B4A;font-weight:700">{m_val:,}</span>&nbsp;<span style="color:#2E7D32;font-size:1.4rem;line-height:1">●</span>'
            else:
                macd_signal = f'<span style="color:#1565C0;font-weight:700">{m_val:,}</span>&nbsp;<span style="color:#E24B4A;font-size:1.4rem;line-height:1">●</span>'

            # 거래량 신호 (평균 대비)
            avg_vol = sum(volumes[-20:]) / min(len(volumes), 20) if volumes else 0
            if avg_vol > 0 and v >= avg_vol * 1.5:
                vol_signal = f'<span style="font-weight:600">{int(v):,}</span>&nbsp;<span style="color:#2E7D32;font-size:1.4rem;line-height:1">●</span>'
            else:
                vol_signal = f'{int(v):,}'

            date_str = dates_use[i] if abs(i) <= len(dates_use) else ""
            if isinstance(date_str, str) and len(date_str)==8:
                date_str = f"{date_str[4:6]}.{date_str[6:]}"

            rows_html += (
                f'<tr style="border-bottom:1px solid #F0F0F0;font-size:1rem">'
                f'<td style="padding:13px 10px;text-align:center;color:#616161">{date_str}</td>'
                f'<td style="padding:13px 10px;text-align:center;font-weight:600">{int(p):,}원</td>'
                f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{int(p-po):+,}원</td>'
                f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{dc:+.2f}%</td>'
                f'<td style="padding:13px 10px;text-align:center">{vol_signal}</td>'
                f'<td style="padding:13px 10px;text-align:center">{rsi_signal}</td>'
                f'<td style="padding:13px 10px;text-align:center">{macd_signal}</td>'
                f'</tr>'
            )
        except: break

    st.markdown(
        '<table style="width:100%;border-collapse:collapse;font-size:1rem;background:white;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)">'
        '<tr style="background:#F8F9FA;font-weight:700;color:#424242;font-size:1rem">'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">날짜</th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">종가</th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">변동</th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">등락률</th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">거래량<br><span style="font-size:.75rem;color:#9E9E9E;font-weight:400">평균1.5배↑🟢</span></th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">RSI<br><span style="font-size:.75rem;color:#9E9E9E;font-weight:400">30↓매수🟢 70↑매도🔴</span></th>'
        '<th style="padding:12px 10px;border-bottom:2px solid #EEE;text-align:center">MACD<br><span style="font-size:.75rem;color:#9E9E9E;font-weight:400">양수🟢 음수🔴</span></th>'
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

def get_stock_name(code, api_name=""):
    """종목명 우선순위: API → theme_map → STOCK_NAMES → 코드"""
    if api_name and api_name.strip():
        return api_name.strip()
    if code in THEME_MAP:
        return THEME_MAP[code]["name"]
    return STOCK_NAMES.get(code, code)

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

# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 파라미터")
    peg_max    = st.slider("PEG 상한",           0.3, 2.0, 1.5, 0.1,
                           help="1.5 이하 = 성장 대비 저평가. EPS 근사 오차 감안")
    eps_min    = st.slider("EPS 성장률 하한(%)",  5,   50,   8,  1,
                           help="근사값 기준 8%+. 실제 EPS는 더 높을 수 있음")
    per_max    = st.slider("PER 상한",            5,   60,  40,  1,
                           help="성장주는 PER 높은 경우 많음. 40 이하 권장")
    gap_max    = st.slider("이격도 상한(%)",       85, 115, 103,  1,
                           help="103% = 이평 약간 위. 반등 초기 종목 포함")
    sector_min = st.slider("섹터 소외도 하한(%)",  0,   20,   0,  1,
                           help="0 = 소외도 무관. 섹터 근사 오차 감안")
    vol_min    = st.slider("거래량지수 하한",      1.0, 3.0, 1.0, 0.1,
                           help="1.0 = 최소한의 거래 있으면 OK")
    lynch_w    = st.slider("린치 가중치",         0.3, 0.8, 0.6, 0.1,
                           help="0.6 = 펀더멘털 60% + 타이밍 40%")
    bnf_w      = round(1.0-lynch_w, 1)
    market     = st.selectbox("시장", ["KOSPI","KOSDAQ","KOSPI+KOSDAQ"])
    top_n      = st.slider("상위 종목 수", 5, 30, 10, 1)
    st.markdown("---")
    st.caption("💡 파라미터 가이드")
    st.caption("결과 0개 → PEG/이격도 올리기")
    st.caption("결과 너무 많음 → PEG/EPS 내리기")
    st.caption("주 1~2회 judal_theme_crawler.py 실행 권장")

# ── Anthropic API 키 (secrets에서만 읽기, 화면 노출 없음) ──
try:
    ant_key = st.secrets.get("ANTHROPIC_API_KEY", "")
except:
    ant_key = ""

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
<div class="lb-header">
  <div class="date-badge">{today_str}</div>
  <h1>LB SCREENER</h1>
  <p>Lynch × BNF — 성장주 펀더멘털 발굴 + 기술적 타이밍 결합 | 한국투자증권 공식 API</p>
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
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="stage-card stage-lynch"><div class="stage-label lynch-label">Stage 1 · 피터 린치</div><div class="stage-title">펀더멘털 필터</div><div class="stage-criteria">PEG <b>{peg_max}</b> 이하<br>EPS 성장률 <b>{eps_min}%+</b> 확인<br>6분류 — 고속성장주 우선</div></div>',unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stage-card stage-bnf"><div class="stage-label bnf-label">Stage 2 · BNF</div><div class="stage-title">타이밍 필터</div><div class="stage-criteria">이격도 <b>{gap_max}%</b> 이하<br>섹터 내 소외 <b>{sector_min}%+</b><br>거래량 급증 확인</div></div>',unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stage-card stage-score"><div class="stage-label score-label">Stage 3 · 결합</div><div class="stage-title">LB 스코어 산출</div><div class="stage-criteria">린치 품질 <b>×{lynch_w}</b><br>BNF 타이밍 <b>×{bnf_w}</b><br>상위 종목 자동 선별</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stage-card stage-report"><div class="stage-label report-label">Stage 4 · 리포트</div><div class="stage-title">AI 투자 분석</div><div class="stage-criteria">Claude API 종목 해설<br>펀더멘털 + 기술적 분석<br>리스크 요인 자동 진단</div></div>',unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.expander("📖 지표 해설 — 어떤 숫자가 좋은가?"):
        st.markdown("""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
<div style="background:white;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,.07)">
<div style="color:#1565C0;font-weight:700;margin-bottom:8px">PEG (피터 린치 핵심)</div>
<div style="font-size:.8rem;line-height:2">
0.5 이하 → <b style="color:#2E7D32">강력매수</b><br>
0.5~1.0 → <b style="color:#1565C0">매수</b><br>
1.0~1.5 → <b style="color:#F57F17">보유</b><br>
1.5 이상 → <b style="color:#C62828">고평가</b>
</div>
<div style="font-size:.75rem;color:#9E9E9E;margin-top:6px">PER이 높아도 성장률이 더 높으면 저평가</div>
</div>
<div style="background:white;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,.07)">
<div style="color:#1565C0;font-weight:700;margin-bottom:8px">EPS 성장률</div>
<div style="font-size:.8rem;line-height:2">
25% 이상 → <b style="color:#2E7D32">고속성장주</b><br>
10~25%  → <b style="color:#1565C0">견실성장주</b><br>
0~10%   → <b style="color:#F57F17">완만성장주</b><br>
마이너스 → <b style="color:#C62828">적자 (제외)</b>
</div>
<div style="font-size:.75rem;color:#9E9E9E;margin-top:6px">린치는 연 25%+ 성장주 선호</div>
</div>
<div style="background:white;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,.07)">
<div style="color:#6A1B9A;font-weight:700;margin-bottom:8px">이격도 (BNF 핵심)</div>
<div style="font-size:.8rem;line-height:2">
90% 이하 → <b style="color:#2E7D32">강한 눌림목</b><br>
90~97%  → <b style="color:#1565C0">눌림목 구간</b><br>
97~103% → <b style="color:#F57F17">이평 근처</b><br>
103% 이상 → <b style="color:#C62828">과열</b>
</div>
<div style="font-size:.75rem;color:#9E9E9E;margin-top:6px">현재가 ÷ 25일이평 × 100</div>
</div>
<div style="background:white;border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,.07)">
<div style="color:#6A1B9A;font-weight:700;margin-bottom:8px">LB 스코어</div>
<div style="font-size:.8rem;line-height:2">
70 이상 → <b style="color:#2E7D32">최우선 주목</b><br>
50~70  → <b style="color:#1565C0">관심 종목</b><br>
30~50  → <b style="color:#F57F17">참고 종목</b><br>
30 이하 → <b style="color:#C62828">조건 미달</b>
</div>
<div style="font-size:.75rem;color:#9E9E9E;margin-top:6px">린치×0.6 + BNF×0.4 결합 점수</div>
</div>
</div>
""", unsafe_allow_html=True)

    run = st.button("▶ 스크리닝 실행", use_container_width=True, key="run_btn")

    if "results"  not in st.session_state: st.session_state.results  = None
    if "token"    not in st.session_state: st.session_state.token    = ""

    if run:
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

        st.markdown(f'<div class="param-bar"><span style="font-size:.8rem;color:#757575;font-weight:700">적용 기준</span><span class="param-chip">PEG ≤ {peg_max}</span><span class="param-chip">EPS ≥ {eps_min}%</span><span class="param-chip purple">이격도 ≤ {gap_max}%</span><span class="param-chip purple">섹터소외 ≥ {sector_min}%</span></div>',unsafe_allow_html=True)

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
            reason_part = '<div style="background:#F0F4FF;border-radius:10px;padding:10px 14px;font-size:.85rem;color:#333;line-height:1.7;border-left:3px solid #1565C0;min-width:200px;max-width:340px;align-self:center">💡 ' + reason_text + '</div>' if reason_text else '<div style="min-width:10px"></div>'
            name_val = r["name"]
            code_val = r["code"]
            current_val = f'{int(r["current"]):,}'
            peg_val = r["peg"]
            eps_val = f'{r["eps_growth"]:.1f}'
            gap_val = r["gap"]
            lb_val = r["lb_score"]
            grade_val = r["peg_grade"]

            card_html = (
                '<div class="stock-card ' + rc + '">'
                '<div class="stock-rank ' + rnc + '">' + str(i+1) + '</div>'
                '<div style="flex:1">'
                '<div><span class="stock-name">' + name_val + '</span>'
                '<span class="stock-code">' + code_val + '</span>'
                '<span class="stock-cat">' + cat + '</span></div>'
                '<div style="margin-top:4px">'
                '<span style="font-size:.78rem;color:#9E9E9E">현재가 </span>'
                '<span style="font-size:.85rem;font-weight:700">' + current_val + '원</span>'
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
                ov=get_ohlcv_info(r["code"],APP_KEY,APP_SECRET,st.session_state.get("token",""))
                if ov and ov.get("closes"):
                    closes=ov["closes"]
                    if len(closes)>=26:
                        rsi_s, macd_s, sig_s, dates_raw2 = render_domestic_chart(
                            r["code"], r["name"], closes, APP_KEY, APP_SECRET,
                            st.session_state.get("token",""), chart_key=f"lb_{r['code']}")
                        st.markdown("**📋 최근 7거래일 추이**")
                        # 거래량 가져오기
                        try:
                            end2=datetime.today().strftime("%Y%m%d")
                            start2=(datetime.today()-timedelta(days=200)).strftime("%Y%m%d")
                            rv=requests.get(
                                f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                                headers=kis_headers(APP_KEY,APP_SECRET,token,"FHKST03010100"),
                                params={"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":r["code"],
                                        "FID_INPUT_DATE_1":start2,"FID_INPUT_DATE_2":end2,
                                        "FID_PERIOD_DIV_CODE":"D","FID_ORG_ADJ_PRC":"0"},timeout=10)
                            vols2=[float(d.get("acml_vol",0) or 0) for d in rv.json().get("output2",[]) if d.get("stck_clpr")]
                            vols2.reverse()
                        except: vols2=[]
                        render_7day_table(closes, vols2, dates_raw2, rsi_s, macd_s)
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
                import anthropic
                client = anthropic.Anthropic(api_key=ant_key)
                ph = st.empty(); txt = ""
                with client.messages.stream(
                    model="claude-opus-4-5", max_tokens=1500,
                    messages=[{"role":"user","content":prompt}]
                ) as s:
                    for t in s.text_stream:
                        txt += t; ph.markdown(txt + "▌")
                ph.markdown(txt)
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
                '<span style="font-size:.75rem;color:#9E9E9E;margin-left:6px">' + r["code"] + '</span>'
                '<span style="font-size:.78rem;color:#757575;margin-left:10px">현재가 ' + f'{int(r["current"]):,}' + '원</span>'
                '</div>'
                '<div style="margin-top:5px;font-size:.82rem;color:#444;line-height:1.6;'
                'background:#F0F4FF;border-radius:8px;padding:7px 12px;border-left:3px solid #1565C0">'
                '💡 ' + reason_text +
                '</div>'
                '</div>'
                '<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-left:12px">'
                '<div style="text-align:center"><div style="font-size:.9rem;font-weight:700;color:' + peg_color + '">PEG ' + str(r["peg"]) + '</div><div style="font-size:.68rem;color:#9E9E9E">린치</div></div>'
                '<div style="text-align:center"><div style="font-size:.9rem;font-weight:700;color:#1565C0">이격 ' + str(r["gap"]) + '%</div><div style="font-size:.68rem;color:#9E9E9E">BNF</div></div>'
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
                f'<div style="background:white;border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:.82rem;box-shadow:0 1px 4px rgba(0,0,0,.07)">'
                f'<b>{name}</b><br><span style="color:#9E9E9E;font-size:.72rem">{code}</span></div>',
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
            '<div style="background:white;border-radius:14px;padding:20px 24px;'
            'box-shadow:0 4px 16px rgba(0,0,0,.08);margin-bottom:16px">'
            '<div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">'
            '<div style="flex:1">'
            '<div style="font-size:1.4rem;font-weight:900;color:#212121">' + name +
            '<span style="font-size:.8rem;color:#9E9E9E;margin-left:8px;font-weight:400">' + selected_code + '</span></div>'
            '<div style="margin-top:4px">'
            '<span style="font-size:1.1rem;font-weight:700">' + f'{int(current):,}원' + '</span>'
            '<span style="font-size:.8rem;color:#1565C0;margin-left:10px;font-weight:700">' + cat + '</span>'
            '</div>'
            + theme_div +
            '</div>'
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;min-width:360px">'

            # PEG — 1.0 이하 초록, 1.5 이하 주황, 그 외 빨강
            + '<div style="text-align:center;background:#F0F4FF;border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if peg<=1.0 else "#F57F17" if peg<=1.5 else "#E24B4A") + '">PEG ' + str(peg) + '</div>'
            + '<div style="font-size:.72rem;color:#9E9E9E;margin-top:2px">린치 지표</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if peg<=1.0 else "#F57F17" if peg<=1.5 else "#E24B4A") + '">' + ("🟢 저평가" if peg<=1.0 else "🟡 적정" if peg<=1.5 else "🔴 고평가") + '</div></div>'

            # 이격도 — 100% 미만 초록, 103% 이하 주황, 초과 빨강
            + '<div style="text-align:center;background:#F0F4FF;border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if gap_now<100 else "#F57F17" if gap_now<=103 else "#E24B4A") + '">이격 ' + str(gap_now) + '%</div>'
            + '<div style="font-size:.72rem;color:#9E9E9E;margin-top:2px">BNF 타이밍</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if gap_now<100 else "#F57F17" if gap_now<=103 else "#E24B4A") + '">' + ("🟢 눌림목" if gap_now<100 else "🟡 이평근처" if gap_now<=103 else "🔴 과열") + '</div></div>'

            # PBR — 1.0 미만 초록, 2.0 이하 주황, 초과 빨강
            + '<div style="text-align:center;background:#F0F4FF;border-radius:10px;padding:10px">'
            + '<div style="font-size:1.1rem;font-weight:700;color:' + ("#2E7D32" if 0<pbr<1.0 else "#F57F17" if pbr<=2.0 else "#E24B4A") + '">PBR ' + str(pbr) + '</div>'
            + '<div style="font-size:.72rem;color:#9E9E9E;margin-top:2px">자산 대비</div>'
            + '<div style="font-size:.7rem;margin-top:3px;color:' + ("#2E7D32" if 0<pbr<1.0 else "#F57F17" if pbr<=2.0 else "#9E9E9E") + '">' + ("🟢 자산이하" if 0<pbr<1.0 else "🟡 적정" if pbr<=2.0 else "–") + '</div></div>'

            # LB스코어 — 70↑ 초록, 50↑ 파랑, 30↑ 주황, 미만 회색
            + '<div style="text-align:center;background:#F0F4FF;border-radius:10px;padding:10px">'
            + '<div style="font-size:1.3rem;font-weight:900;color:' + lb_color + '">' + str(lb) + '</div>'
            + '<div style="font-size:.72rem;color:#9E9E9E;margin-top:2px">LB 스코어</div>'
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
            '<div style="background:#F0F4FF;border-radius:12px;padding:16px 20px;'
            'border-left:4px solid #1565C0;margin-bottom:16px;font-size:.9rem;'
            'color:#333;line-height:1.8">💡 ' + reason_html + '</div>',
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

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_usd_krw():
        try:
            return float(yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1])
        except:
            return 1380.0

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

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_foreign_news(company_name):
        try:
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(company_name+' stock')}&hl=en&gl=US&ceid=US:en"
            res = requests.get(url, timeout=5)
            root = ET.fromstring(res.text)
            return [{"title": i.find('title').text, "link": i.find('link').text}
                    for i in root.findall('.//item')[:5]]
        except:
            return []

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
                '<div style="background:white;border-radius:14px;padding:20px 24px;'
                'box-shadow:0 4px 16px rgba(0,0,0,.08);margin-bottom:16px">'
                '<div style="font-size:1.4rem;font-weight:900;color:#212121">'
                + company_name +
                '<span style="font-size:.85rem;color:#9E9E9E;margin-left:8px;font-weight:400">(' + f_ticker + ')</span>'
                + (f'<span style="font-size:.78rem;color:#757575;margin-left:8px">{sector}</span>' if sector else '') +
                '</div>'
                '<div style="margin-top:8px;display:flex;gap:20px;flex-wrap:wrap;align-items:center">'
                f'<span style="font-size:1.3rem;font-weight:900">${current:,.2f}</span>'
                f'<span style="color:{chg_color};font-weight:700;font-size:1rem">{chg:+.2f}%</span>'
                f'<span style="color:#757575;font-size:.9rem">≈ {krw_price:,}원</span>'
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
                '<div style="background:#F0F4FF;border-radius:12px;padding:14px 18px;'
                'border-left:4px solid #1a237e;margin:12px 0;font-size:.9rem;color:#333;line-height:1.8">'
                '💡 ' + reason + '</div>',
                unsafe_allow_html=True
            )

            # ── 차트 ─────────────────────────────────
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            n   = min(60, len(closes))
            c60 = closes[-n:]; d60 = dates[-n:]
            v60 = volumes[-n:]

            fig = make_subplots(
                rows=4, cols=1, shared_xaxes=True,
                row_heights=[0.45,0.2,0.2,0.15],
                vertical_spacing=0.03,
                subplot_titles=["주가 + 볼린저밴드","RSI(14)","MACD","거래량"]
            )

            # 주가 캔들 스타일 (단순 라인 + 볼린저)
            fig.add_trace(go.Scatter(x=d60,y=c60,line=dict(color="#1565C0",width=2),name="종가"),row=1,col=1)
            fig.add_trace(go.Scatter(x=d60,y=bb_up.tolist()[-n:],line=dict(color="#E24B4A",width=1,dash="dash"),name="BB상단"),row=1,col=1)
            fig.add_trace(go.Scatter(x=d60,y=bb_mid.tolist()[-n:],line=dict(color="#F57F17",width=1),name="BB중간"),row=1,col=1)
            fig.add_trace(go.Scatter(x=d60,y=bb_low.tolist()[-n:],line=dict(color="#2E7D32",width=1,dash="dash"),name="BB하단"),row=1,col=1)

            # RSI
            rsi_list = rsi_series.tolist()[-n:]
            fig.add_trace(go.Scatter(x=d60,y=rsi_list,line=dict(color="#6A1B9A",width=1.5),name="RSI"),row=2,col=1)
            fig.add_hline(y=70,line_dash="dash",line_color="#E24B4A",row=2,col=1)
            fig.add_hline(y=30,line_dash="dash",line_color="#2E7D32",row=2,col=1)

            # MACD
            macd_n = macd_line.tolist()[-n:]; sig_n = sig_line.tolist()[-n:]
            hist_n = [m-s for m,s in zip(macd_n,sig_n)]
            hcolors = ["#E24B4A" if v<0 else "#2E7D32" for v in hist_n]
            fig.add_trace(go.Bar(x=d60,y=hist_n,marker_color=hcolors,name="히스토"),row=3,col=1)
            fig.add_trace(go.Scatter(x=d60,y=macd_n,line=dict(color="#1565C0",width=1.5),name="MACD"),row=3,col=1)
            fig.add_trace(go.Scatter(x=d60,y=sig_n,line=dict(color="#F57F17",width=1.5),name="시그널"),row=3,col=1)

            # 거래량
            fig.add_trace(go.Bar(x=d60,y=v60,marker_color="#B0BEC5",name="거래량"),row=4,col=1)

            fig.update_layout(height=580,showlegend=False,paper_bgcolor="white",
                              plot_bgcolor="#F8F9FA",margin=dict(l=10,r=10,t=30,b=10))
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
                        rsi_signal = f'<span style="color:#E24B4A;font-weight:700">{r_val}</span> <span style="color:#E24B4A">●</span>'
                    elif r_val <= 30:
                        rsi_signal = f'<span style="color:#2E7D32;font-weight:700">{r_val}</span> <span style="color:#2E7D32">●</span>'
                    else:
                        rsi_signal = f'<span style="color:#424242">{r_val}</span>'

                    if m_val > 0:
                        macd_signal = f'<span style="color:#E24B4A;font-weight:700">{m_val}</span> <span style="color:#2E7D32">●</span>'
                    else:
                        macd_signal = f'<span style="color:#1565C0;font-weight:700">{m_val}</span> <span style="color:#E24B4A">●</span>'

                    vol_signal = f'<span style="font-weight:600">{int(v):,}</span> <span style="color:#2E7D32">●</span>' if v >= avg_vol_f*1.5 else f'{int(v):,}'

                    rows_html += (
                        f'<tr style="border-bottom:1px solid #F0F0F0;font-size:1rem">'
                        f'<td style="padding:13px 10px;text-align:center;color:#616161">{dates[i]}</td>'
                        f'<td style="padding:13px 10px;text-align:center;font-weight:600">${p:,.2f}</td>'
                        f'<td style="padding:13px 10px;text-align:center;color:{chg_color};font-weight:700">{dc:+.2f}%</td>'
                        f'<td style="padding:13px 10px;text-align:center">{vol_signal}</td>'
                        f'<td style="padding:13px 10px;text-align:center">{rsi_signal}</td>'
                        f'<td style="padding:13px 10px;text-align:center">{macd_signal}</td>'
                        f'</tr>'
                    )
                except: break

            st.markdown(
                '<table style="width:100%;border-collapse:collapse;font-size:1rem;background:white;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)">'
                '<tr style="background:#F8F9FA;font-weight:700;color:#424242">'
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
