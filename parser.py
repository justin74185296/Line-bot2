"""
LINE 記帳機器人 - 智能解析模組
負責解析用戶輸入的記帳文字
"""
import re
from typing import Dict, Optional, Tuple, List
import config
import database


class TransactionParser:
    """交易記錄解析器"""
    
    def __init__(self, user_id: str):
        """
        初始化解析器
        
        Args:
            user_id: 用戶 ID，用於取得自訂類別
        """
        self.user_id = user_id
        self.categories = database.get_all_categories(user_id)
        self.all_expense_categories = self.categories['expense']
        self.all_income_categories = self.categories['income']
    
    def parse(self, text: str) -> Optional[Dict]:
        """
        解析用戶輸入的文字
        
        Args:
            text: 用戶輸入的原始文字
        
        Returns:
            解析結果字典，包含：
            - type: 'income' 或 'expense'
            - amount: 金額
            - category: 類別
            - note: 備註
            
            如果無法解析，返回 None
        """
        text = text.strip()
        
        # 嘗試多種解析模式
        result = self._try_parse_patterns(text)
        
        if result:
            return result
        
        return None
    
    def _try_parse_patterns(self, text: str) -> Optional[Dict]:
        """嘗試各種解析模式"""
        
        # 移除常見的貨幣符號和單位
        text = text.replace('$', '').replace('＄', '')
        text = text.replace('NT', '').replace('nt', '')
        text = text.replace('元', ' ').replace('塊', ' ')
        text = text.replace('，', ' ').replace(',', ' ')
        
        # 標準化空格
        text = ' '.join(text.split())
        
        # 檢測是否為收入
        is_income = self._detect_income(text)
        
        # 提取金額
        amount = self._extract_amount(text)
        if amount is None:
            return None
        
        # 移除金額後的文字用於分析類別和備註
        text_without_amount = self._remove_amount_from_text(text, amount)
        
        # 檢測類別
        category, remaining_text = self._detect_category(text_without_amount, is_income)
        
        # 剩餘文字作為備註
        note = self._extract_note(remaining_text)
        
        return {
            'type': 'income' if is_income else 'expense',
            'amount': amount,
            'category': category,
            'note': note
        }
    
    def _detect_income(self, text: str) -> bool:
        """檢測是否為收入"""
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
        """
        從文字中提取金額
        
        支援格式：
        - 純數字：50, 100, 1000
        - 帶小數：50.5, 100.00
        - 帶千分位：1,000, 10,000
        """
        # 先處理帶千分位的數字
        text_cleaned = re.sub(r'(\d),(\d{3})', r'\1\2', text)
        
        # 匹配數字（包含小數）
        patterns = [
            r'(\d+\.?\d*)',  # 基本數字模式
        ]
        
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
            # 返回最合理的金額（通常是最大的那個）
            return max(amounts)
        
        return None
    
    def _remove_amount_from_text(self, text: str, amount: float) -> str:
        """從文字中移除金額部分"""
        # 移除各種金額表示方式
        amount_str = str(int(amount)) if amount == int(amount) else str(amount)
        text = text.replace(amount_str, ' ')
        
        # 移除帶千分位的表示
        if amount >= 1000:
            formatted = f"{int(amount):,}"
            text = text.replace(formatted, ' ')
        
        return ' '.join(text.split())
    
    def _detect_category(self, text: str, is_income: bool) -> Tuple[str, str]:
        """
        檢測類別
        
        Args:
            text: 移除金額後的文字
            is_income: 是否為收入
        
        Returns:
            (類別, 剩餘文字)
        """
        text_lower = text.lower()
        matched_category = None
        matched_keyword = None
        
        # 如果是收入，優先使用收入類別
        if is_income:
            matched_category = '收入'
            # 移除收入相關關鍵字
            income_keywords = ['收入', '薪水', '薪資', '工資', '獎金', '年終', 
                             '紅包', '利息', '股息', '兼職', '外快', '退款', 
                             '報銷', '投資收益', '租金收入', '分紅']
            for kw in income_keywords:
                text = text.replace(kw, ' ')
            return matched_category, ' '.join(text.split())
        
        # 檢查用戶是否直接指定了類別名稱
        for cat in self.all_expense_categories:
            if cat in text:
                matched_category = cat
                text = text.replace(cat, ' ')
                return matched_category, ' '.join(text.split())
        
        # 使用關鍵字映射進行智能分類
        for category, keywords in config.KEYWORD_CATEGORY_MAP.items():
            if category == '收入':
                continue  # 收入已經在上面處理
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if matched_keyword is None or len(keyword) > len(matched_keyword):
                        matched_category = category
                        matched_keyword = keyword
        
        # 如果找到匹配的關鍵字，移除它
        if matched_keyword:
            # 使用正則表達式不區分大小寫地移除
            text = re.sub(re.escape(matched_keyword), ' ', text, flags=re.IGNORECASE)
        
        # 如果沒有找到類別，使用「其他」
        if matched_category is None:
            matched_category = '其他'
        
        return matched_category, ' '.join(text.split())
    
    def _extract_note(self, text: str) -> str:
        """提取備註"""
        # 清理文字
        note = text.strip()
        
        # 移除一些無意義的詞
        noise_words = ['的', '了', '買', '付', '花', '用', '給', '在', '是']
        for word in noise_words:
            if note == word:
                note = ''
                break
        
        return note


