import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="AMS 자산배분 계산기", layout="centered")

st.title("📈 AMS 전략 자산배분")
st.write("과거 12개월 수익률의 추세를 분석하여 최적의 투자 비중을 계산합니다.")

# 사용자 입력
ticker = st.text_input("ETF 티커를 입력하세요 (예: SPY, 360750.KS)", value="SPY").upper()

if st.button("비중 계산하기"):
    with st.spinner('최신 데이터를 불러오는 중...'):
        try:
            # 1. 데이터 호출 (더 안정적인 Ticker 객체 활용)
            # 일간 데이터를 가져와서 월간으로 리샘플링하는 것이 오류가 훨씬 적습니다.
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period="2y", interval="1d")
            
            if df.empty:
                st.error(f"'{ticker}' 데이터를 찾을 수 없습니다. 티커 형식을 확인해 주세요. (미국은 티커만, 한국은 뒤에 .KS)")
            else:
                # 2. 데이터 가공: 월말 종가 기준으로 변환
                # 'ME'는 Month End를 의미합니다.
                monthly_prices = df['Close'].resample('ME').last().dropna()
                current_price = monthly_prices.iloc[-1]
                
                # 3. AMS 모멘텀 스코어 계산
                results = []
                score = 0
                
                # 최소 13개월치의 월간 데이터가 있어야 12개월 비교가 가능합니다.
                if len(monthly_prices) < 13:
                    st.warning("데이터 기간이 충분하지 않습니다. 상장한 지 1년이 넘은 종목인지 확인해 주세요.")
                else:
                    for i in range(1, 13):
                        past_price = monthly_prices.iloc[-(i+1)]
                        is_positive = current_price > past_price
                        return_pct = (current_price - past_price) / past_price
                        
                        if is_positive:
                            score += 1
                        
                        results.append({
                            "비교 기간": f"과거 {i}개월 전",
                            "과거 주가": f"{past_price:,.0f}",
                            "수익률": f"{return_pct:+.2%}",
                            "상태": "▲ 상승" if is_positive else "▼ 하락"
                        })

                    # 4. 결과 출력
                    etf_weight = (score / 12)
                    cash_weight = 1 - etf_weight

                    # 게이지 차트
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = etf_weight * 100,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': f"{ticker} 권장 투자 비중 (%)"},
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

                    # 지표 표시
                    col1, col2, col3 = st.columns(3)
                    col1.metric("모멘텀 스코어", f"{score} / 12")
                    col2.metric("ETF 비중", f"{etf_weight:.1%}")
                    col3.metric("현금 비중", f"{cash_weight:.1%}")

                    st.subheader("세부 분석 데이터")
                    st.table(pd.DataFrame(results))
                    st.caption(f"최근 데이터 기준일: {monthly_prices.index[-1].strftime('%Y-%m-%d')}")
                    st.caption(f"현재 주가 기준: {current_price:,.0f}")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.info("Tip: yfinance 라이브러리 버전 문제일 수 있습니다. requirements.txt를 확인해 주세요.")
