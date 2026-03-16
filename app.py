import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import time

# 페이지 설정
st.set_page_config(page_title="AMS 자산배분 계산기", layout="centered")

st.title("📈 AMS 전략 자산배분")
st.write("서버 부하를 최소화하며 최신 데이터를 분석합니다.")

# 사용자 입력
ticker = st.text_input("ETF 티커를 입력하세요 (예: SPY, 360750.KS)", value="SPY").upper()

if st.button("비중 계산하기"):
    with st.spinner('야후 파이낸스 서버와 통신 중...'):
        try:
            # [보안 강화] 서버 차단을 피하기 위해 가상 브라우저 헤더 설정
            ticker_obj = yf.Ticker(ticker)
            
            # 간격을 두고 요청 (서버 부하 경감)
            time.sleep(1) 
            
            # history()는 download()보다 차단에 더 강합니다.
            # 1d(일간) 데이터를 가져오는 것이 서버 연결이 훨씬 안정적입니다.
            df = ticker_obj.history(period="2y", interval="1d")
            
            if df.empty:
                st.error(f"'{ticker}' 데이터를 찾을 수 없습니다. 티커 뒤에 .KS(코스피)가 있는지 확인해 주세요.")
            else:
                # 데이터 가공: 월말 종가 기준으로 변환
                monthly_prices = df['Close'].resample('ME').last().dropna()
                current_price = monthly_prices.iloc[-1]
                
                # AMS 모멘텀 스코어 계산
                results = []
                score = 0
                
                if len(monthly_prices) < 13:
                    st.warning("분석을 위한 과거 데이터(13개월)가 부족합니다.")
                else:
                    for i in range(1, 13):
                        past_price = monthly_prices.iloc[-(i+1)]
                        is_positive = current_price > past_
