"""
LINE 記帳機器人 - 工具函數模組
提供格式化、訊息生成等輔助功能
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
import database


def format_amount(amount: float) -> str:
    """
    格式化金額顯示
    
    Args:
        amount: 金額數值
    
    Returns:
        格式化後的字串，如 "1,234" 或 "1,234.50"
    """
    if amount == int(amount):
        return f"{int(amount):,}"
    else:
        return f"{amount:,.2f}"


def format_date(date_str: str, show_time: bool = False) -> str:
    """
    格式化日期顯示
    
    Args:
        date_str: 日期字串
        show_time: 是否顯示時間
    
    Returns:
        格式化後的日期字串
    """
    try:
        if len(date_str) > 10:
            dt = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
        else:
            dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        
        if show_time:
            return dt.strftime('%m/%d %H:%M')
        else:
            return dt.strftime('%m/%d')
    except:
        return date_str[:10] if len(date_str) >= 10 else date_str


def get_category_emoji(category: str) -> str:
    """取得類別對應的 emoji"""
    return config.CATEGORY_EMOJI.get(category, '📌')


def generate_transaction_confirm_message(trans: Dict) -> str:
    """
    生成交易確認訊息
    
    Args:
        trans: 交易資料字典
    
    Returns:
        確認訊息文字
    """
    emoji = get_category_emoji(trans['category'])
    type_text = '收入' if trans['type'] == 'income' else '支出'
    type_emoji = '💵' if trans['type'] == 'income' else '💸'
    
    msg = f"{type_emoji} 已記錄{type_text}！\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"{emoji} 類別：{trans['category']}\n"
    msg += f"💰 金額：${format_amount(trans['amount'])}\n"
    
    if trans.get('note'):
        msg += f"📝 備註：{trans['note']}\n"
    
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"📅 時間：{datetime.now().strftime('%Y/%m/%d %H:%M')}"
    
    return msg


def generate_dashboard_message(user_id: str) -> str:
    """
    生成儀表板訊息
    
    Args:
        user_id: 用戶 ID
    
    Returns:
        儀表板訊息文字
    """
    # 取得本月交易
    transactions = database.get_month_transactions(user_id)
    stats = database.get_statistics(user_id, transactions)
    
    # 取得預算
    budgets = database.get_all_budgets(user_id)
    total_budget = None
    for b in budgets:
        if b['category'] == '總預算':
            total_budget = b['amount']
            break
    
    # 取得最近 5 筆交易
    recent = database.get_recent_transactions(user_id, 5)
    
    now = datetime.now()
    
    msg = f"📊 財務儀表板\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"📅 {now.year}年{now.month}月\n\n"
    
    # 收支概況
    msg += f"💰 本月收入：${format_amount(stats['total_income'])}\n"
    msg += f"💸 本月支出：${format_amount(stats['total_expense'])}\n"
    msg += f"📈 淨餘額：${format_amount(stats['balance'])}\n"
    
    # 預算狀況
    if total_budget:
        remaining = total_budget - stats['total_expense']
        usage_percent = (stats['total_expense'] / total_budget * 100) if total_budget > 0 else 0
        msg += f"\n📋 預算進度\n"
        msg += f"預算：${format_amount(total_budget)}\n"
        msg += f"已用：{usage_percent:.1f}%\n"
        if remaining >= 0:
            msg += f"剩餘：${format_amount(remaining)}\n"
        else:
            msg += f"⚠️ 超支：${format_amount(abs(remaining))}\n"
        
        # 現金流預測
        days_in_month = _get_days_in_month(now.year, now.month)
        days_passed = now.day
        days_remaining = days_in_month - days_passed
        
        if days_passed > 0 and stats['total_expense'] > 0:
            daily_avg = stats['total_expense'] / days_passed
            projected_expense = daily_avg * days_in_month
            projected_remaining = total_budget - projected_expense
            
            msg += f"\n🔮 現金流預測\n"
            msg += f"日均支出：${format_amount(daily_avg)}\n"
            if projected_remaining >= 0:
                msg += f"預計月底剩餘：${format_amount(projected_remaining)}\n"
            else:
                msg += f"⚠️ 預計超支：${format_amount(abs(projected_remaining))}\n"
    
    # 類別支出分佈
    if stats['category_totals']:
        msg += f"\n📊 類別支出分佈\n"
        sorted_cats = sorted(
            stats['category_totals'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for cat, amount in sorted_cats[:5]:
            emoji = get_category_emoji(cat)
            percent = stats['category_percentages'].get(cat, 0)
            bar = _generate_progress_bar(percent)
            msg += f"{emoji} {cat}：${format_amount(amount)} ({percent}%)\n"
            msg += f"   {bar}\n"
    
    # 最近交易
    if recent:
        msg += f"\n📝 最近交易\n"
        for trans in recent:
            emoji = get_category_emoji(trans['category'])
            type_sign = '+' if trans['type'] == 'income' else '-'
            date = format_date(trans['created_at'])
            note = f" ({trans['note']})" if trans['note'] else ""
            msg += f"{date} {emoji} {type_sign}${format_amount(trans['amount'])}{note}\n"
    
    return msg


def generate_today_message(user_id: str) -> str:
    """生成今日統計訊息"""
    transactions = database.get_today_transactions(user_id)
    stats = database.get_statistics(user_id, transactions)
    
    today = datetime.now()
    
    msg = f"📅 今日帳務 ({today.month}/{today.day})\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    if not transactions:
        msg += "今天還沒有任何記錄喔！\n"
        msg += "💡 直接輸入如「早餐 50」即可記帳"
        return msg
    
    msg += f"💰 收入：${format_amount(stats['total_income'])}\n"
    msg += f"💸 支出：${format_amount(stats['total_expense'])}\n"
    msg += f"📊 淨額：${format_amount(stats['balance'])}\n\n"
    
    msg += f"📋 明細列表\n"
    for trans in transactions:
        emoji = get_category_emoji(trans['category'])
        type_sign = '+' if trans['type'] == 'income' else '-'
        time = format_date(trans['created_at'], show_time=True)
        note = f" - {trans['note']}" if trans['note'] else ""
        msg += f"{time} {emoji} {type_sign}${format_amount(trans['amount'])}{note}\n"
    
    return msg


def generate_week_message(user_id: str) -> str:
    """生成本週統計訊息"""
    transactions = database.get_week_transactions(user_id)
    stats = database.get_statistics(user_id, transactions)
    
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    msg = f"📅 本週帳務\n"
    msg += f"({start_of_week.month}/{start_of_week.day} - {today.month}/{today.day})\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    if not transactions:
        msg += "這週還沒有任何記錄喔！"
        return msg
    
    msg += f"💰 收入：${format_amount(stats['total_income'])}\n"
    msg += f"💸 支出：${format_amount(stats['total_expense'])}\n"
    msg += f"📊 淨額：${format_amount(stats['balance'])}\n"
    msg += f"📝 交易筆數：{stats['transaction_count']} 筆\n\n"
    
    # 類別分佈
    if stats['category_totals']:
        msg += f"📊 支出分佈\n"
        sorted_cats = sorted(
            stats['category_totals'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for cat, amount in sorted_cats:
            emoji = get_category_emoji(cat)
            percent = stats['category_percentages'].get(cat, 0)
            msg += f"{emoji} {cat}：${format_amount(amount)} ({percent}%)\n"
    
    return msg


def generate_month_message(user_id: str, year: int = None, 
                          month: int = None) -> str:
    """生成月份統計訊息"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    transactions = database.get_month_transactions(user_id, year, month)
    stats = database.get_statistics(user_id, transactions)
    
    is_current_month = (year == now.year and month == now.month)
    
    msg = f"📅 {year}年{month}月帳務\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    if not transactions:
        msg += "這個月還沒有任何記錄喔！"
        return msg
    
    msg += f"💰 總收入：${format_amount(stats['total_income'])}\n"
    msg += f"💸 總支出：${format_amount(stats['total_expense'])}\n"
    msg += f"📊 淨餘額：${format_amount(stats['balance'])}\n"
    msg += f"📝 交易筆數：{stats['transaction_count']} 筆\n\n"
    
    # 預算進度（僅當前月份）
    if is_current_month:
        budgets = database.get_all_budgets(user_id)
        total_budget = None
        for b in budgets:
            if b['category'] == '總預算':
                total_budget = b['amount']
                break
        
        if total_budget:
            remaining = total_budget - stats['total_expense']
            usage_percent = (stats['total_expense'] / total_budget * 100)
            msg += f"📋 預算使用\n"
            msg += f"預算：${format_amount(total_budget)}\n"
            msg += f"進度：{usage_percent:.1f}%\n"
            if remaining >= 0:
                msg += f"剩餘：${format_amount(remaining)}\n\n"
            else:
                msg += f"⚠️ 超支：${format_amount(abs(remaining))}\n\n"
    
    # 類別分佈（圓餅圖文字）
    if stats['category_totals']:
        msg += f"📊 支出類別分佈\n"
        sorted_cats = sorted(
            stats['category_totals'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for cat, amount in sorted_cats:
            emoji = get_category_emoji(cat)
            percent = stats['category_percentages'].get(cat, 0)
            bar = _generate_progress_bar(percent)
            msg += f"{emoji} {cat}\n"
            msg += f"   ${format_amount(amount)} ({percent}%)\n"
            msg += f"   {bar}\n"
    
    return msg


def generate_budget_message(user_id: str) -> str:
    """生成預算狀況訊息"""
    budgets = database.get_all_budgets(user_id)
    
    msg = f"💰 預算設定\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    if not budgets:
        msg += "目前尚未設定任何預算\n\n"
        msg += "💡 設定方式：\n"
        msg += "• 設定預算 10000（設定總預算）\n"
        msg += "• 設定預算 飲食 5000（設定類別預算）"
        return msg
    
    # 取得本月支出
    transactions = database.get_month_transactions(user_id)
    stats = database.get_statistics(user_id, transactions)
    
    for budget in budgets:
        category = budget['category']
        budget_amount = budget['amount']
        
        if category == '總預算':
            spent = stats['total_expense']
            emoji = '📊'
        else:
            spent = stats['category_totals'].get(category, 0)
            emoji = get_category_emoji(category)
        
        remaining = budget_amount - spent
        usage_percent = (spent / budget_amount * 100) if budget_amount > 0 else 0
        bar = _generate_progress_bar(usage_percent)
        
        msg += f"\n{emoji} {category}\n"
        msg += f"預算：${format_amount(budget_amount)}\n"
        msg += f"已用：${format_amount(spent)} ({usage_percent:.1f}%)\n"
        msg += f"{bar}\n"
        
        if remaining >= 0:
            msg += f"剩餘：${format_amount(remaining)}\n"
        else:
            msg += f"⚠️ 超支：${format_amount(abs(remaining))}\n"
    
    return msg


def generate_reminder_message(user_id: str) -> str:
    """生成提醒列表訊息"""
    reminders = database.get_reminders(user_id)
    
    msg = f"⏰ 帳單提醒\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    if not reminders:
        msg += "目前沒有設定任何提醒\n\n"
        msg += "💡 設定方式：\n"
        msg += "設定提醒 房租 10000 每月25日"
        return msg
    
    for r in reminders:
        msg += f"\n📌 {r['name']}\n"
        msg += f"   金額：${format_amount(r['amount'])}\n"
        msg += f"   每月 {r['day_of_month']} 日\n"
    
    return msg


def generate_categories_message(user_id: str) -> str:
    """生成類別列表訊息"""
    categories = database.get_all_categories(user_id)
    custom_cats = database.get_custom_categories(user_id)
    custom_names = [c['name'] for c in custom_cats]
    
    msg = f"📑 記帳類別\n"
    msg += f"━━━━━━━━━━━━━━━\n\n"
    
    msg += f"💸 支出類別\n"
    for cat in categories['expense']:
        emoji = get_category_emoji(cat)
        is_custom = " (自訂)" if cat in custom_names else ""
        msg += f"{emoji} {cat}{is_custom}\n"
    
    msg += f"\n💰 收入類別\n"
    for cat in categories['income']:
        emoji = get_category_emoji(cat)
        is_custom = " (自訂)" if cat in custom_names else ""
        msg += f"{emoji} {cat}{is_custom}\n"
    
    msg += f"\n💡 管理類別：\n"
    msg += f"• 新增類別 旅行\n"
    msg += f"• 刪除類別 旅行"
    
    return msg


def generate_export_message(user_id: str, year: int = None, 
                           month: int = None) -> str:
    """生成匯出 CSV 訊息"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    csv_content = database.export_transactions_csv(user_id, year, month)
    
    if not csv_content:
        return f"📤 匯出失敗\n\n{year}年{month}月沒有任何交易記錄"
    
    msg = f"📤 匯出 {year}年{month}月交易記錄\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"請複製以下 CSV 內容：\n\n"
    msg += f"```\n{csv_content}\n```"
    
    return msg


def generate_help_message() -> str:
    """生成幫助訊息"""
    msg = f"📖 使用說明\n"
    msg += f"━━━━━━━━━━━━━━━\n\n"
    
    msg += f"💡 快速記帳\n"
    msg += f"直接輸入文字即可記帳：\n"
    msg += f"• 早餐 50\n"
    msg += f"• 晚餐 200 元\n"
    msg += f"• 交通 100\n"
    msg += f"• 購物 500 網購\n"
    msg += f"• 薪水 30000（自動識別為收入）\n\n"
    
    msg += f"📊 查看統計\n"
    msg += f"• 儀表板 - 本月總覽\n"
    msg += f"• 今天 - 今日明細\n"
    msg += f"• 本週 - 本週統計\n"
    msg += f"• 本月 - 本月統計\n"
    msg += f"• 統計 2026/01 - 指定月份\n\n"
    
    msg += f"💰 預算管理\n"
    msg += f"• 預算 - 查看預算\n"
    msg += f"• 設定預算 10000 - 設定總預算\n"
    msg += f"• 設定預算 飲食 5000 - 類別預算\n\n"
    
    msg += f"⏰ 提醒功能\n"
    msg += f"• 提醒 - 查看提醒\n"
    msg += f"• 設定提醒 房租 10000 每月25日\n\n"
    
    msg += f"📑 其他功能\n"
    msg += f"• 類別 - 查看類別列表\n"
    msg += f"• 新增類別 旅行\n"
    msg += f"• 刪除類別 旅行\n"
    msg += f"• 匯出 - 匯出本月 CSV\n"
    msg += f"• 清空 - 清除所有記錄\n\n"
    
    msg += f"🎯 記帳小技巧\n"
    msg += f"系統會自動識別類別，例如：\n"
    msg += f"「咖啡 100」→ 自動歸類為飲食\n"
    msg += f"「加油 500」→ 自動歸類為交通"
    
    return msg


def generate_clear_confirm_message() -> str:
    """生成清空確認訊息"""
    msg = f"⚠️ 確認清空\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    msg += f"此操作將刪除所有交易記錄！\n"
    msg += f"此操作無法復原！\n\n"
    msg += f"請輸入「確認清空」來執行"
    return msg


def generate_clear_success_message(count: int) -> str:
    """生成清空成功訊息"""
    return f"✅ 已清空 {count} 筆交易記錄"


def generate_welcome_message() -> str:
    """生成歡迎訊息"""
    msg = f"👋 歡迎使用記帳小幫手！\n"
    msg += f"━━━━━━━━━━━━━━━\n\n"
    msg += f"我可以幫你輕鬆追蹤每一筆收支 💰\n\n"
    msg += f"🚀 快速開始：\n"
    msg += f"直接輸入如「早餐 50」即可記帳！\n\n"
    msg += f"📊 主要功能：\n"
    msg += f"• 智能記帳 - 自動識別類別\n"
    msg += f"• 統計報表 - 圖表化分析\n"
    msg += f"• 預算管理 - 控制支出\n"
    msg += f"• 帳單提醒 - 不漏繳費用\n\n"
    msg += f"輸入「幫助」查看完整功能說明 📖"
    
    return msg


def generate_error_message(error_type: str = 'parse') -> str:
    """生成錯誤訊息"""
    if error_type == 'parse':
        msg = f"🤔 抱歉，我無法理解您的輸入\n\n"
        msg += f"💡 記帳格式範例：\n"
        msg += f"• 早餐 50\n"
        msg += f"• 交通 100\n"
        msg += f"• 購物 500 生日禮物\n\n"
        msg += f"輸入「幫助」查看更多說明"
    else:
        msg = f"😅 發生了一點小問題\n請稍後再試，或輸入「幫助」查看說明"
    
    return msg


def generate_budget_warning_message(warnings: List[Dict]) -> str:
    """生成預算警告訊息"""
    if not warnings:
        return ""
    
    msg = f"⚠️ 預算提醒\n"
    msg += f"━━━━━━━━━━━━━━━\n"
    
    for w in warnings:
        emoji = '🔴' if w['is_over'] else '🟡'
        status = '已超支' if w['is_over'] else '即將用完'
        
        msg += f"\n{emoji} {w['category']} {status}！\n"
        msg += f"預算：${format_amount(w['budget'])}\n"
        msg += f"已用：${format_amount(w['spent'])} ({w['ratio']*100:.1f}%)\n"
    
    msg += f"\n💡 請注意控制支出喔！"
    
    return msg


# ========== 內部輔助函數 ==========

def _generate_progress_bar(percent: float, length: int = 10) -> str:
    """生成進度條"""
    filled = int(percent / 100 * length)
    filled = min(filled, length)  # 確保不超過長度
    
    bar = '█' * filled + '░' * (length - filled)
    return f"[{bar}]"


def _get_days_in_month(year: int, month: int) -> int:
    """取得指定月份的天數"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    this_month = datetime(year, month, 1)
    return (next_month - this_month).days