class CommandParser:
    """指令解析器"""
    
    # 支援的指令及其別名
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
        """
        解析指令
        
        Args:
            text: 用戶輸入的文字
        
        Returns:
            (指令名稱, 參數列表)
            如果不是指令，返回 (None, [])
        """
        text = text.strip()
        text_lower = text.lower()
        parts = text.split()
        
        # 檢查是否匹配任何指令
        for cmd, aliases in cls.COMMANDS.items():
            for alias in aliases:
                alias_lower = alias.lower()
                
                # 完全匹配
                if text_lower == alias_lower:
                    return cmd, []
                
                # 前綴匹配（指令 + 參數）
                if text_lower.startswith(alias_lower + ' '):
                    params = text[len(alias):].strip()
                    return cmd, params.split() if params else []
                
                # 對於某些指令，檢查是否包含關鍵字
                if cmd in ['set_budget', 'set_reminder', 'add_category', 
                          'delete_category', 'stats', 'income', 'delete']:
                    if alias_lower in text_lower:
                        # 提取參數
                        idx = text_lower.find(alias_lower)
                        params = text[idx + len(alias):].strip()
                        return cmd, params.split() if params else []
        
        # 特殊處理：統計 YYYY/MM 格式
        stats_match = re.match(r'統計\s*(\d{4})[/\-](\d{1,2})', text)
        if stats_match:
            year = stats_match.group(1)
            month = stats_match.group(2)
            return 'stats', [year, month]
        
        # 特殊處理：設定預算 類別 金額
        budget_match = re.match(r'設定預算\s+(\S+)\s+(\d+)', text)
        if budget_match:
            category = budget_match.group(1)
            amount = budget_match.group(2)
            return 'set_budget', [category, amount]
        
        # 特殊處理：設定預算 金額（總預算）
        budget_total_match = re.match(r'設定預算\s+(\d+)', text)
        if budget_total_match:
            amount = budget_total_match.group(1)
            return 'set_budget', ['總預算', amount]
        
        # 特殊處理：設定提醒 名稱 金額 每月X日
        reminder_match = re.match(
            r'設定提醒\s+(\S+)\s+(\d+)\s+每月(\d{1,2})日?', text)
        if reminder_match:
            name = reminder_match.group(1)
            amount = reminder_match.group(2)
            day = reminder_match.group(3)
            return 'set_reminder', [name, amount, day]
        
        # 特殊處理：收入 金額 備註
        income_match = re.match(r'收入\s+(\d+)\s*(.*)', text)
        if income_match:
            amount = income_match.group(1)
            note = income_match.group(2).strip()
            return 'income', [amount, note] if note else [amount]
        
        # 特殊處理：刪除 ID
        delete_match = re.match(r'刪除\s+(\d+)', text)
        if delete_match:
            trans_id = delete_match.group(1)
            return 'delete', [trans_id]
        
        return None, []


def parse_user_input(user_id: str, text: str) -> Dict:
    """
    統一的用戶輸入解析入口
    
    Args:
        user_id: 用戶 ID
        text: 用戶輸入文字
    
    Returns:
        解析結果字典：
        {
            'type': 'command' | 'transaction' | 'unknown',
            'command': 指令名稱（如果是指令）,
            'params': 參數列表（如果是指令）,
            'transaction': 交易資料（如果是交易）,
            'original_text': 原始文字
        }
    """
    text = text.strip()
    
    # 先嘗試解析為指令
    command, params = CommandParser.parse(text)
    if command:
        return {
            'type': 'command',
            'command': command,
            'params': params,
            'original_text': text
        }
    
    # 嘗試解析為交易記錄
    parser = TransactionParser(user_id)
    transaction = parser.parse(text)
    if transaction:
        return {
            'type': 'transaction',
            'transaction': transaction,
            'original_text': text
        }
    
    # 無法識別
    return {
        'type': 'unknown',
        'original_text': text
    }
