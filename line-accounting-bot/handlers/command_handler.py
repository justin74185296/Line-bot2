"""
指令處理器
處理各種指令（儀表板、統計、預算等）
"""
from typing import Optional

from models.user_data import UserData
from models.transaction import Transaction
from models.reminder import Reminder
from services.storage import StorageService
from services.statistics import StatisticsService
from services.reminder import ReminderService
from services.parser import MessageParser
from config import Config, Emoji, CATEGORY_EMOJI
from utils.validators import validate_budget, validate_reminder_day, validate_category


class CommandHandler:
    """指令處理器"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.reminder_service = ReminderService()
    
    def handle_dashboard(self, user_data: UserData) -> str:
        """處理儀表板指令"""
        return StatisticsService.format_dashboard(user_data)
    
    def handle_today(self, user_data: UserData) -> str:
        """處理今日報表指令"""
        return StatisticsService.format_today_report(user_data)
    
    def handle_this_week(self, user_data: UserData) -> str:
        """處理本週報表指令"""
        return StatisticsService.format_week_report(user_data)
    
    def handle_this_month(self, user_data: UserData) -> str:
        """處理本月報表指令"""
        return StatisticsService.format_month_report(user_data)
    
    def handle_stats(self, user_data: UserData, params: dict) -> str:
        """處理統計指令"""
        year = params.get('year')
        month = params.get('month')
        
        return StatisticsService.format_month_report(user_data, year, month)
    
    def handle_export(self, user_data: UserData) -> str:
        """處理匯出指令"""
        return StatisticsService.format_export_csv(user_data)
    
    def handle_help(self) -> str:
        """處理幫助指令"""
        return (
            f"{Emoji.INFO} 記帳機器人使用說明\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"\n"
            f"{Emoji.MONEY} 記帳方式\n"
            f"直接輸入文字即可記帳：\n"
            f"• 「早餐 50」\n"
            f"• 「午餐 120 便當」\n"
            f"• 「交通 $80」\n"
            f"• 「薪水 30000 收入」\n"
            f"\n"
            f"{Emoji.CHART} 查詢指令\n"
            f"• 「儀表板」- 個人財務總覽\n"
            f"• 「今天」- 今日收支明細\n"
            f"• 「本週」- 本週統計\n"
            f"• 「本月」- 本月統計\n"
            f"• 「統計 2024/01」- 指定月份\n"
            f"\n"
            f"{Emoji.TARGET} 預算管理\n"
            f"• 「預算」- 查看預算\n"
            f"• 「設定預算 10000」- 設定總預算\n"
            f"• 「設定預算 飲食 3000」- 類別預算\n"
            f"\n"
            f"{Emoji.BELL} 提醒功能\n"
            f"• 「提醒」- 查看提醒\n"
            f"• 「設定提醒 房租 10000 每月25日」\n"
            f"\n"
            f"{Emoji.RECEIPT} 類別管理\n"
            f"• 「類別」- 查看所有類別\n"
            f"• 「新增類別 旅行」\n"
            f"• 「刪除類別 旅行」\n"
            f"\n"
            f"📤 其他功能\n"
            f"• 「匯出」- 匯出本月CSV\n"
            f"• 「清空」- 清除所有資料\n"
            f"• 「幫助」- 顯示此說明\n"
            f"\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💡 小技巧：輸入金額和關鍵字，\n"
            f"機器人會自動判斷類別！"
        )
    
    def handle_show_budget(self, user_data: UserData) -> str:
        """處理顯示預算指令"""
        budget = user_data.budget
        budget_status = StatisticsService.calculate_budget_status(user_data)
        
        lines = [
            f"{Emoji.TARGET} 預算設定",
            f"━━━━━━━━━━━━━━━━",
        ]
        
        # 總預算
        if budget.total_budget > 0:
            status = budget_status.get('total', {})
            status_emoji = (
                Emoji.CROSS if status.get('status') == 'exceeded'
                else Emoji.WARNING if status.get('status') == 'warning'
                else Emoji.CHECK
            )
            
            lines.extend([
                f"",
                f"💰 每月總預算：${budget.total_budget:,.0f}",
                f"   已使用：${status.get('spent', 0):,.0f} ({status.get('percentage', 0):.1f}%)",
                f"   剩餘：${status.get('remaining', 0):,.0f} {status_emoji}",
            ])
        else:
            lines.extend([
                f"",
                f"💰 尚未設定總預算",
                f"   輸入「設定預算 10000」來設定",
            ])
        
        # 類別預算
        if budget.category_budgets:
            lines.extend([
                f"",
                f"📊 類別預算：",
            ])
            
            for category, amount in budget.category_budgets.items():
                cat_status = budget_status.get('categories', {}).get(category, {})
                emoji = CATEGORY_EMOJI.get(category, '📦')
                status_emoji = (
                    Emoji.CROSS if cat_status.get('status') == 'exceeded'
                    else Emoji.WARNING if cat_status.get('status') == 'warning'
                    else Emoji.CHECK
                )
                
                lines.append(
                    f"   {emoji} {category}: ${amount:,.0f} "
                    f"(已用 ${cat_status.get('spent', 0):,.0f}) {status_emoji}"
                )
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"設定方式：",
            f"「設定預算 金額」- 總預算",
            f"「設定預算 類別 金額」- 類別預算",
        ])
        
        return '\n'.join(lines)
    
    def handle_set_total_budget(self, user_data: UserData, amount: float) -> str:
        """處理設定總預算指令"""
        is_valid, error = validate_budget(amount)
        
        if not is_valid:
            return f"{Emoji.CROSS} {error}"
        
        user_data.budget.set_total_budget(amount)
        self.storage.save_user(user_data)
        
        return (
            f"{Emoji.CHECK} 已設定每月總預算\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 預算金額：${amount:,.0f}\n"
            f"\n"
            f"當支出達到 80% 時會提醒您 {Emoji.BELL}"
        )
    
    def handle_set_category_budget(self, user_data: UserData, 
                                   category: str, amount: float) -> str:
        """處理設定類別預算指令"""
        is_valid, error = validate_budget(amount)
        
        if not is_valid:
            return f"{Emoji.CROSS} {error}"
        
        # 檢查類別是否存在
        all_categories = user_data.get_all_expense_categories(
            Config.DEFAULT_EXPENSE_CATEGORIES
        )
        
        if category not in all_categories:
            return (
                f"{Emoji.CROSS} 找不到類別「{category}」\n"
                f"可用類別：{', '.join(all_categories)}"
            )
        
        user_data.budget.set_category_budget(category, amount)
        self.storage.save_user(user_data)
        
        emoji = CATEGORY_EMOJI.get(category, '📦')
        
        return (
            f"{Emoji.CHECK} 已設定 {emoji}{category} 類別預算\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💰 預算金額：${amount:,.0f}"
        )
    
    def handle_show_reminders(self, user_data: UserData) -> str:
        """處理顯示提醒指令"""
        return self.reminder_service.format_reminders_list(user_data)
    
    def handle_set_reminder(self, user_data: UserData, 
                           name: str, amount: float, day: int) -> str:
        """處理設定提醒指令"""
        is_valid, error = validate_reminder_day(day)
        
        if not is_valid:
            return f"{Emoji.CROSS} {error}"
        
        reminder = self.reminder_service.create_reminder(
            user_data, name, amount, day
        )
        self.storage.save_user(user_data)
        
        return (
            f"{Emoji.CHECK} 已設定帳單提醒\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📝 名稱：{name}\n"
            f"💰 金額：${amount:,.0f}\n"
            f"📅 提醒日期：每月 {day} 號\n"
            f"🆔 ID：{reminder.reminder_id}\n"
            f"\n"
            f"到期當天會自動提醒您 {Emoji.BELL}"
        )
    
    def handle_delete_reminder(self, user_data: UserData, 
                               reminder_id: str) -> str:
        """處理刪除提醒指令"""
        if not reminder_id:
            return (
                f"{Emoji.QUESTION} 請指定要刪除的提醒 ID\n"
                f"輸入「提醒」查看所有提醒的 ID"
            )
        
        success = self.reminder_service.delete_reminder(user_data, reminder_id)
        
        if success:
            self.storage.save_user(user_data)
            return f"{Emoji.CHECK} 已刪除提醒 {reminder_id}"
        else:
            return f"{Emoji.CROSS} 找不到提醒 {reminder_id}"
    
    def handle_show_categories(self, user_data: UserData) -> str:
        """處理顯示類別指令"""
        expense_categories = user_data.get_all_expense_categories(
            Config.DEFAULT_EXPENSE_CATEGORIES
        )
        income_categories = user_data.get_all_income_categories(
            Config.DEFAULT_INCOME_CATEGORIES
        )
        
        lines = [
            f"{Emoji.CHART} 類別管理",
            f"━━━━━━━━━━━━━━━━",
            f"",
            f"💸 支出類別：",
        ]
        
        for cat in expense_categories:
            emoji = CATEGORY_EMOJI.get(cat, '📦')
            is_custom = cat in user_data.custom_expense_categories
            custom_tag = " (自訂)" if is_custom else ""
            lines.append(f"   {emoji} {cat}{custom_tag}")
        
        lines.extend([
            f"",
            f"💵 收入類別：",
        ])
        
        for cat in income_categories:
            emoji = CATEGORY_EMOJI.get(cat, '💵')
            is_custom = cat in user_data.custom_income_categories
            custom_tag = " (自訂)" if is_custom else ""
            lines.append(f"   {emoji} {cat}{custom_tag}")
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"• 新增：「新增類別 名稱」",
            f"• 刪除：「刪除類別 名稱」",
        ])
        
        return '\n'.join(lines)
    
    def handle_add_category(self, user_data: UserData, 
                           category: str, is_expense: bool = True) -> str:
        """處理新增類別指令"""
        if not category:
            return (
                f"{Emoji.QUESTION} 請指定類別名稱\n"
                f"例如：「新增類別 旅行」"
            )
        
        is_valid, error = validate_category(category)
        
        if not is_valid:
            return f"{Emoji.CROSS} {error}"
        
        # 檢查是否已存在
        all_categories = (
            user_data.get_all_expense_categories(Config.DEFAULT_EXPENSE_CATEGORIES)
            if is_expense else
            user_data.get_all_income_categories(Config.DEFAULT_INCOME_CATEGORIES)
        )
        
        if category in all_categories:
            return f"{Emoji.WARNING} 類別「{category}」已存在"
        
        success = user_data.add_custom_category(category, is_expense)
        
        if success:
            self.storage.save_user(user_data)
            type_str = "支出" if is_expense else "收入"
            return f"{Emoji.CHECK} 已新增{type_str}類別「{category}」"
        else:
            return f"{Emoji.CROSS} 新增類別失敗"
    
    def handle_delete_category(self, user_data: UserData, 
                               category: str, is_expense: bool = True) -> str:
        """處理刪除類別指令"""
        if not category:
            return (
                f"{Emoji.QUESTION} 請指定類別名稱\n"
                f"例如：「刪除類別 旅行」"
            )
        
        # 檢查是否為預設類別
        default_categories = (
            Config.DEFAULT_EXPENSE_CATEGORIES if is_expense 
            else Config.DEFAULT_INCOME_CATEGORIES
        )
        
        if category in default_categories:
            return f"{Emoji.CROSS} 無法刪除預設類別「{category}」"
        
        success = user_data.remove_custom_category(category, is_expense)
        
        if success:
            self.storage.save_user(user_data)
            return f"{Emoji.CHECK} 已刪除類別「{category}」"
        else:
            return f"{Emoji.CROSS} 找不到自訂類別「{category}」"
    
    def handle_clear(self, user_data: UserData) -> str:
        """處理清空資料指令（第一次詢問確認）"""
        user_data.set_pending_action('clear_all', {})
        self.storage.save_user(user_data)
        
        return (
            f"{Emoji.WARNING} 確定要清空所有資料嗎？\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"這將刪除：\n"
            f"• 所有交易記錄\n"
            f"• 預算設定\n"
            f"• 提醒設定\n"
            f"• 自訂類別\n"
            f"\n"
            f"⚠️ 此操作無法復原！\n"
            f"\n"
            f"輸入「確認」執行清空\n"
            f"輸入「取消」取消操作"
        )
    
    def handle_confirm(self, user_data: UserData) -> str:
        """處理確認操作"""
        if not user_data.pending_action:
            return f"{Emoji.QUESTION} 沒有待確認的操作"
        
        action_type = user_data.pending_action.get('type')
        
        if action_type == 'clear_all':
            user_data.clear_all_data()
            self.storage.save_user(user_data)
            
            return (
                f"{Emoji.CHECK} 已清空所有資料\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"您可以開始重新記帳了 {Emoji.SPARKLE}"
            )
        
        user_data.clear_pending_action()
        return f"{Emoji.QUESTION} 未知的操作類型"
    
    def handle_cancel(self, user_data: UserData) -> str:
        """處理取消操作"""
        if not user_data.pending_action:
            return f"{Emoji.INFO} 沒有待取消的操作"
        
        user_data.clear_pending_action()
        self.storage.save_user(user_data)
        
        return f"{Emoji.CHECK} 已取消操作"
    
    def handle_delete_transaction(self, user_data: UserData, 
                                  transaction_id: str) -> str:
        """處理刪除交易記錄指令"""
        if not transaction_id:
            # 顯示最近的交易讓用戶選擇
            recent = StatisticsService.get_recent_transactions(user_data, 5)
            
            if not recent:
                return f"{Emoji.INFO} 沒有交易記錄可以刪除"
            
            lines = [
                f"{Emoji.RECEIPT} 最近的交易記錄",
                f"━━━━━━━━━━━━━━━━",
                f"",
            ]
            
            for t in recent:
                type_emoji = '📥' if t.is_income else '📤'
                lines.append(
                    f"{type_emoji} {t.date} {t.category} ${t.amount:,.0f}\n"
                    f"   🆔 {t.transaction_id}"
                )
            
            lines.extend([
                f"",
                f"━━━━━━━━━━━━━━━━",
                f"輸入「刪除 [ID]」刪除記錄",
            ])
            
            return '\n'.join(lines)
        
        success = user_data.remove_transaction(transaction_id)
        
        if success:
            self.storage.save_user(user_data)
            return f"{Emoji.CHECK} 已刪除交易記錄 {transaction_id}"
        else:
            return f"{Emoji.CROSS} 找不到交易記錄 {transaction_id}"
