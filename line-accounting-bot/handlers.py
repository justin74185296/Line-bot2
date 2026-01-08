"""
LINE 記帳機器人 - 訊息處理器模組
處理所有 LINE 訊息和指令
"""
from typing import Dict, Optional
import database
import utils
from parser import parse_user_input


# 用於追蹤等待確認的操作
pending_confirmations = {}


def handle_message(user_id: str, text: str) -> str:
    """
    處理用戶訊息的主入口
    
    Args:
        user_id: LINE 用戶 ID
        text: 用戶傳送的文字訊息
    
    Returns:
        回覆訊息
    """
    # 初始化用戶資料表
    database.init_user_tables(user_id)
    
    # 檢查是否有等待確認的操作
    if user_id in pending_confirmations:
        return handle_confirmation(user_id, text)
    
    # 解析用戶輸入
    parsed = parse_user_input(user_id, text)
    
    if parsed['type'] == 'command':
        return handle_command(user_id, parsed['command'], parsed['params'])
    elif parsed['type'] == 'transaction':
        return handle_transaction(user_id, parsed['transaction'])
    else:
        return utils.generate_error_message('parse')


def handle_command(user_id: str, command: str, params: list) -> str:
    """
    處理指令
    
    Args:
        user_id: 用戶 ID
        command: 指令名稱
        params: 參數列表
    
    Returns:
        回覆訊息
    """
    handlers = {
        'dashboard': handle_dashboard,
        'today': handle_today,
        'week': handle_week,
        'month': handle_month,
        'budget': handle_budget,
        'set_budget': handle_set_budget,
        'reminder': handle_reminder,
        'set_reminder': handle_set_reminder,
        'stats': handle_stats,
        'export': handle_export,
        'clear': handle_clear,
        'add_category': handle_add_category,
        'delete_category': handle_delete_category,
        'categories': handle_categories,
        'help': handle_help,
        'income': handle_income,
        'delete': handle_delete,
    }
    
    handler = handlers.get(command)
    if handler:
        return handler(user_id, params)
    else:
        return utils.generate_error_message('parse')


def handle_transaction(user_id: str, transaction: Dict) -> str:
    """
    處理交易記錄
    
    Args:
        user_id: 用戶 ID
        transaction: 解析後的交易資料
    
    Returns:
        確認訊息
    """
    # 新增交易記錄
    trans_id = database.add_transaction(
        user_id=user_id,
        trans_type=transaction['type'],
        amount=transaction['amount'],
        category=transaction['category'],
        note=transaction.get('note', '')
    )
    
    # 生成確認訊息
    msg = utils.generate_transaction_confirm_message(transaction)
    
    # 檢查預算狀況
    warnings = database.check_budget_status(user_id)
    if warnings:
        warning_msg = utils.generate_budget_warning_message(warnings)
        if warning_msg:
            msg += f"\n\n{warning_msg}"
    
    return msg


def handle_confirmation(user_id: str, text: str) -> str:
    """
    處理等待確認的操作
    
    Args:
        user_id: 用戶 ID
        text: 用戶輸入
    
    Returns:
        回覆訊息
    """
    pending = pending_confirmations.get(user_id)
    
    if not pending:
        return utils.generate_error_message('parse')
    
    action = pending.get('action')
    
    if action == 'clear':
        if text.strip() == '確認清空':
            count = database.clear_all_transactions(user_id)
            del pending_confirmations[user_id]
            return utils.generate_clear_success_message(count)
        else:
            del pending_confirmations[user_id]
            return "❌ 已取消清空操作"
    
    # 清除過期的確認
    del pending_confirmations[user_id]
    return handle_message(user_id, text)


# ========== 指令處理函數 ==========

def handle_dashboard(user_id: str, params: list) -> str:
    """處理儀表板指令"""
    return utils.generate_dashboard_message(user_id)


def handle_today(user_id: str, params: list) -> str:
    """處理今日統計指令"""
    return utils.generate_today_message(user_id)


def handle_week(user_id: str, params: list) -> str:
    """處理本週統計指令"""
    return utils.generate_week_message(user_id)


def handle_month(user_id: str, params: list) -> str:
    """處理本月統計指令"""
    return utils.generate_month_message(user_id)


def handle_budget(user_id: str, params: list) -> str:
    """處理預算查詢指令"""
    return utils.generate_budget_message(user_id)


