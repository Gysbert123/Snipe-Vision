"""
Technical Analysis Indicators Module
Comprehensive indicator calculations using pandas-ta
"""
import pandas as pd
import pandas_ta as ta

def calculate_all_indicators(df):
    """Calculate all technical indicators for a dataframe"""
    indicators = {}
    
    try:
        # Trend Indicators
        indicators['SMA_20'] = ta.sma(df.Close, length=20)
        indicators['SMA_50'] = ta.sma(df.Close, length=50)
        indicators['SMA_200'] = ta.sma(df.Close, length=200)
        indicators['EMA_9'] = ta.ema(df.Close, length=9)
        indicators['EMA_12'] = ta.ema(df.Close, length=12)
        indicators['EMA_26'] = ta.ema(df.Close, length=26)
        indicators['EMA_50'] = ta.ema(df.Close, length=50)
        indicators['EMA_200'] = ta.ema(df.Close, length=200)
        
        # MACD
        macd = ta.macd(df.Close)
        if macd is not None and isinstance(macd, pd.DataFrame):
            indicators['MACD'] = macd.iloc[:, 0] if len(macd.columns) > 0 else None
            indicators['MACD_Signal'] = macd.iloc[:, 1] if len(macd.columns) > 1 else None
            indicators['MACD_Hist'] = macd.iloc[:, 2] if len(macd.columns) > 2 else None
        
        # ADX
        adx = ta.adx(df.High, df.Low, df.Close)
        if adx is not None and isinstance(adx, pd.DataFrame):
            indicators['ADX'] = adx.iloc[:, 0] if len(adx.columns) > 0 else None
        
        # Parabolic SAR
        indicators['PSAR'] = ta.psar(df.High, df.Low)
        
        # Aroon
        aroon = ta.aroon(df.High, df.Low)
        if aroon is not None and isinstance(aroon, pd.DataFrame):
            indicators['Aroon_Up'] = aroon.iloc[:, 0] if len(aroon.columns) > 0 else None
            indicators['Aroon_Down'] = aroon.iloc[:, 1] if len(aroon.columns) > 1 else None
        
        # SuperTrend
        supertrend = ta.supertrend(df.High, df.Low, df.Close)
        if supertrend is not None and isinstance(supertrend, pd.DataFrame):
            indicators['SuperTrend'] = supertrend.iloc[:, 0] if len(supertrend.columns) > 0 else None
        
        # Momentum Indicators
        indicators['RSI'] = ta.rsi(df.Close, length=14)
        stoch = ta.stoch(df.High, df.Low, df.Close)
        if stoch is not None and isinstance(stoch, pd.DataFrame):
            indicators['Stoch_K'] = stoch.iloc[:, 0] if len(stoch.columns) > 0 else None
            indicators['Stoch_D'] = stoch.iloc[:, 1] if len(stoch.columns) > 1 else None
        indicators['CCI'] = ta.cci(df.High, df.Low, df.Close)
        indicators['Williams_R'] = ta.willr(df.High, df.Low, df.Close)
        indicators['ROC'] = ta.roc(df.Close)
        indicators['MFI'] = ta.mfi(df.High, df.Low, df.Close, df.Volume)
        
        # Volatility Indicators
        bb = ta.bbands(df.Close, length=20)
        if bb is not None and isinstance(bb, pd.DataFrame):
            indicators['BB_Upper'] = bb.iloc[:, 0] if len(bb.columns) > 0 else None
            indicators['BB_Middle'] = bb.iloc[:, 1] if len(bb.columns) > 1 else None
            indicators['BB_Lower'] = bb.iloc[:, 2] if len(bb.columns) > 2 else None
        indicators['ATR'] = ta.atr(df.High, df.Low, df.Close)
        indicators['STD'] = df.Close.rolling(20).std()
        
        # Volume Indicators
        indicators['OBV'] = ta.obv(df.Close, df.Volume)
        indicators['VWAP'] = ta.vwap(df.High, df.Low, df.Close, df.Volume)
        indicators['CMF'] = ta.cmf(df.High, df.Low, df.Close, df.Volume)
        volume_ma = df.Volume.rolling(20).mean()
        indicators['Volume_MA'] = volume_ma
        indicators['Volume_Ratio'] = df.Volume / volume_ma if volume_ma.iloc[-1] > 0 else 0
        
        # Additional Moving Averages
        indicators['Hull_MA'] = ta.hma(df.Close)
        indicators['TEMA'] = ta.tema(df.Close)
        indicators['KAMA'] = ta.kama(df.Close)
        indicators['VWMA'] = ta.vwma(df.Close, df.Volume)
        
        # Ichimoku (simplified)
        ichimoku = ta.ichimoku(df.High, df.Low, df.Close)
        if ichimoku is not None:
            if isinstance(ichimoku, tuple) and len(ichimoku) > 0:
                ichi_df = ichimoku[0] if isinstance(ichimoku[0], pd.DataFrame) else None
                if ichi_df is not None:
                    indicators['Ichimoku_Base'] = ichi_df.iloc[:, 0] if len(ichi_df.columns) > 0 else None
                    indicators['Ichimoku_Conversion'] = ichi_df.iloc[:, 1] if len(ichi_df.columns) > 1 else None
        
        # Donchian Channels
        indicators['Donchian_High'] = df.High.rolling(20).max()
        indicators['Donchian_Low'] = df.Low.rolling(20).min()
        indicators['Donchian_Mid'] = (indicators['Donchian_High'] + indicators['Donchian_Low']) / 2
        
    except Exception as e:
        pass
    
    return indicators

