"""
LINE 記帳機器人 - 資料庫模組
使用 SQLite 進行資料儲存，每位用戶獨立表格
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import config


@contextmanager
def get_connection():
    """取得資料庫連線的 context manager"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_user_tables(user_id: str) -> None:
    """
    初始化用戶的所有資料表
    
    Args:
        user_id: LINE 用戶 ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 交易記錄表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS transactions_{user_id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 預算表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS budgets_{user_id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE,
                amount REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 自訂類別表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS categories_{user_id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL DEFAULT 'expense',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 提醒表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS reminders_{user_id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                day_of_month INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_notified DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用戶設定表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS settings_{user_id} (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()


# ========== 交易相關函數 ==========

def add_transaction(user_id: str, trans_type: str, amount: float, 
                   category: str, note: str = '') -> int:
    """
    新增交易記錄
    
    Args:
        user_id: 用戶 ID
        trans_type: 交易類型 (income/expense)
        amount: 金額
        category: 類別
        note: 備註
    
    Returns:
        新增記錄的 ID
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO transactions_{user_id} (type, amount, category, note)
            VALUES (?, ?, ?, ?)
        ''', (trans_type, amount, category, note))
        conn.commit()
        return cursor.lastrowid


def get_transactions_by_date_range(user_id: str, start_date: datetime, 
                                   end_date: datetime) -> List[Dict]:
    """
    取得指定日期範圍內的交易記錄
    
    Args:
        user_id: 用戶 ID
        start_date: 開始日期
        end_date: 結束日期
    
    Returns:
        交易記錄列表
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM transactions_{user_id}
            WHERE created_at >= ? AND created_at < ?
            ORDER BY created_at DESC
        ''', (start_date.strftime(config.DATETIME_FORMAT), 
              end_date.strftime(config.DATETIME_FORMAT)))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_today_transactions(user_id: str) -> List[Dict]:
    """取得今日交易記錄"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    return get_transactions_by_date_range(user_id, today, tomorrow)


def get_week_transactions(user_id: str) -> List[Dict]:
    """取得本週交易記錄"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=7)
    return get_transactions_by_date_range(user_id, start_of_week, end_of_week)


def get_month_transactions(user_id: str, year: int = None, 
                          month: int = None) -> List[Dict]:
    """取得指定月份交易記錄，預設為本月"""
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    return get_transactions_by_date_range(user_id, start_date, end_date)


def get_recent_transactions(user_id: str, limit: int = 5) -> List[Dict]:
    """取得最近的交易記錄"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM transactions_{user_id}
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_transaction(user_id: str, transaction_id: int) -> bool:
    """刪除指定交易記錄"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            DELETE FROM transactions_{user_id} WHERE id = ?
        ''', (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_transactions(user_id: str) -> int:
    """清除用戶所有交易記錄"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM transactions_{user_id}')
        conn.commit()
        return cursor.rowcount


# ========== 統計相關函數 ==========

def get_statistics(user_id: str, transactions: List[Dict]) -> Dict:
    """
    計算交易統計數據
    
    Args:
        user_id: 用戶 ID
        transactions: 交易記錄列表
    
    Returns:
        統計數據字典
    """
    total_income = 0.0
    total_expense = 0.0
    category_totals = {}
    
    for trans in transactions:
        if trans['type'] == 'income':
            total_income += trans['amount']
        else:
            total_expense += trans['amount']
            category = trans['category']
            category_totals[category] = category_totals.get(category, 0) + trans['amount']
    
    # 計算類別百分比
    category_percentages = {}
    if total_expense > 0:
        for cat, amount in category_totals.items():
            category_percentages[cat] = round((amount / total_expense) * 100, 1)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
        'category_totals': category_totals,
        'category_percentages': category_percentages,
        'transaction_count': len(transactions)
    }


# ========== 預算相關函數 ==========

def set_budget(user_id: str, category: str, amount: float) -> None:
    """
    設定預算
    
    Args:
        user_id: 用戶 ID
        category: 類別（'總預算' 表示總預算）
        amount: 預算金額
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT OR REPLACE INTO budgets_{user_id} (category, amount, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (category, amount))
        conn.commit()


def get_budget(user_id: str, category: str = None) -> Optional[Dict]:
    """
    取得預算
    
    Args:
        user_id: 用戶 ID
        category: 類別（None 表示取得所有預算）
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute(f'''
                SELECT * FROM budgets_{user_id} WHERE category = ?
            ''', (category,))
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor.execute(f'SELECT * FROM budgets_{user_id}')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def get_all_budgets(user_id: str) -> List[Dict]:
    """取得所有預算設定"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM budgets_{user_id}')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_budget(user_id: str, category: str) -> bool:
    """刪除預算設定"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            DELETE FROM budgets_{user_id} WHERE category = ?
        ''', (category,))
        conn.commit()
        return cursor.rowcount > 0


# ========== 自訂類別相關函數 ==========

