"""
提醒資料模型
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class Reminder:
    """提醒設定"""
    name: str  # 提醒名稱（如：房租）
    amount: float  # 金額
    day_of_month: int  # 每月幾號
    reminder_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: str = '其他'
    is_active: bool = True
    last_triggered: Optional[str] = None  # 上次觸發日期
    created_at: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Reminder':
        """從字典建立物件"""
        return cls(
            name=data.get('name', ''),
            amount=float(data.get('amount', 0)),
            day_of_month=int(data.get('day_of_month', 1)),
            reminder_id=data.get('reminder_id', str(uuid.uuid4())[:8]),
            category=data.get('category', '其他'),
            is_active=data.get('is_active', True),
            last_triggered=data.get('last_triggered'),
            created_at=data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
    
    def should_trigger_today(self) -> bool:
        """今天是否應該觸發"""
        if not self.is_active:
            return False
        
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        
        # 檢查是否是指定日期
        if today.day != self.day_of_month:
            return False
        
        # 檢查今天是否已經觸發過
        if self.last_triggered == today_str:
            return False
        
        return True
    
    def mark_triggered(self) -> None:
        """標記為已觸發"""
        self.last_triggered = datetime.now().strftime('%Y-%m-%d')
    
    def format_display(self) -> str:
        """格式化顯示"""
        status = '啟用' if self.is_active else '停用'
        return f"📅 {self.name} | ${self.amount:,.0f} | 每月{self.day_of_month}號 | {status}"
