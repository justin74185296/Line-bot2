"""
智能記帳訊息解析器
"""
import re
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from config import Config


@dataclass
class ParseResult:
    """解析結果"""
    success: bool
    amount: float = 0.0
    category: str = ''
    transaction_type: str = 'expense'  # 'income' 或 'expense'
    note: str = ''
    confidence: float = 0.0  # 解析信心度 0-1
    needs_confirmation: bool = False
    suggested_category: str = ''
    raw_text: str = ''
    error_message: str = ''


class MessageParser:
    """智能訊息解析器"""
    
    # 金額匹配模式
    AMOUNT_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*[元塊]',  # 50元, 50塊
        r'\$\s*(\d+(?:\.\d+)?)',       # $50
        r'(\d+(?:\.\d+)?)',            # 純數字
    ]
    
    # 收入關鍵字
    INCOME_KEYWORDS = Config.INCOME_KEYWORDS
    
    # 類別關鍵字映射
    CATEGORY_KEYWORDS = Config.CATEGORY_KEYWORDS
    
    @classmethod
    def parse(cls, text: str, custom_categories: list = None) -> ParseResult:
        """
        解析用戶輸入的記帳訊息
        
        支援格式：
        - "早餐 50"
        - "午餐 100元"
        - "交通 $80"
        - "薪水 30000 收入"
        - "晚餐 200 麥當勞"
        """
        text = text.strip()
        
        if not text:
            return ParseResult(
                success=False,
                error_message='請輸入記帳內容',
                raw_text=text
            )
        
        # 1. 檢查是否為收入
        is_income = cls._is_income(text)
        
        # 2. 提取金額
        amount = cls._extract_amount(text)
        if amount is None or amount <= 0:
            return ParseResult(
                success=False,
                error_message='無法識別金額，請使用如「早餐 50」的格式',
                raw_text=text
            )
        
        # 3. 識別類別
        category, confidence = cls._identify_category(text, is_income, custom_categories)
        
        # 4. 提取備註
        note = cls._extract_note(text, amount, category)
        
        # 5. 判斷是否需要確認
        needs_confirmation = confidence < 0.7
        
        return ParseResult(
            success=True,
            amount=amount,
            category=category,
            transaction_type='income' if is_income else 'expense',
            note=note,
            confidence=confidence,
            needs_confirmation=needs_confirmation,
            suggested_category=category if needs_confirmation else '',
            raw_text=text
        )
    
    @classmethod
    def _is_income(cls, text: str) -> bool:
        """判斷是否為收入"""
        text_lower = text.lower()
        
        # 明確標記收入
        if '收入' in text or '入帳' in text:
            return True
        
        # 檢查收入關鍵字
        for keyword in cls.INCOME_KEYWORDS:
            if keyword in text:
                return True
        
        return False
    
    @classmethod
    def _extract_amount(cls, text: str) -> Optional[float]:
        """提取金額"""
        # 移除千分位符號
        text = text.replace(',', '')
        
        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    amount = float(match.group(1))
                    if amount > 0:
                        return amount
                except ValueError:
                    continue
        
        return None
    
    @classmethod
    def _identify_category(cls, text: str, is_income: bool, 
                          custom_categories: list = None) -> Tuple[str, float]:
        """
        識別類別
        返回 (類別名稱, 信心度)
        """
        text_lower = text.lower()
        
        if is_income:
            # 收入類別識別
            income_keywords = {
                '薪水': ['薪水', '薪資', '工資', '月薪'],
                '獎金': ['獎金', '年終', '分紅', '佣金', '績效'],
                '投資': ['投資', '股息', '利息', '分紅', '股票'],
                '兼職': ['兼職', '打工', '接案', '外快'],
                '禮金': ['禮金', '紅包', '禮物'],
                '其他收入': ['退款', '報銷', '返現', '中獎']
            }
            
            for category, keywords in income_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        return category, 0.9
            
            return '其他收入', 0.5
        
        # 支出類別識別
        best_category = '其他'
        best_confidence = 0.3
        
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # 關鍵字越長，信心度越高
                    confidence = min(0.9, 0.6 + len(keyword) * 0.05)
                    if confidence > best_confidence:
                        best_category = category
                        best_confidence = confidence
        
        # 檢查自訂類別
        if custom_categories:
            for custom_cat in custom_categories:
                if custom_cat.lower() in text_lower:
                    return custom_cat, 0.95
        
        return best_category, best_confidence
    
    @classmethod
    def _extract_note(cls, text: str, amount: float, category: str) -> str:
        """提取備註"""
        # 移除金額相關字串
        note = text
        
        # 移除金額
        amount_str = str(int(amount)) if amount == int(amount) else str(amount)
        note = re.sub(rf'\$?\s*{re.escape(amount_str)}\s*[元塊]?', '', note)
        
        # 移除類別關鍵字
        for cat, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                note = note.replace(keyword, '')
        
        # 移除收入/支出標記
        for keyword in ['收入', '支出', '入帳', '花費']:
            note = note.replace(keyword, '')
        
        # 清理空白
        note = ' '.join(note.split()).strip()
        
        # 如果備註太短或只剩類別名，返回空
        if len(note) < 2 or note == category:
            return ''
        
        return note
    
    @classmethod
    def parse_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        解析指令
        返回 (指令類型, 參數字典)
        """
        text = text.strip().lower()
        
        # 指令映射
        commands = {
            # 儀表板
            ('儀表板', 'dashboard', '首頁', '主頁'): ('dashboard', {}),
            
            # 時間範圍查詢
            ('今天', '今日', 'today'): ('today', {}),
            ('本月', '這個月', 'this_month'): ('this_month', {}),
            ('本週', '這週', '這禮拜', 'this_week'): ('this_week', {}),
            
            # 幫助
            ('幫助', '說明', 'help', '?', '？'): ('help', {}),
            
            # 匯出
            ('匯出', '導出', 'export'): ('export', {}),
            
            # 清空
            ('清空', '清除', '刪除全部', 'clear'): ('clear', {}),
            
            # 類別管理
            ('類別', '分類', 'categories'): ('categories', {}),
        }
        
        # 檢查完全匹配
        for keywords, result in commands.items():
            if text in keywords:
                return result
        
        # 檢查部分匹配和帶參數的指令
        
        # 預算指令
        if text.startswith(('預算', 'budget')) or '設定預算' in text:
            return cls._parse_budget_command(text)
        
        # 設定提醒
        if text.startswith(('提醒', '設定提醒', 'reminder')):
            return cls._parse_reminder_command(text)
        
        # 統計指令
        if text.startswith(('統計', 'stats')):
            return cls._parse_stats_command(text)
        
        # 收入指令
        if text.startswith(('收入', 'income')):
            return cls._parse_income_command(text)
        
        # 新增類別
        if text.startswith(('新增類別', '添加類別', 'add category')):
            return cls._parse_add_category_command(text)
        
        # 刪除類別
        if text.startswith(('刪除類別', '移除類別', 'delete category')):
            return cls._parse_delete_category_command(text)
        
        # 刪除記錄
        if text.startswith(('刪除', '取消', 'delete')):
            return cls._parse_delete_command(text)
        
        # 確認操作
        if text in ('是', '確認', 'yes', 'y', '對', '好'):
            return ('confirm', {})
        
        if text in ('否', '取消', 'no', 'n', '不要'):
            return ('cancel', {})
        
        # 無法識別為指令
        return ('unknown', {'text': text})
    
    @classmethod
    def _parse_budget_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析預算指令"""
        # 設定預算 5000
        # 設定預算 飲食 3000
        
        if '設定' in text or 'set' in text:
            # 提取金額
            amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if amount_match:
                amount = float(amount_match.group(1))
                
                # 檢查是否有類別
                for category in Config.DEFAULT_EXPENSE_CATEGORIES:
                    if category in text:
                        return ('set_category_budget', {
                            'category': category, 
                            'amount': amount
                        })
                
                return ('set_total_budget', {'amount': amount})
        
        return ('show_budget', {})
    
    @classmethod
    def _parse_reminder_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析提醒指令"""
        # 設定提醒 房租 10000 每月25日
        # 提醒
        
        if '設定' in text:
            # 提取金額
            amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
            # 提取日期
            day_match = re.search(r'(?:每月)?(\d{1,2})[日號]', text)
            
            if amount_match and day_match:
                amount = float(amount_match.group(1))
                day = int(day_match.group(1))
                
                # 提取名稱（移除已知部分後的文字）
                name = text
                name = re.sub(r'設定提醒|提醒|設定', '', name)
                name = re.sub(r'\d+(?:\.\d+)?', '', name)
                name = re.sub(r'每月?\d{1,2}[日號]', '', name)
                name = name.strip()
                
                if not name:
                    name = '帳單'
                
                return ('set_reminder', {
                    'name': name,
                    'amount': amount,
                    'day': day
                })
        
        # 刪除提醒
        if '刪除' in text or '取消' in text:
            # 提取提醒ID或名稱
            return ('delete_reminder', {'text': text})
        
        return ('show_reminders', {})
    
    @classmethod
    def _parse_stats_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析統計指令"""
        # 統計 2024/01
        # 統計 2024年1月
        
        year_match = re.search(r'(\d{4})', text)
        month_match = re.search(r'[/\-年]?\s*(\d{1,2})\s*月?', text)
        
        params = {}
        if year_match:
            params['year'] = int(year_match.group(1))
        if month_match:
            params['month'] = int(month_match.group(1))
        
        return ('stats', params)
    
    @classmethod
    def _parse_income_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析收入指令"""
        # 收入 5000 獎金
        
        # 移除 "收入" 關鍵字後解析
        text_without_keyword = re.sub(r'^收入\s*', '', text)
        
        return ('income', {'text': text_without_keyword})
    
    @classmethod
    def _parse_add_category_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析新增類別指令"""
        # 新增類別 旅行
        
        category = re.sub(r'^(新增類別|添加類別|add category)\s*', '', text, flags=re.IGNORECASE)
        category = category.strip()
        
        if category:
            return ('add_category', {'category': category})
        
        return ('add_category', {'category': ''})
    
    @classmethod
    def _parse_delete_category_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析刪除類別指令"""
        category = re.sub(r'^(刪除類別|移除類別|delete category)\s*', '', text, flags=re.IGNORECASE)
        category = category.strip()
        
        if category:
            return ('delete_category', {'category': category})
        
        return ('delete_category', {'category': ''})
    
    @classmethod
    def _parse_delete_command(cls, text: str) -> Tuple[str, Dict[str, Any]]:
        """解析刪除記錄指令"""
        # 刪除 abc123
        
        # 嘗試提取交易ID
        id_match = re.search(r'[a-f0-9]{8}', text, re.IGNORECASE)
        if id_match:
            return ('delete_transaction', {'transaction_id': id_match.group()})
        
        return ('delete_transaction', {'transaction_id': ''})
