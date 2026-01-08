"""
預算資料模型
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Budget:
    """預算設定"""
    total_budget: float = 0.0  # 總預算
    category_budgets: Dict[str, float] = field(default_factory=dict)  # 類別預算
    month: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m'))
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Budget':
        """從字典建立物件"""
        return cls(
            total_budget=float(data.get('total_budget', 0)),
            category_budgets=data.get('category_budgets', {}),
            month=data.get('month', datetime.now().strftime('%Y-%m'))
        )
    
    def set_total_budget(self, amount: float) -> None:
        """設定總預算"""
        self.total_budget = amount
    
    def set_category_budget(self, category: str, amount: float) -> None:
        """設定類別預算"""
        self.category_budgets[category] = amount
    
    def get_category_budget(self, category: str) -> Optional[float]:
        """取得類別預算"""
        return self.category_budgets.get(category)
    
    def remove_category_budget(self, category: str) -> bool:
        """移除類別預算"""
        if category in self.category_budgets:
            del self.category_budgets[category]
            return True
        return False
    
    def has_budget(self) -> bool:
        """是否有設定預算"""
        return self.total_budget > 0 or len(self.category_budgets) > 0
