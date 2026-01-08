"""
輔助工具函數
"""
from datetime import datetime
from typing import Optional


def format_amount(amount: float, with_symbol: bool = True) -> str:
    """
    格式化金額顯示
    
    Args:
        amount: 金額
        with_symbol: 是否包含貨幣符號
    
    Returns:
        格式化後的金額字串
    """
    if with_symbol:
        return f"${amount:,.0f}"
    return f"{amount:,.0f}"


def format_date(date_str: str, style: str = 'short') -> str:
    """
    格式化日期顯示
    
    Args:
        date_str: 日期字串 (YYYY-MM-DD)
        style: 'short' (MM/DD), 'medium' (M月D日), 'long' (YYYY年M月D日)
    
    Returns:
        格式化後的日期字串
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        if style == 'short':
            return date_obj.strftime('%m/%d')
        elif style == 'medium':
            return f"{date_obj.month}月{date_obj.day}日"
        elif style == 'long':
            return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"
        else:
            return date_str
    except ValueError:
        return date_str


def truncate_text(text: str, max_length: int = 20, suffix: str = '...') -> str:
    """
    截斷文字
    
    Args:
        text: 原始文字
        max_length: 最大長度
        suffix: 截斷後綴
    
    Returns:
        截斷後的文字
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def get_greeting() -> str:
    """根據時間取得問候語"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "早安"
    elif 12 <= hour < 18:
        return "午安"
    else:
        return "晚安"


def get_weekday_name(date_str: Optional[str] = None) -> str:
    """取得星期幾"""
    weekdays = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    
    if date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        date_obj = datetime.now()
    
    return weekdays[date_obj.weekday()]


def calculate_days_in_month(year: int, month: int) -> int:
    """計算某月的天數"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    from datetime import timedelta
    last_day = next_month - timedelta(days=1)
    return last_day.day


def get_month_range(year: int, month: int) -> tuple:
    """取得月份的起始和結束日期"""
    start_date = f"{year:04d}-{month:02d}-01"
    days = calculate_days_in_month(year, month)
    end_date = f"{year:04d}-{month:02d}-{days:02d}"
    return start_date, end_date
