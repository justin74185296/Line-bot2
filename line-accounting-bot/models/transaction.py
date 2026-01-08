"""
交易記錄資料模型
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Transaction:
    """交易記錄"""
    amount: float
    category: str
    transaction_type: str  # 'income' 或 'expense'
    note: str = ''
    date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    time: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sub_category: Optional[str] = None
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """從字典建立物件"""
        return cls(
            amount=float(data.get('amount', 0)),
            category=data.get('category', '其他'),
            transaction_type=data.get('transaction_type', 'expense'),
            note=data.get('note', ''),
            date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
            time=data.get('time', datetime.now().strftime('%H:%M:%S')),
            transaction_id=data.get('transaction_id', str(uuid.uuid4())[:8]),
            sub_category=data.get('sub_category')
        )
    
    @property
    def datetime_obj(self) -> datetime:
        """取得 datetime 物件"""
        return datetime.strptime(f"{self.date} {self.time}", '%Y-%m-%d %H:%M:%S')
    
    @property
    def is_expense(self) -> bool:
        """是否為支出"""
        return self.transaction_type == 'expense'
    
    @property
    def is_income(self) -> bool:
        """是否為收入"""
        return self.transaction_type == 'income'
    
    def format_display(self) -> str:
        """格式化顯示"""
        type_str = '支出' if self.is_expense else '收入'
        note_str = f" ({self.note})" if self.note else ""
        return f"{self.date} | {self.category} | {type_str} ${self.amount:,.0f}{note_str}"