def handle_set_budget(user_id: str, params: list) -> str:
    """
    處理設定預算指令
    
    格式：
    - 設定預算 10000（設定總預算）
    - 設定預算 飲食 5000（設定類別預算）
    """
    if not params:
        return "❌ 請指定預算金額\n\n💡 格式：\n• 設定預算 10000\n• 設定預算 飲食 5000"
    
    try:
        if len(params) == 1:
            # 設定總預算
            amount = float(params[0])
            category = '總預算'
        else:
            # 設定類別預算
            category = params[0]
            amount = float(params[1])
        
        if amount <= 0:
            return "❌ 預算金額必須大於 0"
        
        database.set_budget(user_id, category, amount)
        
        emoji = utils.get_category_emoji(category) if category != '總預算' else '📊'
        return f"✅ 已設定預算\n\n{emoji} {category}：${utils.format_amount(amount)}"
    
    except ValueError:
        return "❌ 無法識別預算金額\n\n💡 格式：設定預算 飲食 5000"


def handle_reminder(user_id: str, params: list) -> str:
    """處理提醒查詢指令"""
    return utils.generate_reminder_message(user_id)


def handle_set_reminder(user_id: str, params: list) -> str:
    """
    處理設定提醒指令
    
    格式：設定提醒 房租 10000 每月25日
    """
    if len(params) < 3:
        return "❌ 請提供完整資訊\n\n💡 格式：設定提醒 房租 10000 每月25日"
    
    try:
        name = params[0]
        amount = float(params[1])
        
        # 解析日期
        day_str = params[2] if len(params) > 2 else ''
        day = None
        
        # 嘗試從參數中提取日期數字
        import re
        day_match = re.search(r'(\d{1,2})', ' '.join(params[2:]))
        if day_match:
            day = int(day_match.group(1))
        
        if not day or day < 1 or day > 31:
            return "❌ 日期格式錯誤\n\n💡 請輸入 1-31 之間的日期"
        
        if amount <= 0:
            return "❌ 金額必須大於 0"
        
        reminder_id = database.add_reminder(user_id, name, amount, day)
        
        return f"✅ 已新增提醒\n\n📌 {name}\n💰 金額：${utils.format_amount(amount)}\n📅 每月 {day} 日提醒"
    
    except ValueError:
        return "❌ 無法識別金額\n\n💡 格式：設定提醒 房租 10000 每月25日"


def handle_stats(user_id: str, params: list) -> str:
    """
    處理統計指令
    
    格式：統計 2026/01
    """
    if not params:
        return utils.generate_month_message(user_id)
    
    try:
        if len(params) >= 2:
            year = int(params[0])
            month = int(params[1])
        else:
            # 嘗試解析 YYYY/MM 格式
            import re
            match = re.match(r'(\d{4})[/\-](\d{1,2})', params[0])
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
            else:
                return "❌ 日期格式錯誤\n\n💡 格式：統計 2026/01"
        
        if month < 1 or month > 12:
            return "❌ 月份必須在 1-12 之間"
        
        return utils.generate_month_message(user_id, year, month)
    
    except ValueError:
        return "❌ 日期格式錯誤\n\n💡 格式：統計 2026/01"


def handle_export(user_id: str, params: list) -> str:
    """處理匯出指令"""
    year = None
    month = None
    
    if params:
        try:
            import re
            match = re.match(r'(\d{4})[/\-](\d{1,2})', params[0])
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
        except:
            pass
    
    return utils.generate_export_message(user_id, year, month)


def handle_clear(user_id: str, params: list) -> str:
    """處理清空指令"""
    # 設定等待確認狀態
    pending_confirmations[user_id] = {
        'action': 'clear',
    }
    return utils.generate_clear_confirm_message()


def handle_add_category(user_id: str, params: list) -> str:
    """
    處理新增類別指令
    
    格式：新增類別 旅行
    """
    if not params:
        return "❌ 請指定類別名稱\n\n💡 格式：新增類別 旅行"
    
    category_name = params[0]
    
    # 檢查是否為預設類別
    all_cats = database.get_all_categories(user_id)
    all_category_names = all_cats['expense'] + all_cats['income']
    
    if category_name in all_category_names:
        return f"❌ 類別「{category_name}」已經存在"
    
    # 判斷是支出還是收入類別（預設為支出）
    cat_type = 'expense'
    if len(params) > 1 and params[1] in ['收入', 'income']:
        cat_type = 'income'
    
    success = database.add_custom_category(user_id, category_name, cat_type)
    
    if success:
        type_text = '收入' if cat_type == 'income' else '支出'
        return f"✅ 已新增{type_text}類別：{category_name}"
    else:
        return f"❌ 新增類別失敗，可能已存在同名類別"


