#!/usr/bin/env python3
"""直接修改 run_btc_dag.py 的 178-200 行"""

file_path = "/Users/chen/Documents/GitHub/chanson-feishu/run_btc_dag.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 打印要修改的行
print("修改前的 178-185 行:")
for i in range(177, min(186, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

# 替换 178-184 行（索引 177-183）
new_lines = '''    print(f"  [1/12] 📡 data_collector: 获取 {symbol} 三周期实时数据...")

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
'''

# 替换行
lines[177:184] = [new_lines]

# 在 for 循环后添加 fallback 代码（找到 200 行附近）
for i in range(195, 205):
    if i < len(lines) and 'print(f"         ❌ {iv}: {e}")' in lines[i]:
        # 在这行之后插入 fallback 代码
        fallback_code = '''
    # Fallback: 如果 ticker 失败，使用 1h K 线的最新收盘价
    if current_price == 0.0 and "1h" in _cache["kline_dfs"]:
        df_1h = _cache["kline_dfs"]["1h"]
        if len(df_1h) > 0:
            current_price = float(df_1h["close"].iloc[-1])
            _cache["current_price"] = current_price
            price_source = "1h_kline_close"
            print(f"         ⚠️  使用 1h K 线收盘价作为 fallback: ${current_price:,.2f}")
'''
        lines.insert(i+1, fallback_code)
        print(f"\n✅ 在{i+1}行后插入 fallback 代码")
        break

# 保存文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ 文件修改完成！")

# 验证修改
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("\n修改后的 177-195 行:")
for i in range(176, min(200, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
