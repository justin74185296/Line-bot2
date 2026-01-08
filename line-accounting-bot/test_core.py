#!/usr/bin/env python3
"""
核心邏輯測試腳本（不需要外部依賴）
可以直接運行驗證解析和統計邏輯
"""
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, Emoji, CATEGORY_EMOJI
from models.transaction import Transaction
from models.budget import Budget
from models.reminder import Reminder
from models.user_data import UserData
from services.parser import MessageParser
from utils.helpers import format_amount, format_date
from utils.validators import validate_amount, validate_date

def test_transaction_model():
    """測試交易模型"""
    print("\n📝 測試交易模型...")
    
    t = Transaction(
        amount=100,
        category="飲食",
        transaction_type="expense",
        note="午餐"
    )
    
    assert t.amount == 100
    assert t.category == "飲食"
    assert t.is_expense == True
    assert t.is_income == False
    
    # 測試序列化
    d = t.to_dict()
    t2 = Transaction.from_dict(d)
    assert t2.amount == t.amount
    assert t2.category == t.category
    
    print("   ✅ 交易模型測試通過")

def test_budget_model():
    """測試預算模型"""
    print("\n💰 測試預算模型...")
    
    b = Budget()
    b.set_total_budget(10000)
    b.set_category_budget("飲食", 3000)
    
    assert b.total_budget == 10000
    assert b.get_category_budget("飲食") == 3000
    assert b.has_budget() == True
    
    print("   ✅ 預算模型測試通過")

def test_reminder_model():
    """測試提醒模型"""
    print("\n🔔 測試提醒模型...")
    
    r = Reminder(
        name="房租",
        amount=10000,
        day_of_month=25
    )
    
    assert r.name == "房租"
    assert r.amount == 10000
    assert r.day_of_month == 25
    assert r.is_active == True
    
    print("   ✅ 提醒模型測試通過")

def test_user_data_model():
    """測試用戶資料模型"""
    print("\n👤 測試用戶資料模型...")
    
    user = UserData(user_id="test123")
    
    # 新增交易
    t = Transaction(amount=50, category="飲食", transaction_type="expense")
    user.add_transaction(t)
    
    assert len(user.transactions) == 1
    
    # 新增自訂類別
    user.add_custom_category("旅行", is_expense=True)
    assert "旅行" in user.custom_expense_categories
    
    # 測試序列化
    d = user.to_dict()
    user2 = UserData.from_dict(d)
    assert user2.user_id == user.user_id
    assert len(user2.transactions) == 1
    
    print("   ✅ 用戶資料模型測試通過")

def test_parser_expense():
    """測試支出解析"""
    print("\n📊 測試支出解析...")
    
    test_cases = [
        ("早餐 50", 50, "飲食", "expense"),
        ("午餐 100元", 100, "飲食", "expense"),
        ("晚餐 $200", 200, "飲食", "expense"),
        ("捷運 25", 25, "交通", "expense"),
        ("計程車 150", 150, "交通", "expense"),
        ("電影 350", 350, "娛樂", "expense"),
        ("看病 500", 500, "醫療", "expense"),
    ]
    
    for text, expected_amount, expected_category, expected_type in test_cases:
        result = MessageParser.parse(text)
        assert result.success, f"解析失敗: {text}"
        assert result.amount == expected_amount, f"金額錯誤: {text} -> {result.amount}"
        assert result.category == expected_category, f"類別錯誤: {text} -> {result.category}"
        assert result.transaction_type == expected_type, f"類型錯誤: {text}"
        print(f"   ✅ '{text}' -> ${result.amount} ({result.category})")
    
    print("   ✅ 支出解析測試通過")

def test_parser_income():
    """測試收入解析"""
    print("\n💵 測試收入解析...")
    
    test_cases = [
        ("薪水 30000 收入", 30000, "income"),
        ("獎金 5000", 5000, "income"),
        ("兼職 2000 收入", 2000, "income"),
    ]
    
    for text, expected_amount, expected_type in test_cases:
        result = MessageParser.parse(text)
        assert result.success, f"解析失敗: {text}"
        assert result.amount == expected_amount, f"金額錯誤: {text}"
        assert result.transaction_type == expected_type, f"類型錯誤: {text} -> {result.transaction_type}"
        print(f"   ✅ '{text}' -> ${result.amount} (收入)")
    
    print("   ✅ 收入解析測試通過")

def test_parser_commands():
    """測試指令解析"""
    print("\n⌨️ 測試指令解析...")
    
    test_cases = [
        ("儀表板", "dashboard"),
        ("dashboard", "dashboard"),
        ("今天", "today"),
        ("本月", "this_month"),
        ("本週", "this_week"),
        ("幫助", "help"),
        ("匯出", "export"),
        ("類別", "categories"),
    ]
    
    for text, expected_command in test_cases:
        command, params = MessageParser.parse_command(text)
        assert command == expected_command, f"指令錯誤: {text} -> {command}"
        print(f"   ✅ '{text}' -> {command}")
    
    # 測試帶參數的指令
    command, params = MessageParser.parse_command("設定預算 10000")
    assert command == "set_total_budget"
    assert params.get("amount") == 10000
    print(f"   ✅ '設定預算 10000' -> {command}, amount={params.get('amount')}")
    
    command, params = MessageParser.parse_command("設定預算 飲食 3000")
    assert command == "set_category_budget"
    assert params.get("category") == "飲食"
    assert params.get("amount") == 3000
    print(f"   ✅ '設定預算 飲食 3000' -> {command}, category={params.get('category')}")
    
    print("   ✅ 指令解析測試通過")

def test_validators():
    """測試驗證函數"""
    print("\n🔍 測試驗證函數...")
    
    # 金額驗證
    valid, amount, error = validate_amount(100)
    assert valid == True
    assert amount == 100
    
    valid, amount, error = validate_amount("$1,000")
    assert valid == True
    assert amount == 1000
    
    valid, amount, error = validate_amount(-50)
    assert valid == False
    
    print("   ✅ 金額驗證測試通過")
    
    # 日期驗證
    valid, date, error = validate_date("2024-01-15")
    assert valid == True
    assert date == "2024-01-15"
    
    print("   ✅ 日期驗證測試通過")

def test_helpers():
    """測試輔助函數"""
    print("\n🛠️ 測試輔助函數...")
    
    assert format_amount(1000) == "$1,000"
    assert format_amount(1234.5, with_symbol=False) == "1,234"
    
    assert format_date("2024-01-15", "short") == "01/15"
    assert format_date("2024-01-15", "medium") == "1月15日"
    
    print("   ✅ 輔助函數測試通過")

def test_config():
    """測試配置"""
    print("\n⚙️ 測試配置...")
    
    assert len(Config.DEFAULT_EXPENSE_CATEGORIES) > 0
    assert len(Config.DEFAULT_INCOME_CATEGORIES) > 0
    assert len(Config.CATEGORY_KEYWORDS) > 0
    
    assert Emoji.MONEY == "💰"
    assert "飲食" in CATEGORY_EMOJI
    
    print("   ✅ 配置測試通過")

def main():
    """運行所有測試"""
    print("=" * 50)
    print("🧪 LINE 記帳機器人核心邏輯測試")
    print("=" * 50)
    
    try:
        test_config()
        test_transaction_model()
        test_budget_model()
        test_reminder_model()
        test_user_data_model()
        test_parser_expense()
        test_parser_income()
        test_parser_commands()
        test_validators()
        test_helpers()
        
        print("\n" + "=" * 50)
        print("✅ 所有測試通過！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
