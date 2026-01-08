"""
測試腳本 - 驗證解析功能（無需外部依賴）
執行：python test_parser.py
"""
import os
import sys
import re
from typing import Dict, Optional, Tuple, List

# 模擬 config 模組的必要設定
class MockConfig:
    DATABASE_PATH = 'test_data.db'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    DEFAULT_CATEGORIES = {
        'expense': ['飲食', '交通', '購物', '娛樂', '醫療', '居住', '其他'],
        'income': ['收入']
    }
    
    KEYWORD_CATEGORY_MAP = {
        '飲食': [
            '早餐', '午餐', '晚餐', '宵夜', '咖啡', '飲料', '便當', '麵', '飯',
            '餐廳', '小吃', '麥當勞', '肯德基', '摩斯', '星巴克', '全家', '7-11',
            '超商', '早午餐', '下午茶', '甜點', '蛋糕', '麵包', '水果', '零食',
            '火鍋', '燒烤', '壽司', '拉麵', '牛排', '披薩', '漢堡', '炸雞',
            '奶茶', '手搖', '飲品', '果汁', '啤酒', '酒', '餐費', '伙食'
        ],
        '交通': [
            '公車', '捷運', 'uber', 'taxi', '計程車', '高鐵', '台鐵', '火車',
            '機票', '油錢', '加油', '停車', '過路費', 'etag', '悠遊卡', '儲值',
            '腳踏車', 'ubike', '客運', '通勤', '車費', '交通費', '機車', '汽車'
        ],
        '購物': [
            '衣服', '鞋子', '包包', '配件', '網購', '淘寶', '蝦皮', 'momo',
            '日用品', '生活用品', '家電', '3c', '手機', '電腦', '書', '文具',
            '化妝品', '保養品', '服飾', '百貨', '超市', '大賣場', '家具'
        ],
        '娛樂': [
            '電影', '遊戲', 'netflix', 'spotify', '音樂', '演唱會', 'ktv',
            '旅遊', '景點', '門票', '展覽', '健身', '運動', '健身房', '瑜珈',
            '按摩', 'spa', '唱歌', '聚會', '派對', '訂閱', '會員'
        ],
        '醫療': [
            '看診', '掛號', '醫院', '診所', '藥', '藥局', '牙醫', '眼科',
            '健檢', '保健', '維他命', '醫療', '醫藥', '手術', '治療', '看醫生'
        ],
        '居住': [
            '房租', '租金', '水電', '電費', '水費', '瓦斯', '網路', '管理費',
            '房貸', '保險', '維修', '裝潢', '傢俱', '清潔', '房屋', '住宿'
        ],
        '收入': [
            '薪水', '薪資', '工資', '獎金', '年終', '紅包', '利息', '股息',
            '兼職', '外快', '退款', '報銷', '投資', '收益', '租金收入', '分紅'
        ]
    }
    
    BUDGET_WARNING_THRESHOLD = 0.8


