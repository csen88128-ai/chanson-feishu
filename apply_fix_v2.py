#!/usr/bin/env python3
"""应用价格获取修复到 run_btc_dag.py"""

file_path = "/Users/chen/Documents/GitHub/chanson-feishu/run_btc_dag.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 使用 repr 来匹配精确的字符串
old_code = '''    print(f"  [1/12] 📡 data_collector: 获取 {symbol} 三周期实时数据...")

    try:
        current_price = fetch_ticker_price(symbol)
        _cache["current_price"] = current_price
    except Exception:
        current_price = 0.0

    kline_summary = {}
    for iv in intervals:
        try:
            df = fetch_klines(symbol, iv, 500)
            _cache["kline_dfs"][iv] = df
            kline_summary[iv] = {
                "count": len(df),
                "start": str(df["date"].iloc[0]) if len(df) > 0 else "N/A",
                "end": str(df["date"].iloc[-1]) if len(df) > 0 else "N/A",
                "latest_close": float(df["close"].iloc[-1]) if len(df) > 0 else 0,
            }
            print(f"         ✅ {iv}: {len(df)} 根 K 线，最新收盘 ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            kline_summary[iv] = {"error": str(e)}
            print(f"         ❌ {iv}: {e}")'''

new_code = '''    print(f"  [1/12] 📡 data_collector: 获取 {symbol} 三周期实时数据...")

    current_price = 0.0
    price_source = "unknown"
    
    # 尝试获取 ticker 价格
    try:
        current_price = fetch_ticker_price(symbol)
        _cache["current_price"] = current_price
        price_source = "ticker"
        print(f"         ✅ Ticker 价格：${current_price:,.2f}")
    except Exception as e:
        print(f"         ⚠️  Ticker 获取失败：{e}，将使用 K 线最新收盘价")

    kline_summary = {}
    for iv in intervals:
        try:
            df = fetch_klines(symbol, iv, 500)
            _cache["kline_dfs"][iv] = df
            kline_summary[iv] = {
                "count": len(df),
                "start": str(df["date"].iloc[0]) if len(df) > 0 else "N/A",
                "end": str(df["date"].iloc[-1]) if len(df) > 0 else "N/A",
                "latest_close": float(df["close"].iloc[-1]) if len(df) > 0 else 0,
            }
            print(f"         ✅ {iv}: {len(df)} 根 K 线，最新收盘 ${df['close'].iloc[-1]:,.2f}")
        except Exception as e:
            kline_summary[iv] = {"error": str(e)}
            print(f"         ❌ {iv}: {e}")
    
    # Fallback: 如果 ticker 失败，使用 1h K 线的最新收盘价
    if current_price == 0.0 and "1h" in _cache["kline_dfs"]:
        df_1h = _cache["kline_dfs"]["1h"]
        if len(df_1h) > 0:
            current_price = float(df_1h["close"].iloc[-1])
            _cache["current_price"] = current_price
            price_source = "1h_kline_close"
            print(f"         ⚠️  使用 1h K 线收盘价作为 fallback: ${current_price:,.2f}")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 修复成功！")
else:
    print("❌ 未找到需要替换的代码段")
    # 尝试查找相似内容
    if "fetch_ticker_price" in content:
        print("✓ fetch_ticker_price 存在于文件中")
    if "data_collector" in content:
        print("✓ data_collector 存在于文件中")
