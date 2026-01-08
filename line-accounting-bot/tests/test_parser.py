"""
測試訊息解析器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.parser import MessageParser


def test_parse_simple_expense():
    """測試簡單支出解析"""
    result = MessageParser.parse("早餐 50")
    assert result.success == True
    assert result.amount == 50
    assert result.category == "飲食"
    assert result.transaction_type == "expense"


def test_parse_expense_with_unit():
    """測試帶單位的支出解析"""
    result = MessageParser.parse("午餐 100元")
    assert result.success == True
    assert result.amount == 100
    assert result.transaction_type == "expense"
    
    result = MessageParser.parse("晚餐 $200")
    assert result.success == True
    assert result.amount == 200


def test_parse_expense_with_note():
    """測試帶備註的支出解析"""
    result = MessageParser.parse("午餐 120 便當")
    assert result.success == True
    assert result.amount == 120
    assert result.category == "飲食"


def test_parse_income():
    """測試收入解析"""
    result = MessageParser.parse("薪水 30000 收入")
    assert result.success == True
    assert result.amount == 30000
    assert result.transaction_type == "income"
    
    result = MessageParser.parse("獎金 5000")
    assert result.success == True
    assert result.transaction_type == "income"


def test_parse_transport():
    """測試交通類別解析"""
    result = MessageParser.parse("捷運 25")
    assert result.success == True
    assert result.category == "交通"
    
    result = MessageParser.parse("計程車 150")
    assert result.success == True
    assert result.category == "交通"


def test_parse_command():
    """測試指令解析"""
    command, params = MessageParser.parse_command("儀表板")
    assert command == "dashboard"
    
    command, params = MessageParser.parse_command("今天")
    assert command == "today"
    
    command, params = MessageParser.parse_command("幫助")
    assert command == "help"
    
    command, params = MessageParser.parse_command("設定預算 10000")
    assert command == "set_total_budget"
    assert params.get("amount") == 10000


def test_parse_invalid():
    """測試無效輸入"""
    result = MessageParser.parse("")
    assert result.success == False
    
    result = MessageParser.parse("沒有金額")
    assert result.success == False


if __name__ == "__main__":
    test_parse_simple_expense()
    test_parse_expense_with_unit()
    test_parse_expense_with_note()
    test_parse_income()
    test_parse_transport()
    test_parse_command()
    test_parse_invalid()
    print("✅ 所有測試通過！")