# 簡化版的解析器（不依賴外部模組）
class SimpleTransactionParser:
    """簡化版交易記錄解析器"""
    
    def __init__(self):
        self.config = MockConfig()
        self.all_expense_categories = self.config.DEFAULT_CATEGORIES['expense']
        self.all_income_categories = self.config.DEFAULT_CATEGORIES['income']
    
    def parse(self, text: str) -> Optional[Dict]:
        text = text.strip()
        result = self._try_parse_patterns(text)
        if result:
            return result
        return None
    
    def _try_parse_patterns(self, text: str) -> Optional[Dict]:
        text = text.replace('$', '').replace('＄', '')
        text = text.replace('NT', '').replace('nt', '')
        text = text.replace('元', ' ').replace('塊', ' ')
        text = text.replace('，', ' ').replace(',', ' ')
        text = ' '.join(text.split())
        
        is_income = self._detect_income(text)
        amount = self._extract_amount(text)
        if amount is None:
            return None
        
        text_without_amount = self._remove_amount_from_text(text, amount)
        category, remaining_text = self._detect_category(text_without_amount, is_income)
        note = self._extract_note(remaining_text)
        
        return {
            'type': 'income' if is_income else 'expense',
            'amount': amount,
            'category': category,
            'note': note
        }
    
    def _detect_income(self, text: str) -> bool:
        income_keywords = [
            '收入', '薪水', '薪資', '工資', '獎金', '年終', '紅包',
            '利息', '股息', '兼職', '外快', '退款', '報銷', '投資收益',
            '租金收入', '分紅', '入帳', '進帳'
        ]
        text_lower = text.lower()
        for keyword in income_keywords:
            if keyword in text_lower:
                return True
        return False
    
    def _extract_amount(self, text: str) -> Optional[float]:
        text_cleaned = re.sub(r'(\d),(\d{3})', r'\1\2', text)
        patterns = [r'(\d+\.?\d*)']
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text_cleaned)
            for match in matches:
                try:
                    amount = float(match)
                    if amount > 0:
                        amounts.append(amount)
                except ValueError:
                    continue
        if amounts:
            return max(amounts)
        return None
    
    def _remove_amount_from_text(self, text: str, amount: float) -> str:
        amount_str = str(int(amount)) if amount == int(amount) else str(amount)
        text = text.replace(amount_str, ' ')
        if amount >= 1000:
            formatted = f"{int(amount):,}"
            text = text.replace(formatted, ' ')
        return ' '.join(text.split())
    
    def _detect_category(self, text: str, is_income: bool) -> Tuple[str, str]:
        text_lower = text.lower()
        matched_category = None
        matched_keyword = None
        
        if is_income:
            matched_category = '收入'
            income_keywords = ['收入', '薪水', '薪資', '工資', '獎金', '年終', 
                             '紅包', '利息', '股息', '兼職', '外快', '退款', 
                             '報銷', '投資收益', '租金收入', '分紅']
            for kw in income_keywords:
                text = text.replace(kw, ' ')
            return matched_category, ' '.join(text.split())
        
        for cat in self.all_expense_categories:
            if cat in text:
                matched_category = cat
                text = text.replace(cat, ' ')
                return matched_category, ' '.join(text.split())
        
        for category, keywords in self.config.KEYWORD_CATEGORY_MAP.items():
            if category == '收入':
                continue
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if matched_keyword is None or len(keyword) > len(matched_keyword):
                        matched_category = category
                        matched_keyword = keyword
        
        if matched_keyword:
            text = re.sub(re.escape(matched_keyword), ' ', text, flags=re.IGNORECASE)
        
        if matched_category is None:
            matched_category = '其他'
        
        return matched_category, ' '.join(text.split())
    
    def _extract_note(self, text: str) -> str:
        note = text.strip()
        noise_words = ['的', '了', '買', '付', '花', '用', '給', '在', '是']
        for word in noise_words:
            if note == word:
                note = ''
                break
        return note


class SimpleCommandParser:
    """簡化版指令解析器"""
    
    COMMANDS = {
        'dashboard': ['儀表板', 'dashboard', '首頁', '總覽'],
        'today': ['今天', '今日', 'today'],
        'week': ['本週', '這週', '這禮拜', 'week'],
        'month': ['本月', '這個月', 'month'],
        'budget': ['預算', 'budget'],
        'set_budget': ['設定預算', '設預算'],
        'reminder': ['提醒', 'reminder', '帳單提醒'],
        'set_reminder': ['設定提醒', '新增提醒', '設提醒'],
        'stats': ['統計', 'stats', 'statistics'],
        'export': ['匯出', 'export', '導出'],
        'clear': ['清空', '清除', 'clear', '刪除全部'],
        'add_category': ['新增類別', '添加類別'],
        'delete_category': ['刪除類別', '移除類別'],
        'categories': ['類別', '類別列表', 'categories'],
        'help': ['幫助', '說明', 'help', '?', '？', '使用說明'],
        'income': ['收入'],
        'delete': ['刪除', '取消', 'delete'],
        'undo': ['復原', '撤銷', 'undo'],
    }
    
    @classmethod
    def parse(cls, text: str) -> Tuple[Optional[str], List[str]]:
        text = text.strip()
        text_lower = text.lower()
        
        for cmd, aliases in cls.COMMANDS.items():
            for alias in aliases:
                alias_lower = alias.lower()
                if text_lower == alias_lower:
                    return cmd, []
                if text_lower.startswith(alias_lower + ' '):
                    params = text[len(alias):].strip()
                    return cmd, params.split() if params else []
                if cmd in ['set_budget', 'set_reminder', 'add_category', 
                          'delete_category', 'stats', 'income', 'delete']:
                    if alias_lower in text_lower:
                        idx = text_lower.find(alias_lower)
                        params = text[idx + len(alias):].strip()
                        return cmd, params.split() if params else []
        
        stats_match = re.match(r'統計\s*(\d{4})[/\-](\d{1,2})', text)
        if stats_match:
            year = stats_match.group(1)
            month = stats_match.group(2)
            return 'stats', [year, month]
        
        budget_match = re.match(r'設定預算\s+(\S+)\s+(\d+)', text)
        if budget_match:
            category = budget_match.group(1)
            amount = budget_match.group(2)
            return 'set_budget', [category, amount]
        
        budget_total_match = re.match(r'設定預算\s+(\d+)', text)
        if budget_total_match:
            amount = budget_total_match.group(1)
            return 'set_budget', ['總預算', amount]
        
        reminder_match = re.match(r'設定提醒\s+(\S+)\s+(\d+)\s+每月(\d{1,2})日?', text)
        if reminder_match:
            name = reminder_match.group(1)
            amount = reminder_match.group(2)
            day = reminder_match.group(3)
            return 'set_reminder', [name, amount, day]
        
        income_match = re.match(r'收入\s+(\d+)\s*(.*)', text)
        if income_match:
            amount = income_match.group(1)
            note = income_match.group(2).strip()
            return 'income', [amount, note] if note else [amount]
        
        delete_match = re.match(r'刪除\s+(\d+)', text)
        if delete_match:
            trans_id = delete_match.group(1)
            return 'delete', [trans_id]
        
        return None, []


