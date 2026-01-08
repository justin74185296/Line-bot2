"""
LINE 記帳機器人配置檔案
"""
import os

# 嘗試載入環境變數（可選）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv 不是必須的


class Config:
    """應用配置類"""
    
    # LINE Bot 配置
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
    LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
    
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    
    # 伺服器配置
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # 資料儲存路徑
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # 預設類別配置
    DEFAULT_EXPENSE_CATEGORIES = [
        '飲食', '交通', '購物', '娛樂', '醫療', '居住', '教育', '通訊', '其他'
    ]
    
    DEFAULT_INCOME_CATEGORIES = [
        '薪水', '獎金', '投資', '兼職', '禮金', '其他收入'
    ]
    
    # 智能分類關鍵字映射
    CATEGORY_KEYWORDS = {
        '飲食': [
            '早餐', '午餐', '晚餐', '宵夜', '飲料', '咖啡', '茶', '奶茶',
            '便當', '麵', '飯', '麥當勞', '肯德基', '摩斯', '星巴克',
            '食物', '吃', '餐', '零食', '點心', '水果', '蔬菜', '肉',
            '超商', '便利商店', '全家', '7-11', '萊爾富', 'OK',
            '外送', 'uber', 'foodpanda', '熊貓'
        ],
        '交通': [
            '交通', '捷運', '公車', '計程車', 'taxi', 'uber', '高鐵', '台鐵',
            '火車', '客運', '油錢', '加油', '停車', '停車費', 'youbike',
            '機車', '汽車', '車', '悠遊卡', '儲值', 'gogoro'
        ],
        '購物': [
            '購物', '買', '衣服', '褲子', '鞋', '包', '配件', '飾品',
            '日用品', '生活用品', '電器', '3C', '手機', '電腦', '網購',
            '蝦皮', 'pchome', 'momo', '淘寶', '亞馬遜'
        ],
        '娛樂': [
            '娛樂', '電影', '演唱會', '遊戲', 'KTV', '唱歌', '酒吧', '夜店',
            '旅遊', '旅行', '出遊', '門票', '景點', '訂閱', 'Netflix',
            'Spotify', 'YouTube', '健身', '運動', '書', '雜誌'
        ],
        '醫療': [
            '醫療', '看病', '醫院', '診所', '藥', '藥局', '掛號', '健康',
            '牙醫', '眼科', '皮膚', '感冒', '保健', '維他命'
        ],
        '居住': [
            '居住', '房租', '租金', '水費', '電費', '瓦斯', '網路', '管理費',
            '房貸', '修繕', '傢俱', '家具', '裝潢', '清潔'
        ],
        '教育': [
            '教育', '學費', '補習', '課程', '書籍', '文具', '考試', '證照',
            '進修', '線上課程'
        ],
        '通訊': [
            '通訊', '電話', '手機費', '網路費', '電信'
        ]
    }
    
    # 收入關鍵字
    INCOME_KEYWORDS = [
        '薪水', '薪資', '工資', '收入', '獎金', '年終', '分紅', '佣金',
        '利息', '投資', '股息', '租金收入', '兼職', '打工', '禮金', '紅包',
        '退款', '報銷', '返現'
    ]
    
    # 預算警告閾值
    BUDGET_WARNING_THRESHOLD = 0.8  # 80%
    BUDGET_DANGER_THRESHOLD = 1.0   # 100%


# 表情符號配置
class Emoji:
    """表情符號常數"""
    MONEY = '💰'
    CHART = '📊'
    CALENDAR = '📅'
    BELL = '🔔'
    CHECK = '✅'
    CROSS = '❌'
    WARNING = '⚠️'
    STAR = '⭐'
    FIRE = '🔥'
    GRAPH_UP = '📈'
    GRAPH_DOWN = '📉'
    WALLET = '👛'
    BANK = '🏦'
    RECEIPT = '🧾'
    FOOD = '🍽️'
    CAR = '🚗'
    SHOPPING = '🛒'
    GAME = '🎮'
    HOSPITAL = '🏥'
    HOME = '🏠'
    BOOK = '📚'
    PHONE = '📱'
    QUESTION = '❓'
    INFO = 'ℹ️'
    SPARKLE = '✨'
    PIGGY = '🐷'
    TROPHY = '🏆'
    TARGET = '🎯'
    CLOCK = '⏰'


# 類別對應的表情符號
CATEGORY_EMOJI = {
    '飲食': '🍽️',
    '交通': '🚗',
    '購物': '🛒',
    '娛樂': '🎮',
    '醫療': '🏥',
    '居住': '🏠',
    '教育': '📚',
    '通訊': '📱',
    '其他': '📦',
    '薪水': '💼',
    '獎金': '🎁',
    '投資': '📈',
    '兼職': '💪',
    '禮金': '🧧',
    '其他收入': '💵'
}
