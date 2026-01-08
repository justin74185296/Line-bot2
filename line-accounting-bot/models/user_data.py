"""
用戶資料模型
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from .transaction import Transaction
from .budget import Budget
from .reminder import Reminder


@dataclass
class UserData:
    """用戶資料"""
    user_id: str
    transactions: List[Transaction] = field(default_factory=list)
    budget: Budget = field(default_factory=Budget)
    reminders: List[Reminder] = field(default_factory=list)
    custom_expense_categories: List[str] = field(default_factory=list)
    custom_income_categories: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    last_active: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    settings: Dict = field(default_factory=dict)
    pending_action: Optional[Dict] = None  # 待確認的操作
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            'user_id': self.user_id,
            'transactions': [t.to_dict() for t in self.transactions],
            'budget': self.budget.to_dict(),
            'reminders': [r.to_dict() for r in self.reminders],
            'custom_expense_categories': self.custom_expense_categories,
            'custom_income_categories': self.custom_income_categories,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'settings': self.settings,
            'pending_action': self.pending_action
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserData':
        """從字典建立物件"""
        return cls(
            user_id=data.get('user_id', ''),
            transactions=[Transaction.from_dict(t) for t in data.get('transactions', [])],
            budget=Budget.from_dict(data.get('budget', {})),
            reminders=[Reminder.from_dict(r) for r in data.get('reminders', [])],
            custom_expense_categories=data.get('custom_expense_categories', []),
            custom_income_categories=data.get('custom_income_categories', []),
            created_at=data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            last_active=data.get('last_active', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            settings=data.get('settings', {}),
            pending_action=data.get('pending_action')
        )
    
    def add_transaction(self, transaction: Transaction) -> None:
        """新增交易記錄"""
        self.transactions.append(transaction)
        self.update_last_active()
    
    def remove_transaction(self, transaction_id: str) -> bool:
        """刪除交易記錄"""
        for i, t in enumerate(self.transactions):
            if t.transaction_id == transaction_id:
                del self.transactions[i]
                return True
        return False
    
    def add_reminder(self, reminder: Reminder) -> None:
        """新增提醒"""
        self.reminders.append(reminder)
    
    def remove_reminder(self, reminder_id: str) -> bool:
        """刪除提醒"""
        for i, r in enumerate(self.reminders):
            if r.reminder_id == reminder_id:
                del self.reminders[i]
                return True
        return False
    
    def add_custom_category(self, category: str, is_expense: bool = True) -> bool:
        """新增自訂類別"""
        if is_expense:
            if category not in self.custom_expense_categories:
                self.custom_expense_categories.append(category)
                return True
        else:
            if category not in self.custom_income_categories:
                self.custom_income_categories.append(category)
                return True
        return False
    
    def remove_custom_category(self, category: str, is_expense: bool = True) -> bool:
        """刪除自訂類別"""
        if is_expense:
            if category in self.custom_expense_categories:
                self.custom_expense_categories.remove(category)
                return True
        else:
            if category in self.custom_income_categories:
                self.custom_income_categories.remove(category)
                return True
        return False
    
    def get_all_expense_categories(self, default_categories: List[str]) -> List[str]:
        """取得所有支出類別（預設 + 自訂）"""
        return default_categories + self.custom_expense_categories
    
    def get_all_income_categories(self, default_categories: List[str]) -> List[str]:
        """取得所有收入類別（預設 + 自訂）"""
        return default_categories + self.custom_income_categories
    
    def update_last_active(self) -> None:
        """更新最後活動時間"""
        self.last_active = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def set_pending_action(self, action_type: str, data: dict) -> None:
        """設定待確認操作"""
        self.pending_action = {
            'type': action_type,
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def clear_pending_action(self) -> None:
        """清除待確認操作"""
        self.pending_action = None
    
    def clear_all_data(self) -> None:
        """清除所有資料"""
        self.transactions = []
        self.budget = Budget()
        self.reminders = []
        self.custom_expense_categories = []
        self.custom_income_categories = []
        self.pending_action = None
