# 📱 本地获取BTC最新数据 - 超简单指南

## 只需要3步！

---

## 第1步：下载脚本

### 方式A：从GitHub下载
1. 访问：https://github.com/csen88128-ai/chanson-feishu
2. 进入 `scripts` 目录
3. 下载这两个文件：
   - `get_btc_ultra_simple.py`
   - `获取BTC数据_超简单版.bat`

### 方式B：从聊天中复制
如果您看到这两个文件，直接下载即可。

---

## 第2步：双击运行

### Windows用户
1. 双击：`获取BTC数据_超简单版.bat`
2. 等待几秒钟
3. 看到"✅ 数据获取成功！"

### Mac/Linux用户
打开终端，进入脚本目录，运行：
```bash
python get_btc_ultra_simple.py
```

---

## 第3步：上传数据

### 方式A：上传文件（推荐）
1. 找到生成的文件：`btc_latest_data.json`
2. 点击聊天框的附件按钮
3. 上传这个文件
4. 发送给AI助手

### 方式B：复制数据
1. 打开文件：`btc_latest_data.json`
2. 复制所有内容
3. 粘贴到聊天中发送

---

## 🎯 运行后的结果

脚本会生成两个文件：

### 1. btc_latest_data.json（用于上传）
```json
{
  "source": "CoinGecko",
  "price": 73608.08,
  "change_24h": -0.23,
  "timestamp": "2026-04-16 23:52:34"
}
```

### 2. btc_latest_data.txt（方便查看）
```
数据来源: CoinGecko
当前价格: $73,608.08
获取时间: 2026-04-16 23:52:34
24h涨跌: -0.23%
```

---

## ⚠️ 常见问题

### Q1: 双击没有反应？
**A**: 检查：
1. Python是否已安装
2. 右键 → 打开方式 → 选择Python

### Q2: 提示"未安装requests"？
**A**: 安装requests库：
```bash
pip install requests
```

### Q3: 所有交易所都连接失败？
**A**: 检查：
1. 网络连接是否正常
2. 是否需要VPN（可能需要）
3. 防火墙是否阻止了连接

### Q4: 不会上传文件？
**A**:
1. 点击聊天框的"📎"或"上传"按钮
2. 选择 `btc_latest_data.json` 文件
3. 点击发送

---

## 💡 技术细节

### 脚本会做什么
1. 自动尝试连接3个交易所：
   - CoinGecko
   - Binance
   - OKX
2. 获取BTC当前价格
3. 保存到JSON和TXT文件

### 脚本会自动选择
- 如果CoinGecko失败 → 自动尝试Binance
- 如果Binance失败 → 自动尝试OKX
- 无需手动切换

### 数据质量
- ✅ 数据来源：交易所官方API
- ✅ 数据准确性：高
- ✅ 数据时效性：实时（几秒钟内）

---

## 📋 完整流程示例

### 您的操作
```
1. 下载脚本到电脑
2. 双击运行
3. 看到"✅ 数据获取成功！"
4. 上传btc_latest_data.json文件
```

### AI助手的操作
```
1. 读取您上传的文件
2. 运行多智能体协作分析
3. 生成专业分析报告
4. 发送给您
```

---

## 🚀 开始吧！

### 第1步：下载脚本
从GitHub下载这两个文件：
- `get_btc_ultra_simple.py`
- `获取BTC数据_超简单版.bat`

### 第2步：双击运行
双击 `获取BTC数据_超简单版.bat`

### 第3步：上传数据
上传 `btc_latest_data.json` 文件

**就这么简单！** 😊

---

## 📞 需要帮助？

如果遇到任何问题：
1. 检查Python是否安装：`python --version`
2. 安装依赖：`pip install requests`
3. 尝试在命令行运行：`python get_btc_ultra_simple.py`
4. 查看错误信息并反馈

---

**准备好了吗？现在就可以开始！** 🎯

**记住：只需要3步 - 下载 → 双击运行 → 上传文件** 🚀
