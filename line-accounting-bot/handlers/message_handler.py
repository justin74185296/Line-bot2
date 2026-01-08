"""
訊息處理器
處理 LINE 訊息事件
"""
from typing import Optional

from models.user_data import UserData
from models.transaction import Transaction
from services.storage import StorageService
from services.parser import MessageParser, ParseResult
from services.statistics import StatisticsService
from services.reminder import ReminderService
from handlers.command_handler import CommandHandler
from config import Config, Emoji, CATEGORY_EMOJI


class MessageHandler:
    """訊息處理器"""
    
    def __init__(self, storage: StorageService):
        self.storage = storage
        self.command_handler = CommandHandler(storage)
        self.reminder_service = ReminderService()
    
    def handle_message(self, user_id: str, text: str) -> str:
        """
        處理用戶訊息
        
        Args:
            user_id: LINE 用戶 ID
            text: 訊息內容
        
        Returns:
            回覆訊息
        """
        # 取得用戶資料
        user_data = self.storage.get_user(user_id)
        
        # 檢查是否有待確認的操作
        if user_data.pending_action:
            return self._handle_pending_action(user_data, text)
        
        # 嘗試解析為指令
        command, params = MessageParser.parse_command(text)
        
        if command != 'unknown':
            return self._handle_command(user_data, command, params)
        
        # 嘗試解析為記帳訊息
        parse_result = MessageParser.parse(
            text, 
            user_data.custom_expense_categories + user_data.custom_income_categories
        )
        
        if parse_result.success:
            return self._handle_accounting(user_data, parse_result)
        
        # 無法識別
        return self._handle_unknown(text, parse_result.error_message)
    
    def _handle_pending_action(self, user_data: UserData, text: str) -> str:
        """處理待確認的操作"""
        text_lower = text.strip().lower()
        
        if text_lower in ('是', '確認', 'yes', 'y', '對', '好'):
            return self.command_handler.handle_confirm(user_data)
        elif text_lower in ('否', '取消', 'no', 'n', '不要'):
            return self.command_handler.handle_cancel(user_data)
        else:
            # 清除待確認操作，處理新訊息
            user_data.clear_pending_action()
            self.storage.save_user(user_data)
            return self.handle_message(user_data.user_id, text)
    
    def _handle_command(self, user_data: UserData, 
                       command: str, params: dict) -> str:
        """處理指令"""
        command_handlers = {
            'dashboard': lambda: self.command_handler.handle_dashboard(user_data),
            'today': lambda: self.command_handler.handle_today(user_data),
            'this_week': lambda: self.command_handler.handle_this_week(user_data),
            'this_month': lambda: self.command_handler.handle_this_month(user_data),
            'stats': lambda: self.command_handler.handle_stats(user_data, params),
            'export': lambda: self.command_handler.handle_export(user_data),
            'help': lambda: self.command_handler.handle_help(),
            'show_budget': lambda: self.command_handler.handle_show_budget(user_data),
            'set_total_budget': lambda: self.command_handler.handle_set_total_budget(
                user_data, params.get('amount', 0)
            ),
            'set_category_budget': lambda: self.command_handler.handle_set_category_budget(
                user_data, params.get('category', ''), params.get('amount', 0)
            ),
            'show_reminders': lambda: self.command_handler.handle_show_reminders(user_data),
            'set_reminder': lambda: self.command_handler.handle_set_reminder(
                user_data, 
                params.get('name', ''),
                params.get('amount', 0),
                params.get('day', 1)
            ),
            'delete_reminder': lambda: self.command_handler.handle_delete_reminder(
                user_data, params.get('reminder_id', '')
            ),
            'categories': lambda: self.command_handler.handle_show_categories(user_data),
            'add_category': lambda: self.command_handler.handle_add_category(
                user_data, params.get('category', '')
            ),
            'delete_category': lambda: self.command_handler.handle_delete_category(
                user_data, params.get('category', '')
            ),
            'clear': lambda: self.command_handler.handle_clear(user_data),
            'confirm': lambda: self.command_handler.handle_confirm(user_data),
            'cancel': lambda: self.command_handler.handle_cancel(user_data),
            'delete_transaction': lambda: self.command_handler.handle_delete_transaction(
                user_data, params.get('transaction_id', '')
            ),
            'income': lambda: self._handle_income_command(user_data, params.get('text', '')),
        }
        
        handler = command_handlers.get(command)
        
        if handler:
            return handler()
        
        return self._handle_unknown(params.get('text', ''), '')
    
    def _handle_income_command(self, user_data: UserData, text: str) -> str:
        """處理收入指令"""
        if not text:
            return (
                f"{Emoji.QUESTION} 請輸入收入金額和說明\n"
                f"例如：「收入 5000 獎金」"
            )
        
        # 強制解析為收入
        parse_result = MessageParser.parse(text + ' 收入')
        
        if parse_result.success:
            parse_result.transaction_type = 'income'
            return self._handle_accounting(user_data, parse_result)
        
        return (
            f"{Emoji.CROSS} 無法識別收入訊息\n"
            f"請使用格式：「收入 金額 說明」"
        )
    
    def _handle_accounting(self, user_data: UserData, 
                          parse_result: ParseResult) -> str:
        """處理記帳訊息"""
        # 建立交易記錄
        transaction = Transaction(
            amount=parse_result.amount,
            category=parse_result.category,
            transaction_type=parse_result.transaction_type,
            note=parse_result.note
        )
        
        # 儲存交易記錄
        user_data.add_transaction(transaction)
        self.storage.save_user(user_data)
        
        # 組裝回覆訊息
        type_str = '收入' if transaction.is_income else '支出'
        type_emoji = '📥' if transaction.is_income else '📤'
        category_emoji = CATEGORY_EMOJI.get(transaction.category, '📦')
        
        lines = [
            f"{Emoji.CHECK} 已記錄{type_str}",
            f"━━━━━━━━━━━━━━━━",
            f"{type_emoji} {category_emoji} {transaction.category}",
            f"💰 金額：${transaction.amount:,.0f}",
        ]
        
        if transaction.note:
            lines.append(f"📝 備註：{transaction.note}")
        
        lines.append(f"📅 日期：{transaction.date}")
        
        # 如果信心度低，顯示提示
        if parse_result.confidence < 0.7:
            lines.extend([
                f"",
                f"💡 自動歸類為「{transaction.category}」",
                f"如需修改，輸入「類別」查看選項",
            ])
        
        # 檢查預算警告
        budget_warning = self.reminder_service.check_budget_warning(user_data)
        if budget_warning and transaction.is_expense:
            lines.extend([
                f"",
                budget_warning
            ])
        
        # 顯示今日統計
        today_transactions = StatisticsService.get_today_transactions(user_data)
        today_totals = StatisticsService.calculate_totals(today_transactions)
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"📊 今日統計",
            f"收入：${today_totals['income']:,.0f} | "
            f"支出：${today_totals['expense']:,.0f}",
        ])
        
        return '\n'.join(lines)
    
    def _handle_unknown(self, text: str, error_message: str) -> str:
        """處理無法識別的訊息"""
        lines = [
            f"{Emoji.QUESTION} 無法識別您的訊息",
        ]
        
        if error_message:
            lines.append(f"原因：{error_message}")
        
        lines.extend([
            f"",
            f"📝 記帳格式範例：",
            f"• 「早餐 50」",
            f"• 「午餐 120 便當」",
            f"• 「薪水 30000 收入」",
            f"",
            f"💡 輸入「幫助」查看完整說明",
        ])
        
        return '\n'.join(lines)
    
    def handle_follow(self, user_id: str) -> str:
        """處理用戶加入好友事件"""
        user_data = self.storage.get_user(user_id)
        
        return (
            f"{Emoji.SPARKLE} 歡迎使用記帳機器人！\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"\n"
            f"我是您的專屬記帳小幫手 {Emoji.PIGGY}\n"
            f"幫助您輕鬆追蹤每日收支！\n"
            f"\n"
            f"📝 快速記帳\n"
            f"直接輸入「早餐 50」即可記帳\n"
            f"\n"
            f"📊 查看報表\n"
            f"輸入「儀表板」查看財務總覽\n"
            f"\n"
            f"🎯 預算管理\n"
            f"輸入「設定預算 10000」設定預算\n"
            f"\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"輸入「幫助」查看完整功能說明\n"
            f"\n"
            f"開始您的理財之旅吧！{Emoji.TROPHY}"
        )
    
    def handle_unfollow(self, user_id: str) -> None:
        """處理用戶取消好友事件"""
        # 可以選擇保留或刪除用戶資料
        # 這裡選擇保留資料，以防用戶之後重新加入
        pass
