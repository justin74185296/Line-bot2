"""
測試統計服務
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from models.user_data import UserData
from models.transaction import Transaction
from services.statistics import StatisticsService


def create_test_user():
    """建立測試用戶資料"""
    user = UserData(user_id="test_user")
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 新增測試交易
    user.add_transaction(Transaction(
        amount=50,
        category="飲食",
        transaction_type="expense",
        note="早餐",
        date=today
    ))
    
    user.add_transaction(Transaction(
        amount=100,
        category="飲食",
        transaction_type="expense",
        note="午餐",
        date=today
    ))
    
    user.add_transaction(Transaction(
        amount=80,
        category="交通",
        transaction_type="expense",
        date=today
    ))
    
    user.add_transaction(Transaction(
        amount=30000,
        category="薪水",
        transaction_type="income",
        date=today
    ))
    
    return user


def test_calculate_totals():
    """測試計算總額"""
    user = create_test_user()
    transactions = StatisticsService.get_today_transactions(user)
    totals = StatisticsService.calculate_totals(transactions)
    
    assert totals['income'] == 30000
    assert totals['expense'] == 230  # 50 + 100 + 80
    assert totals['balance'] == 29770


def test_calculate_category_stats():
    """測試類別統計"""
    user = create_test_user()
    transactions = StatisticsService.get_today_transactions(user)
    stats = StatisticsService.calculate_category_stats(transactions)
    
    assert "飲食" in stats
    assert stats["飲食"]["amount"] == 150  # 50 + 100
    assert stats["飲食"]["count"] == 2
    
    assert "交通" in stats
    assert stats["交通"]["amount"] == 80
    assert stats["交通"]["count"] == 1


def test_get_recent_transactions():
    """測試取得最近交易"""
    user = create_test_user()
    recent = StatisticsService.get_recent_transactions(user, 3)
    
    assert len(recent) == 3


def test_format_dashboard():
    """測試儀表板格式化"""
    user = create_test_user()
    dashboard = StatisticsService.format_dashboard(user)
    
    assert "儀表板" in dashboard
    assert "總收入" in dashboard
    assert "總支出" in dashboard


if __name__ == "__main__":
    test_calculate_totals()
    test_calculate_category_stats()
    test_get_recent_transactions()
    test_format_dashboard()
    print("✅ 所有統計測試通過！")
