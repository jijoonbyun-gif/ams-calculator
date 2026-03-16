import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import time

# 페이지 설정
st.set_page_config(page_title="AMS 자산배분 계산기", layout="centered")

st.title("📈 AMS 전략 자산배분")
st.write("과거 12개월 수익률의 추세를 분석하여 최적의 투자 비중을 계산합니다.")

# 사용자 입력
ticker = st.text_input("ETF 티커를 입력하세요 (예: SPY, 360750.KS)", value="SPY").upper()

if st.button("비중 계산하기"):
    with st.spinner('최신 데이터를 불러오는 중...'):
        try:
            # 야후 파이낸스 Ticker 객체 생성
            ticker_obj = yf.Ticker(ticker)
            
            # 서버 차단을 피하기 위한 미세한 대기
            time.sleep(1)
            
            # 일간 데이터를 가져와서 월간으로 변환 (가장 안정적인 방식)
            df = ticker_obj.history(period="2y", interval="1d")
            
            if df.empty:
                st.error(f"'{ticker}' 데이터를 찾을 수 없습니다. 티커 형식을 확인해 주세요.")
            else:
                # 월말 종가 기준으로 데이터 리샘플링
                monthly_prices = df['Close'].resample('ME').last().dropna()
                current_price = monthly_prices.iloc[-1]
                
                # AMS 모멘텀 스코어 계산 로직
                results = []
                score = 0
                
                if len(monthly_prices) < 13:
                    st.warning("분석을 위한 과거 데이터(13개월)가 부족합니다.")
                else:
                    for i in range(1, 13):
                        past_price = monthly_prices.iloc[-(i+1)]
                        is_positive = current_price > past_price
                        return_pct = (current_price - past_price) / past_price
                        
                        if is_positive:
                            score += 1
                        
                        results.append({
                            "비교 기간": f"과거 {i}개월 전",
                            "과거 가격": f"{past_price:,.0f}",
                            "수익률": f"{return_pct:+.2%}",
                            "상태": "▲ 상승" if is_positive else "▼ 하락"
                        })

                    # 비중 계산
                    etf_weight = (score / 12)
                    cash_weight = 1 - etf_weight

                    # 결과 게이지 차트
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = etf_weight * 100,
                        title = {'text': f"{ticker} 권장 비중 (%)"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#1f77b4"}
                        }
                    ))
                    st.plotly_chart(fig)

                    col1, col2 = st.columns(2)
                    col1.metric("모멘텀 스코어", f"{score} / 12")
                    col2.metric("ETF 비중", f"{etf_weight:.1%}")

                    st.subheader("상세 분석 리스트")
                    st.table(pd.DataFrame(results))
                    st.caption(f"데이터 기준일: {monthly_prices.index[-1].date()}")

        except Exception as e:
            # 에러 발생 시 처리
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                st.error("현재 야후 서버 접속이 일시 제한되었습니다. 5분 후 다시 시도해 주세요.")
            else:
                st.error(f"오류가 발생했습니다: {e}")
