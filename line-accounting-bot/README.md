# LINE 記帳機器人 💰

一個專業的 LINE 記帳機器人，使用 Python Flask 和 line-bot-sdk 開發，對標專業記帳 App（如 Money Manager EX、Wallet、Toshl、AndroMoney、Moze）的核心功能。

## ✨ 功能特色

### 📝 智能記帳
- **自然語言輸入**：直接輸入「早餐 50」、「午餐 120 便當」即可記帳
- **智能類別識別**：自動識別消費類別（飲食、交通、購物等）
- **收入/支出區分**：輸入「薪水 30000 收入」記錄收入

### 📊 統計報表
- **儀表板**：個人財務總覽，一目了然
- **時間維度**：今日、本週、本月統計
- **類別分析**：支出分類統計與佔比
- **現金流預測**：預測本月剩餘支出

### 🎯 預算管理
- **總預算設定**：設定每月總預算
- **類別預算**：為特定類別設定預算
- **超支警告**：預算使用 80% 時自動提醒

### 🔔 提醒功能
- **帳單提醒**：設定每月固定帳單提醒
- **預算警告**：自動推播預算超支通知

### 📤 資料管理
- **CSV 匯出**：匯出交易記錄
- **類別自訂**：新增/刪除自訂類別
- **資料清空**：二次確認的安全清空機制

## 🚀 快速開始

### 1. 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Messaging API Channel
3. 取得 **Channel Access Token** 和 **Channel Secret**

### 2. 部署到 Replit

1. 在 Replit 建立新專案，選擇 Python
2. 上傳所有專案檔案
3. 前往 **Secrets** 設定環境變數：
   - `LINE_CHANNEL_ACCESS_TOKEN`: 你的 Channel Access Token
   - `LINE_CHANNEL_SECRET`: 你的 Channel Secret
4. 點擊 **Run** 啟動機器人

### 3. 設定 Webhook

1. 在 LINE Developers Console 中，設定 Webhook URL
2. URL 格式：`https://your-replit-url.repl.co/callback`
3. 開啟 **Use webhook**

## 📖 使用說明

### 記帳方式

```
早餐 50              → 自動歸類為「飲食」
午餐 120 便當        → 飲食，備註「便當」
交通 $80             → 自動歸類為「交通」
薪水 30000 收入      → 記錄為收入
```

### 指令列表

| 指令 | 說明 |
|------|------|
| `儀表板` | 顯示個人財務總覽 |
| `今天` | 今日收支明細 |
| `本週` | 本週統計 |
| `本月` | 本月統計報表 |
| `統計 2024/01` | 指定月份統計 |
| `預算` | 查看預算設定 |
| `設定預算 10000` | 設定總預算 |
| `設定預算 飲食 3000` | 設定類別預算 |
| `提醒` | 查看提醒設定 |
| `設定提醒 房租 10000 每月25日` | 設定帳單提醒 |
| `類別` | 查看所有類別 |
| `新增類別 旅行` | 新增自訂類別 |
| `匯出` | 匯出本月 CSV |
| `清空` | 清除所有資料 |
| `幫助` | 顯示使用說明 |

## 🏗️ 專案結構

```
line-accounting-bot/
├── main.py              # 主程式入口
├── config.py            # 配置設定
├── requirements.txt     # 套件依賴
├── .replit              # Replit 配置
├── .env.example         # 環境變數範例
├── README.md            # 說明文件
├── data/                # 資料儲存目錄
├── models/              # 資料模型
│   ├── __init__.py
│   ├── transaction.py   # 交易記錄
│   ├── budget.py        # 預算設定
│   ├── reminder.py      # 提醒設定
│   └── user_data.py     # 用戶資料
├── services/            # 服務層
│   ├── __init__.py
│   ├── storage.py       # 資料儲存
│   ├── parser.py        # 訊息解析
│   ├── statistics.py    # 統計服務
│   └── reminder.py      # 提醒服務
├── handlers/            # 處理器
│   ├── __init__.py
│   ├── message_handler.py   # 訊息處理
│   └── command_handler.py   # 指令處理
└── utils/               # 工具函數
    ├── __init__.py
    ├── helpers.py       # 輔助函數
    └── validators.py    # 驗證函數
```

## ⚙️ 技術規格

- **後端框架**：Flask
- **LINE SDK**：line-bot-sdk v3
- **資料儲存**：JSON 文件（支援 Replit 環境）
- **定時任務**：Threading（提醒推播）

## 🔧 環境變數

| 變數名稱 | 說明 | 必填 |
|---------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | ✅ |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | ✅ |
| `PORT` | 伺服器端口（預設 5000） | ❌ |
| `FLASK_ENV` | 環境模式（development/production） | ❌ |

## 📱 預設類別

### 支出類別
- 🍽️ 飲食
- 🚗 交通
- 🛒 購物
- 🎮 娛樂
- 🏥 醫療
- 🏠 居住
- 📚 教育
- 📱 通訊
- 📦 其他

### 收入類別
- 💼 薪水
- 🎁 獎金
- 📈 投資
- 💪 兼職
- 🧧 禮金
- 💵 其他收入

## 🛡️ 資料安全

- 每位用戶資料獨立儲存，以 LINE user_id 為主鍵
- 敏感操作（如清空資料）需二次確認
- 資料儲存於本地，不上傳第三方服務

## 📝 更新日誌

### v1.0.0
- 初始版本
- 智能記帳解析
- 完整統計報表
- 預算管理功能
- 帳單提醒功能
- 類別自訂功能

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

---

Made with ❤️ for better personal finance management