def add_custom_category(user_id: str, name: str, 
                       cat_type: str = 'expense') -> bool:
    """
    新增自訂類別
    
    Args:
        user_id: 用戶 ID
        name: 類別名稱
        cat_type: 類別類型 (expense/income)
    
    Returns:
        是否成功新增
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
                INSERT INTO categories_{user_id} (name, type)
                VALUES (?, ?)
            ''', (name, cat_type))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def delete_custom_category(user_id: str, name: str) -> bool:
    """刪除自訂類別"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            DELETE FROM categories_{user_id} WHERE name = ?
        ''', (name,))
        conn.commit()
        return cursor.rowcount > 0


def get_custom_categories(user_id: str) -> List[Dict]:
    """取得用戶所有自訂類別"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM categories_{user_id}')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_categories(user_id: str) -> Dict[str, List[str]]:
    """取得用戶所有類別（包含預設和自訂）"""
    custom_cats = get_custom_categories(user_id)
    
    # 複製預設類別
    all_cats = {
        'expense': list(config.DEFAULT_CATEGORIES['expense']),
        'income': list(config.DEFAULT_CATEGORIES['income'])
    }
    
    # 加入自訂類別
    for cat in custom_cats:
        if cat['type'] in all_cats:
            if cat['name'] not in all_cats[cat['type']]:
                all_cats[cat['type']].append(cat['name'])
    
    return all_cats


# ========== 提醒相關函數 ==========

def add_reminder(user_id: str, name: str, amount: float, 
                day_of_month: int) -> int:
    """
    新增提醒
    
    Args:
        user_id: 用戶 ID
        name: 提醒名稱
        amount: 金額
        day_of_month: 每月幾號
    
    Returns:
        新增記錄的 ID
    """
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO reminders_{user_id} (name, amount, day_of_month)
            VALUES (?, ?, ?)
        ''', (name, amount, day_of_month))
        conn.commit()
        return cursor.lastrowid


def get_reminders(user_id: str) -> List[Dict]:
    """取得用戶所有提醒"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM reminders_{user_id}
            WHERE is_active = 1
            ORDER BY day_of_month
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_today_reminders(user_id: str) -> List[Dict]:
    """取得今日到期的提醒"""
    today = datetime.now().day
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT * FROM reminders_{user_id}
            WHERE is_active = 1 AND day_of_month = ?
        ''', (today,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def delete_reminder(user_id: str, reminder_id: int) -> bool:
    """刪除提醒"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            DELETE FROM reminders_{user_id} WHERE id = ?
        ''', (reminder_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_reminder_notified(user_id: str, reminder_id: int) -> None:
    """更新提醒的最後通知日期"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE reminders_{user_id}
            SET last_notified = DATE('now')
            WHERE id = ?
        ''', (reminder_id,))
        conn.commit()


# ========== 用戶設定相關函數 ==========

def set_user_setting(user_id: str, key: str, value: str) -> None:
    """設定用戶設定"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT OR REPLACE INTO settings_{user_id} (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        conn.commit()


def get_user_setting(user_id: str, key: str) -> Optional[str]:
    """取得用戶設定"""
    init_user_tables(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT value FROM settings_{user_id} WHERE key = ?
        ''', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None


# ========== 資料匯出相關函數 ==========

def export_transactions_csv(user_id: str, year: int = None, 
                           month: int = None) -> str:
    """
    匯出交易記錄為 CSV 格式文字
    
    Args:
        user_id: 用戶 ID
        year: 年份（預設本月）
        month: 月份（預設本月）
    
    Returns:
        CSV 格式字串
    """
    transactions = get_month_transactions(user_id, year, month)
    
    if not transactions:
        return ""
    
    # CSV 標題
    csv_lines = ["日期,類型,類別,金額,備註"]
    
    for trans in transactions:
        date = trans['created_at'][:10] if trans['created_at'] else ''
        trans_type = '收入' if trans['type'] == 'income' else '支出'
        note = trans['note'].replace(',', '，') if trans['note'] else ''
        csv_lines.append(f"{date},{trans_type},{trans['category']},{trans['amount']},{note}")
    
    return '\n'.join(csv_lines)


# ========== 預算檢查函數 ==========

def check_budget_status(user_id: str) -> List[Dict]:
    """
    檢查預算使用狀況
    
    Returns:
        超過警告閾值的預算列表
    """
    budgets = get_all_budgets(user_id)
    if not budgets:
        return []
    
    month_transactions = get_month_transactions(user_id)
    stats = get_statistics(user_id, month_transactions)
    
    warnings = []
    
    for budget in budgets:
        category = budget['category']
        budget_amount = budget['amount']
        
        if category == '總預算':
            spent = stats['total_expense']
        else:
            spent = stats['category_totals'].get(category, 0)
        
        if budget_amount > 0:
            usage_ratio = spent / budget_amount
            if usage_ratio >= config.BUDGET_WARNING_THRESHOLD:
                warnings.append({
                    'category': category,
                    'budget': budget_amount,
                    'spent': spent,
                    'ratio': usage_ratio,
                    'is_over': usage_ratio >= 1.0
                })
    
    return warnings