def test_transaction_parser():
    """測試交易解析器"""
    print("=" * 50)
    print("測試交易解析器")
    print("=" * 50)
    
    test_cases = [
        ("早餐 50", "飲食", "expense"),
        ("午餐 120 元", "飲食", "expense"),
        ("晚餐 200 麥當勞", "飲食", "expense"),
        ("咖啡 100 星巴克", "飲食", "expense"),
        ("捷運 30", "交通", "expense"),
        ("加油 500", "交通", "expense"),
        ("uber 250", "交通", "expense"),
        ("電影 350", "娛樂", "expense"),
        ("衣服 1000", "購物", "expense"),
        ("房租 10000", "居住", "expense"),
        ("看醫生 500", "醫療", "expense"),
        ("薪水 30000", "收入", "income"),
        ("獎金 5000 年終", "收入", "income"),
        ("紅包 2000", "收入", "income"),
        ("其他 100", "其他", "expense"),
        ("飲食 50", "飲食", "expense"),
        ("交通 100", "交通", "expense"),
    ]
    
    parser = SimpleTransactionParser()
    
    passed = 0
    failed = 0
    
    for text, expected_category, expected_type in test_cases:
        result = parser.parse(text)
        
        if result is None:
            print(f"❌ 解析失敗：{text}")
            failed += 1
            continue
        
        if result['category'] == expected_category and result['type'] == expected_type:
            print(f"✅ {text}")
            print(f"   → 類別：{result['category']}, 金額：{result['amount']}, "
                  f"類型：{result['type']}, 備註：{result.get('note', '')}")
            passed += 1
        else:
            print(f"❌ {text}")
            print(f"   → 預期：{expected_category}/{expected_type}")
            print(f"   → 實際：{result['category']}/{result['type']}")
            failed += 1
    
    print(f"\n測試結果：{passed} 通過, {failed} 失敗")
    return failed == 0


def test_command_parser():
    """測試指令解析器"""
    print("\n" + "=" * 50)
    print("測試指令解析器")
    print("=" * 50)
    
    test_cases = [
        ("儀表板", "dashboard", []),
        ("dashboard", "dashboard", []),
        ("今天", "today", []),
        ("本週", "week", []),
        ("本月", "month", []),
        ("預算", "budget", []),
        ("設定預算 10000", "set_budget", ["總預算", "10000"]),
        ("設定預算 飲食 5000", "set_budget", ["飲食", "5000"]),
        ("提醒", "reminder", []),
        ("類別", "categories", []),
        ("幫助", "help", []),
        ("匯出", "export", []),
        ("清空", "clear", []),
        ("新增類別 旅行", "add_category", ["旅行"]),
        ("刪除類別 旅行", "delete_category", ["旅行"]),
        ("收入 5000 獎金", "income", ["5000", "獎金"]),
        ("統計 2026/01", "stats", ["2026", "01"]),
        ("刪除 123", "delete", ["123"]),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_cmd, expected_params in test_cases:
        cmd, params = SimpleCommandParser.parse(text)
        
        if cmd == expected_cmd:
            print(f"✅ {text}")
            print(f"   → 指令：{cmd}, 參數：{params}")
            passed += 1
        else:
            print(f"❌ {text}")
            print(f"   → 預期：{expected_cmd}")
            print(f"   → 實際：{cmd}")
            failed += 1
    
    print(f"\n測試結果：{passed} 通過, {failed} 失敗")
    return failed == 0


def main():
    """主測試函數"""
    print("LINE 記帳機器人 - 測試腳本（簡化版）")
    print("=" * 50)
    print("此測試不需要安裝任何外部套件")
    print("=" * 50)
    
    results = []
    
    results.append(("交易解析器", test_transaction_parser()))
    results.append(("指令解析器", test_command_parser()))
    
    print("\n" + "=" * 50)
    print("測試總結")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試通過！解析邏輯運作正常！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查")


if __name__ == "__main__":
    main()