def handle_delete_category(user_id: str, params: list) -> str:
    """
    處理刪除類別指令
    
    格式：刪除類別 旅行
    """
    if not params:
        return "❌ 請指定類別名稱\n\n💡 格式：刪除類別 旅行"
    
    category_name = params[0]
    
    # 檢查是否為預設類別
    import config
    default_all = config.DEFAULT_CATEGORIES['expense'] + config.DEFAULT_CATEGORIES['income']
    
    if category_name in default_all:
        return f"❌ 無法刪除預設類別「{category_name}」"
    
    success = database.delete_custom_category(user_id, category_name)
    
    if success:
        return f"✅ 已刪除類別：{category_name}"
    else:
        return f"❌ 找不到類別「{category_name}」或無法刪除"


def handle_categories(user_id: str, params: list) -> str:
    """處理類別列表指令"""
    return utils.generate_categories_message(user_id)


def handle_help(user_id: str, params: list) -> str:
    """處理幫助指令"""
    return utils.generate_help_message()


def handle_income(user_id: str, params: list) -> str:
    """
    處理手動新增收入指令
    
    格式：收入 5000 獎金
    """
    if not params:
        return "❌ 請指定收入金額\n\n💡 格式：收入 5000 獎金"
    
    try:
        amount = float(params[0])
        note = ' '.join(params[1:]) if len(params) > 1 else ''
        
        if amount <= 0:
            return "❌ 金額必須大於 0"
        
        transaction = {
            'type': 'income',
            'amount': amount,
            'category': '收入',
            'note': note
        }
        
        return handle_transaction(user_id, transaction)
    
    except ValueError:
        return "❌ 無法識別金額\n\n💡 格式：收入 5000 獎金"


def handle_delete(user_id: str, params: list) -> str:
    """
    處理刪除交易指令
    
    格式：刪除 123
    """
    if not params:
        # 顯示最近的交易供用戶選擇刪除
        recent = database.get_recent_transactions(user_id, 5)
        if not recent:
            return "📝 目前沒有任何交易記錄"
        
        msg = "📝 最近的交易記錄\n"
        msg += "━━━━━━━━━━━━━━━\n"
        
        for trans in recent:
            emoji = utils.get_category_emoji(trans['category'])
            type_sign = '+' if trans['type'] == 'income' else '-'
            date = utils.format_date(trans['created_at'], show_time=True)
            note = f" ({trans['note']})" if trans['note'] else ""
            msg += f"ID:{trans['id']} {date} {emoji} {type_sign}${utils.format_amount(trans['amount'])}{note}\n"
        
        msg += "\n💡 輸入「刪除 ID」來刪除記錄\n"
        msg += "例如：刪除 123"
        
        return msg
    
    try:
        trans_id = int(params[0])
        success = database.delete_transaction(user_id, trans_id)
        
        if success:
            return f"✅ 已刪除交易記錄 #{trans_id}"
        else:
            return f"❌ 找不到交易記錄 #{trans_id}"
    
    except ValueError:
        return "❌ 無效的交易 ID\n\n💡 格式：刪除 123"


# ========== 事件處理函數 ==========

def handle_follow_event(user_id: str) -> str:
    """
    處理用戶加入好友事件
    
    Args:
        user_id: 用戶 ID
    
    Returns:
        歡迎訊息
    """
    # 初始化用戶資料表
    database.init_user_tables(user_id)
    
    return utils.generate_welcome_message()


def handle_unfollow_event(user_id: str) -> None:
    """
    處理用戶封鎖/取消好友事件
    
    Args:
        user_id: 用戶 ID
    
    Note:
        可以選擇保留或刪除用戶資料
        目前選擇保留資料，以便用戶重新加入時可以繼續使用
    """
    # 可以在這裡加入清理邏輯
    # 目前選擇保留用戶資料
    pass
