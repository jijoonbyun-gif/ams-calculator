import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="AMS 자산배분 계산기", layout="centered")

st.title("📈 AMS 전략 자산배분")
st.write("과거 12개월 수익률을 분석하여 ETF와 현금 비중을 계산합니다.")

# 사용자 입력
ticker = st.text_input("ETF 티커를 입력하세요 (예: SPY, 360750.KS)", value="SPY").upper()

if st.button("비중 계산하기"):
    with st.spinner('데이터를 가져오는 중...'):
        # 1. 데이터 호출 (14개월치)
        data = yf.download(ticker, period="14mo", interval="1mo")
        
        if data.empty:
            st.error("데이터를 불러오지 못했습니다. 티커를 확인해 주세요.")
        else:
            # 종가 데이터 정리
            prices = data['Adj Close'].dropna()
            current_price = prices.iloc[-1]
            
            # 2. 모멘텀 스코어 계산
            results = []
            score = 0
            
            for i in range(1, 13):
                past_price = prices.iloc[-(i+1)]
                return_val = (current_price - past_price) / past_price
                is_positive = current_price > past_price
                
                if is_positive:
                    score += 1
                
                results.append({
                    "기간": f"{i}개월 전 대비",
                    "과거 주가": f"{past_price:,.0f}",
                    "수익률": f"{return_val:.2%}",
                    "결과": "▲ 상승" if is_positive else "▼ 하락"
                })

            # 3. 비중 산출
            etf_weight = (score / 12)
            cash_weight = 1 - etf_weight

            # 결과 표시 (게이지 차트)
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = etf_weight * 100,
                title = {'text': f"{ticker} 투자 비중 (%)"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 50], 'color': "#f0f2f6"},
                        {'range': [50, 100], 'color': "#e1e4e8"}
                    ]
                }
            ))
            st.plotly_chart(fig)

            # 요약 정보
            col1, col2 = st.columns(2)
            col1.metric("ETF 비중", f"{etf_weight:.1%}")
            col2.metric("현금 비중", f"{cash_weight:.1%}")

            st.subheader("상세 분석 데이터")
            df_results = pd.DataFrame(results)
            st.table(df_results)
            
            st.caption(f"기준 가격: {current_price:,.0f} (최근 종가 기준)")
