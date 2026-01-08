"""
提醒服務
處理預算警告和帳單提醒
"""
from typing import List, Dict, Optional
from datetime import datetime
import threading
import time

from models.user_data import UserData
from models.reminder import Reminder
from config import Config, Emoji


class ReminderService:
    """提醒服務"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._line_bot_api = None
        self._storage = None
        self._scheduler_running = False
        self._initialized = True
    
    def set_dependencies(self, line_bot_api, storage):
        """設定依賴"""
        self._line_bot_api = line_bot_api
        self._storage = storage
    
    def check_budget_warning(self, user_data: UserData) -> Optional[str]:
        """
        檢查預算警告
        返回警告訊息，如果沒有警告則返回 None
        """
        from services.statistics import StatisticsService
        
        budget_status = StatisticsService.calculate_budget_status(user_data)
        
        warnings = []
        
        # 檢查總預算
        if budget_status['total']:
            status = budget_status['total']
            
            if status['status'] == 'exceeded':
                warnings.append(
                    f"{Emoji.CROSS} 本月總預算已超支！\n"
                    f"預算：${status['budget']:,.0f}\n"
                    f"已支出：${status['spent']:,.0f}\n"
                    f"超支：${-status['remaining']:,.0f}"
                )
            elif status['status'] == 'warning':
                warnings.append(
                    f"{Emoji.WARNING} 本月預算已使用 {status['percentage']:.1f}%\n"
                    f"剩餘預算：${status['remaining']:,.0f}\n"
                    f"請注意控制支出！"
                )
        
        # 檢查類別預算
        for category, status in budget_status['categories'].items():
            if status['status'] == 'exceeded':
                warnings.append(
                    f"{Emoji.CROSS} {category} 類別預算已超支！\n"
                    f"預算：${status['budget']:,.0f}\n"
                    f"已支出：${status['spent']:,.0f}"
                )
            elif status['status'] == 'warning':
                warnings.append(
                    f"{Emoji.WARNING} {category} 類別預算已使用 {status['percentage']:.1f}%"
                )
        
        if warnings:
            return '\n\n'.join(warnings)
        
        return None
    
    def get_due_reminders(self, user_data: UserData) -> List[Reminder]:
        """取得今天到期的提醒"""
        return [r for r in user_data.reminders if r.should_trigger_today()]
    
    def format_reminder_notification(self, reminder: Reminder) -> str:
        """格式化提醒通知"""
        return (
            f"{Emoji.BELL} 帳單提醒\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📝 {reminder.name}\n"
            f"💰 金額：${reminder.amount:,.0f}\n"
            f"📅 每月 {reminder.day_of_month} 號到期\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"記得處理這筆帳單喔！{Emoji.SPARKLE}"
        )
    
    def format_reminders_list(self, user_data: UserData) -> str:
        """格式化提醒列表"""
        reminders = user_data.reminders
        
        if not reminders:
            return (
                f"{Emoji.BELL} 提醒設定\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"目前沒有設定任何提醒\n\n"
                f"設定方式：\n"
                f"「設定提醒 房租 10000 每月25日」"
            )
        
        lines = [
            f"{Emoji.BELL} 提醒設定",
            f"━━━━━━━━━━━━━━━━",
            f"",
        ]
        
        for r in reminders:
            status_emoji = Emoji.CHECK if r.is_active else Emoji.CROSS
            lines.append(
                f"{status_emoji} {r.name}\n"
                f"   💰 ${r.amount:,.0f} | 每月{r.day_of_month}號\n"
                f"   ID: {r.reminder_id}"
            )
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"刪除提醒：「刪除提醒 [ID]」"
        ])
        
        return '\n'.join(lines)
    
    def create_reminder(self, user_data: UserData, 
                       name: str, amount: float, day: int, 
                       category: str = '其他') -> Reminder:
        """建立新提醒"""
        reminder = Reminder(
            name=name,
            amount=amount,
            day_of_month=day,
            category=category
        )
        
        user_data.add_reminder(reminder)
        
        return reminder
    
    def delete_reminder(self, user_data: UserData, 
                       reminder_id: str) -> bool:
        """刪除提醒"""
        return user_data.remove_reminder(reminder_id)
    
    def send_push_notification(self, user_id: str, message: str) -> bool:
        """發送推播通知"""
        if not self._line_bot_api:
            print("LINE Bot API 未設定")
            return False
        
        try:
            from linebot.v3.messaging import TextMessage, PushMessageRequest
            
            self._line_bot_api.push_message(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )
            return True
        except Exception as e:
            print(f"發送推播通知失敗: {e}")
            return False
    
    def check_and_send_reminders(self) -> int:
        """
        檢查並發送所有到期提醒
        返回發送的通知數量
        """
        if not self._storage:
            return 0
        
        sent_count = 0
        users = self._storage.get_users_with_reminders()
        
        for user_id, user_data in users.items():
            due_reminders = self.get_due_reminders(user_data)
            
            for reminder in due_reminders:
                message = self.format_reminder_notification(reminder)
                
                if self.send_push_notification(user_id, message):
                    reminder.mark_triggered()
                    sent_count += 1
            
            # 儲存更新（提醒已觸發狀態）
            if due_reminders:
                self._storage.save_user(user_data)
        
        return sent_count
    
    def check_and_send_budget_warnings(self) -> int:
        """
        檢查並發送預算警告
        返回發送的通知數量
        """
        if not self._storage:
            return 0
        
        sent_count = 0
        users = self._storage.get_users_with_budget()
        
        for user_id, user_data in users.items():
            warning = self.check_budget_warning(user_data)
            
            if warning:
                # 檢查今天是否已經發送過
                today = datetime.now().strftime('%Y-%m-%d')
                last_warning = user_data.settings.get('last_budget_warning_date')
                
                if last_warning != today:
                    if self.send_push_notification(user_id, warning):
                        user_data.settings['last_budget_warning_date'] = today
                        self._storage.save_user(user_data)
                        sent_count += 1
        
        return sent_count


# 全域提醒服務實例
reminder_service = ReminderService()
