# 🚀 缠论多智能体系统 - 本地运行指南

## 📥 下载项目到本地

### 方法1：使用Git克隆（推荐）
```bash
# 在您的本地电脑上打开终端
git clone https://github.com/csen88128-ai/chanson-feishu.git
cd chanson-feishu
```

### 方法2：直接下载ZIP
1. 访问：https://github.com/csen88128-ai/chanson-feishu
2. 点击 "Code" 按钮
3. 选择 "Download ZIP"
4. 解压到本地目录

---

## 🛠️ 本地环境配置

### 步骤1：安装Python
- 下载Python 3.12：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

### 步骤2：安装依赖
```bash
# Windows
pip install -r requirements.txt

# 或使用uv（推荐，如果已安装）
uv sync
```

### 步骤3：安装requests库
```bash
pip install requests pandas numpy
```

---

## 🚀 运行BTC实时分析

### Windows用户
```bash
# 打开命令提示符或PowerShell
cd chanson-feishu
python analyze_btc_real.py
```

### Mac/Linux用户
```bash
# 打开终端
cd chanson-feishu
python3 analyze_btc_real.py
```

---

## 📊 分析脚本说明

### 1. analyze_btc_real.py（推荐）
**功能**：使用真实Binance API数据

**特点**：
- ✅ 真实实时数据
- ✅ 完整技术指标
- ✅ 缠论结构分析
- ✅ 多空信号判断
- 🌐 需要网络连接

### 2. analyze_btc_simple.py
**功能**：使用模拟数据（演示用）

**特点**：
- ⚡ 速度快
- 📊 完整分析
- ⚠️  模拟数据

### 3. analyze_btc_mock.py
**功能**：带模拟数据的完整分析

---

## 🌐 网络配置

### 如果无法连接Binance API

#### 方法1：使用代理（VPN）
```python
# 在 analyze_btc_real.py 中添加代理设置
import requests

proxies = {
    'http': 'http://127.0.0.1:7890',  # 替换为您的代理端口
    'https': 'http://127.0.0.1:7890',
}

response = requests.get(url, params=params, proxies=proxies, timeout=10)
```

#### 方法2：使用备用API
```python
# 可以尝试其他交易所API
# OKX、Huobi、Coinbase等
```

---

## 📱 使用说明

### 分析结果说明

#### 价格信息
- **当前价格**：最新BTC价格
- **涨跌幅**：相对于前一小时的涨跌
- **最高/最低价**：当前K线的高低点

#### 技术指标
- **MA5/MA20/MA60**：移动平均线
- **RSI**：相对强弱指标（>70超买，<30超卖）
- **MACD**：指数平滑异同移动平均线（金叉看多，死叉看空）

#### 缠论结构
- **顶分型**：短期顶部，可能回调
- **底分型**：短期底部，可能反弹

#### 信号解读
- 🟢 **看多信号**：建议寻找做多机会
- 🔴 **看空信号**：建议谨慎或做空
- 🟡 **观望信号**：等待明确方向

---

## 🔧 常见问题

### Q1：运行时提示"找不到模块"
**解决**：
```bash
pip install -r requirements.txt
```

### Q2：无法连接Binance API
**解决**：
1. 确保VPN已开启
2. 检查代理设置
3. 尝试更换网络

### Q3：Python版本不兼容
**解决**：
- 确保使用Python 3.9+
- 推荐使用Python 3.12

### Q4：数据更新不及时
**解决**：
- Binance API免费版有请求限制
- 可以增加请求间隔
- 考虑使用API密钥（提高限额）

---

## 📞 获取帮助

### 查看文档
- `CHANLUN_README.md` - 系统完整说明
- `BTC_ANALYSIS_GUIDE.md` - BTC分析指南

### 运行测试
```bash
python system_ready_check.py
```

### GitHub仓库
https://github.com/csen88128-ai/chanson-feishu

---

## ⚠️ 免责声明

1. **数据准确性**：系统提供的数据来源于公开API，请以实际交易所数据为准
2. **投资风险**：分析结果仅供参考，不构成投资建议
3. **系统稳定性**：免费API可能有延迟或中断，请做好风险控制
4. **数据来源**：Binance API，数据仅供参考，不保证实时性

---

## 🎯 下一步

### 高级功能
- 尝试完整的12智能体分析
- 使用策略参数优化
- 运行回测系统

### 持续监控
- 设置定时任务，定期运行分析
- 结合交易策略，自动化交易
- 监控多个交易对

---

**项目地址**：https://github.com/csen88128-ai/chanson-feishu.git
**系统版本**：v7.0
**更新时间**：2026-04-16

🎉 **在本地运行，享受真实的BTC实时行情分析！**
