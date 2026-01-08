"""
驗證工具函數
"""
import re
from datetime import datetime
from typing import Optional, Tuple

from config import Config


def validate_amount(amount: any) -> Tuple[bool, Optional[float], str]:
    """
    驗證金額
    
    Args:
        amount: 金額值
    
    Returns:
        (是否有效, 金額值, 錯誤訊息)
    """
    try:
        # 如果是字串，移除貨幣符號和千分位
        if isinstance(amount, str):
            amount = amount.replace('$', '').replace(',', '').strip()
        
        amount_float = float(amount)
        
        if amount_float <= 0:
            return False, None, "金額必須大於 0"
        
        if amount_float > 100000000:  # 一億
            return False, None, "金額過大，請確認是否正確"
        
        return True, amount_float, ""
    
    except (ValueError, TypeError):
        return False, None, "無效的金額格式"


def validate_date(date_str: str) -> Tuple[bool, Optional[str], str]:
    """
    驗證日期
    
    Args:
        date_str: 日期字串
    
    Returns:
        (是否有效, 標準化日期, 錯誤訊息)
    """
    # 支援多種格式
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y.%m.%d',
        '%m/%d',
        '%m-%d',
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            
            # 如果沒有年份，使用當前年份
            if '%Y' not in fmt:
                date_obj = date_obj.replace(year=datetime.now().year)
            
            # 檢查日期是否合理（不能是未來太久）
            if date_obj > datetime.now():
                # 允許今天
                if date_obj.date() > datetime.now().date():
                    return False, None, "不能記錄未來的交易"
            
            return True, date_obj.strftime('%Y-%m-%d'), ""
        
        except ValueError:
            continue
    
    return False, None, "無效的日期格式，請使用 YYYY-MM-DD"


def validate_category(category: str, 
                     is_expense: bool = True,
                     custom_categories: list = None) -> Tuple[bool, str]:
    """
    驗證類別
    
    Args:
        category: 類別名稱
        is_expense: 是否為支出類別
        custom_categories: 自訂類別列表
    
    Returns:
        (是否有效, 錯誤訊息)
    """
    if not category or not category.strip():
        return False, "類別名稱不能為空"
    
    category = category.strip()
    
    if len(category) > 20:
        return False, "類別名稱過長（最多20字）"
    
    if len(category) < 1:
        return False, "類別名稱過短（至少1字）"
    
    # 檢查是否包含特殊字元
    if re.search(r'[<>"\'/\\]', category):
        return False, "類別名稱不能包含特殊字元"
    
    # 取得所有有效類別
    if is_expense:
        valid_categories = Config.DEFAULT_EXPENSE_CATEGORIES.copy()
    else:
        valid_categories = Config.DEFAULT_INCOME_CATEGORIES.copy()
    
    if custom_categories:
        valid_categories.extend(custom_categories)
    
    # 不強制要求類別存在（允許自動建立新類別）
    return True, ""


def validate_reminder_day(day: int) -> Tuple[bool, str]:
    """
    驗證提醒日期
    
    Args:
        day: 每月幾號
    
    Returns:
        (是否有效, 錯誤訊息)
    """
    if not isinstance(day, int):
        try:
            day = int(day)
        except (ValueError, TypeError):
            return False, "日期必須是數字"
    
    if day < 1 or day > 31:
        return False, "日期必須在 1-31 之間"
    
    return True, ""


def validate_budget(amount: float) -> Tuple[bool, str]:
    """
    驗證預算金額
    
    Args:
        amount: 預算金額
    
    Returns:
        (是否有效, 錯誤訊息)
    """
    is_valid, _, error = validate_amount(amount)
    
    if not is_valid:
        return False, error
    
    if amount < 100:
        return False, "預算金額至少要 100 元"
    
    return True, ""
