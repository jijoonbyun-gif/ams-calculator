import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import time

# 페이지 설정
st.set_page_config(page_title="AMS 자산배분 계산기", layout="centered")

st.title("📈 AMS 전략 자산배분")
st.write("최근 영업일 종가를 기준으로 정확한 투자 비중을 계산합니다.")

# 사용자 입력
ticker = st.text_input("ETF 티커를 입력하세요 (예: SPY, 360750.KS)", value="SPY").upper()

if st.button("비중 계산하기"):
    with st.spinner('데이터를 분석 중입니다...'):
        try:
            ticker_obj = yf.Ticker(ticker)
            time.sleep(1) # 서버 차단 방지
            
            # 일간 데이터 가져오기
            df = ticker_obj.history(period="2y", interval="1d")
            
            if df.empty:
                st.error(f"'{ticker}' 데이터를 찾을 수 없습니다.")
            else:
                # [핵심 수정] 실제 데이터가 있는 가장 마지막 날짜를 별도 저장
                # 오늘이 3월 17일이면 정확히 2026-03-17을 가져옵니다.
                real_last_date = df.index[-1].strftime('%Y-%m-%d')
                
                # 내부 계산을 위한 월간 변환
                monthly_prices = df['Close'].resample('ME').last().dropna()
                current_price = monthly_prices.iloc[-1]
                
                results = []
                score = 0
                
                if len(monthly_prices) < 13:
                    st.warning("데이터 기간이 부족합니다.")
                else:
                    for i in range(1, 13):
                        past_price = monthly_prices.iloc[-(i+1)]
                        is_positive = current_price > past_price
                        return_pct = (current_price - past_price) / past_price
                        if is_positive: score += 1
                        
                        results.append({
                            "비교 기간": f"{i}개월 전",
                            "과거 가격": f"{past_price:,.0f}",
                            "수익률": f"{return_pct:+.2%}",
                            "상태": "▲ 상승" if is_positive else "▼ 하락"
                        })

                    etf_weight = (score / 12)
                    
                    # 게이지 차트
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = etf_weight * 100,
                        title = {'text': f"{ticker} 권장 비중 (%)"},
                        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#1f77b4"}}
                    ))
                    st.plotly_chart(fig)

                    col1, col2 = st.columns(2)
                    col1.metric("모멘텀 스코어", f"{score} / 12")
                    col2.metric("ETF 비중", f"{etf_weight:.1%}")

                    st.subheader("상세 분석 리스트")
                    st.table(pd.DataFrame(results))
                    
                    # [출력 수정] 3월 31일 대신 실제 데이터 날짜를 명시
                    st.success(f"✅ 분석 기준일: {real_last_date} (오늘 종가 기준)")
                    st.caption(f"시스템상 월간 그룹화 라벨링을 배제하고 실제 데이터 날짜를 표시합니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")
