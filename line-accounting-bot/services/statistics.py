"""
統計與報表服務
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from models.transaction import Transaction
from models.user_data import UserData
from models.budget import Budget
from config import Config, Emoji, CATEGORY_EMOJI


class StatisticsService:
    """統計服務"""
    
    @staticmethod
    def get_today_transactions(user_data: UserData) -> List[Transaction]:
        """取得今天的交易記錄"""
        today = datetime.now().strftime('%Y-%m-%d')
        return [t for t in user_data.transactions if t.date == today]
    
    @staticmethod
    def get_week_transactions(user_data: UserData) -> List[Transaction]:
        """取得本週的交易記錄"""
        today = datetime.now()
        # 計算本週一的日期
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        return [
            t for t in user_data.transactions 
            if start_date <= t.date <= end_date
        ]
    
    @staticmethod
    def get_month_transactions(user_data: UserData, 
                               year: int = None, 
                               month: int = None) -> List[Transaction]:
        """取得指定月份的交易記錄"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        month_prefix = f"{year:04d}-{month:02d}"
        
        return [
            t for t in user_data.transactions 
            if t.date.startswith(month_prefix)
        ]
    
    @staticmethod
    def get_year_transactions(user_data: UserData, 
                              year: int = None) -> List[Transaction]:
        """取得指定年份的交易記錄"""
        if year is None:
            year = datetime.now().year
        
        year_prefix = f"{year:04d}"
        
        return [
            t for t in user_data.transactions 
            if t.date.startswith(year_prefix)
        ]
    
    @staticmethod
    def calculate_totals(transactions: List[Transaction]) -> Dict[str, float]:
        """計算總收入和總支出"""
        total_income = sum(t.amount for t in transactions if t.is_income)
        total_expense = sum(t.amount for t in transactions if t.is_expense)
        
        return {
            'income': total_income,
            'expense': total_expense,
            'balance': total_income - total_expense
        }
    
    @staticmethod
    def calculate_category_stats(transactions: List[Transaction], 
                                 transaction_type: str = 'expense') -> Dict[str, Dict]:
        """
        計算各類別統計
        返回 {類別: {'amount': 金額, 'count': 筆數, 'percentage': 百分比}}
        """
        filtered = [t for t in transactions if t.transaction_type == transaction_type]
        
        if not filtered:
            return {}
        
        total = sum(t.amount for t in filtered)
        
        category_stats = defaultdict(lambda: {'amount': 0, 'count': 0, 'percentage': 0})
        
        for t in filtered:
            category_stats[t.category]['amount'] += t.amount
            category_stats[t.category]['count'] += 1
        
        # 計算百分比
        for category in category_stats:
            category_stats[category]['percentage'] = (
                category_stats[category]['amount'] / total * 100 if total > 0 else 0
            )
        
        # 按金額排序
        sorted_stats = dict(
            sorted(category_stats.items(), 
                   key=lambda x: x[1]['amount'], 
                   reverse=True)
        )
        
        return sorted_stats
    
    @staticmethod
    def get_recent_transactions(user_data: UserData, 
                                limit: int = 5) -> List[Transaction]:
        """取得最近的交易記錄"""
        # 按日期時間排序
        sorted_transactions = sorted(
            user_data.transactions,
            key=lambda t: f"{t.date} {t.time}",
            reverse=True
        )
        return sorted_transactions[:limit]
    
    @staticmethod
    def calculate_budget_status(user_data: UserData) -> Dict[str, any]:
        """
        計算預算狀態
        返回 {
            'total': {'budget': 預算, 'spent': 已花費, 'remaining': 剩餘, 'percentage': 百分比},
            'categories': {類別: {...}}
        }
        """
        budget = user_data.budget
        month_transactions = StatisticsService.get_month_transactions(user_data)
        month_expense = sum(t.amount for t in month_transactions if t.is_expense)
        
        result = {
            'total': None,
            'categories': {}
        }
        
        # 總預算狀態
        if budget.total_budget > 0:
            remaining = budget.total_budget - month_expense
            percentage = month_expense / budget.total_budget * 100
            
            result['total'] = {
                'budget': budget.total_budget,
                'spent': month_expense,
                'remaining': remaining,
                'percentage': percentage,
                'status': StatisticsService._get_budget_status(percentage)
            }
        
        # 類別預算狀態
        category_stats = StatisticsService.calculate_category_stats(month_transactions)
        
        for category, category_budget in budget.category_budgets.items():
            if category_budget > 0:
                spent = category_stats.get(category, {}).get('amount', 0)
                remaining = category_budget - spent
                percentage = spent / category_budget * 100 if category_budget > 0 else 0
                
                result['categories'][category] = {
                    'budget': category_budget,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage': percentage,
                    'status': StatisticsService._get_budget_status(percentage)
                }
        
        return result
    
    @staticmethod
    def _get_budget_status(percentage: float) -> str:
        """根據百分比取得預算狀態"""
        if percentage >= 100:
            return 'exceeded'
        elif percentage >= 80:
            return 'warning'
        else:
            return 'normal'
    
    @staticmethod
    def calculate_cash_flow_forecast(user_data: UserData) -> Dict[str, float]:
        """
        計算現金流預測
        基於本月剩餘天數和平均支出預測
        """
        today = datetime.now()
        days_in_month = (
            datetime(today.year, today.month % 12 + 1, 1) - timedelta(days=1)
        ).day if today.month < 12 else 31
        
        days_passed = today.day
        days_remaining = days_in_month - days_passed
        
        month_transactions = StatisticsService.get_month_transactions(user_data)
        totals = StatisticsService.calculate_totals(month_transactions)
        
        # 計算日均支出
        daily_expense = totals['expense'] / days_passed if days_passed > 0 else 0
        
        # 預測剩餘支出
        forecast_expense = daily_expense * days_remaining
        
        # 預測月底餘額
        budget_status = StatisticsService.calculate_budget_status(user_data)
        
        if budget_status['total']:
            remaining_budget = budget_status['total']['remaining']
            forecast_balance = remaining_budget - forecast_expense
        else:
            forecast_balance = -forecast_expense
        
        return {
            'daily_expense': daily_expense,
            'days_remaining': days_remaining,
            'forecast_expense': forecast_expense,
            'forecast_balance': forecast_balance,
            'current_expense': totals['expense'],
            'current_income': totals['income']
        }
    
    @staticmethod
    def format_dashboard(user_data: UserData) -> str:
        """格式化儀表板訊息"""
        today = datetime.now()
        month_str = today.strftime('%Y年%m月')
        
        # 本月統計
        month_transactions = StatisticsService.get_month_transactions(user_data)
        totals = StatisticsService.calculate_totals(month_transactions)
        category_stats = StatisticsService.calculate_category_stats(month_transactions)
        
        # 預算狀態
        budget_status = StatisticsService.calculate_budget_status(user_data)
        
        # 現金流預測
        forecast = StatisticsService.calculate_cash_flow_forecast(user_data)
        
        # 最近交易
        recent = StatisticsService.get_recent_transactions(user_data, 5)
        
        # 組裝訊息
        lines = [
            f"{Emoji.CHART} 個人財務儀表板",
            f"━━━━━━━━━━━━━━━━",
            f"",
            f"{Emoji.CALENDAR} {month_str}",
            f"",
            f"💵 總收入：${totals['income']:,.0f}",
            f"💸 總支出：${totals['expense']:,.0f}",
            f"💰 淨餘額：${totals['balance']:,.0f}",
        ]
        
        # 預算狀態
        if budget_status['total']:
            status = budget_status['total']
            status_emoji = (
                Emoji.CROSS if status['status'] == 'exceeded'
                else Emoji.WARNING if status['status'] == 'warning'
                else Emoji.CHECK
            )
            lines.extend([
                f"",
                f"{Emoji.TARGET} 預算狀態",
                f"預算：${status['budget']:,.0f}",
                f"已使用：${status['spent']:,.0f} ({status['percentage']:.1f}%)",
                f"剩餘：${status['remaining']:,.0f} {status_emoji}",
            ])
        
        # 現金流預測
        lines.extend([
            f"",
            f"{Emoji.GRAPH_UP} 現金流預測",
            f"日均支出：${forecast['daily_expense']:,.0f}",
            f"預計本月剩餘支出：${forecast['forecast_expense']:,.0f}",
        ])
        
        # 類別支出分析
        if category_stats:
            lines.extend([
                f"",
                f"{Emoji.CHART} 支出分析 (Top 5)",
            ])
            
            for i, (category, stats) in enumerate(list(category_stats.items())[:5]):
                emoji = CATEGORY_EMOJI.get(category, '📦')
                bar = StatisticsService._create_progress_bar(stats['percentage'])
                lines.append(
                    f"{emoji} {category}: ${stats['amount']:,.0f} ({stats['percentage']:.1f}%)"
                )
                lines.append(f"   {bar}")
        
        # 最近交易
        if recent:
            lines.extend([
                f"",
                f"{Emoji.RECEIPT} 最近交易",
            ])
            
            for t in recent:
                type_emoji = '📥' if t.is_income else '📤'
                category_emoji = CATEGORY_EMOJI.get(t.category, '📦')
                note_str = f" ({t.note})" if t.note else ""
                lines.append(
                    f"{type_emoji} {t.date[5:]} {category_emoji}{t.category} ${t.amount:,.0f}{note_str}"
                )
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"輸入「幫助」查看更多功能 {Emoji.SPARKLE}",
        ])
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_today_report(user_data: UserData) -> str:
        """格式化今日報表"""
        today = datetime.now().strftime('%Y年%m月%d日')
        transactions = StatisticsService.get_today_transactions(user_data)
        totals = StatisticsService.calculate_totals(transactions)
        
        lines = [
            f"{Emoji.CALENDAR} 今日帳務 - {today}",
            f"━━━━━━━━━━━━━━━━",
            f"",
            f"💵 收入：${totals['income']:,.0f}",
            f"💸 支出：${totals['expense']:,.0f}",
            f"💰 淨額：${totals['balance']:,.0f}",
        ]
        
        if transactions:
            lines.extend([
                f"",
                f"{Emoji.RECEIPT} 交易明細 ({len(transactions)} 筆)",
            ])
            
            for t in sorted(transactions, key=lambda x: x.time, reverse=True):
                type_emoji = '📥' if t.is_income else '📤'
                category_emoji = CATEGORY_EMOJI.get(t.category, '📦')
                note_str = f" ({t.note})" if t.note else ""
                lines.append(
                    f"{type_emoji} {t.time[:5]} {category_emoji}{t.category} ${t.amount:,.0f}{note_str}"
                )
        else:
            lines.extend([
                f"",
                f"今天還沒有任何記錄 {Emoji.SPARKLE}",
            ])
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_week_report(user_data: UserData) -> str:
        """格式化本週報表"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        week_str = f"{start_of_week.strftime('%m/%d')} - {today.strftime('%m/%d')}"
        
        transactions = StatisticsService.get_week_transactions(user_data)
        totals = StatisticsService.calculate_totals(transactions)
        category_stats = StatisticsService.calculate_category_stats(transactions)
        
        lines = [
            f"{Emoji.CALENDAR} 本週統計",
            f"📆 {week_str}",
            f"━━━━━━━━━━━━━━━━",
            f"",
            f"💵 總收入：${totals['income']:,.0f}",
            f"💸 總支出：${totals['expense']:,.0f}",
            f"💰 淨餘額：${totals['balance']:,.0f}",
            f"📝 交易筆數：{len(transactions)} 筆",
        ]
        
        if category_stats:
            lines.extend([
                f"",
                f"{Emoji.CHART} 支出分類",
            ])
            
            for category, stats in category_stats.items():
                emoji = CATEGORY_EMOJI.get(category, '📦')
                lines.append(
                    f"{emoji} {category}: ${stats['amount']:,.0f} ({stats['percentage']:.1f}%)"
                )
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_month_report(user_data: UserData, 
                           year: int = None, 
                           month: int = None) -> str:
        """格式化月度報表"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        month_str = f"{year}年{month:02d}月"
        
        transactions = StatisticsService.get_month_transactions(user_data, year, month)
        totals = StatisticsService.calculate_totals(transactions)
        category_stats = StatisticsService.calculate_category_stats(transactions)
        income_stats = StatisticsService.calculate_category_stats(transactions, 'income')
        
        lines = [
            f"{Emoji.CALENDAR} {month_str} 統計報表",
            f"━━━━━━━━━━━━━━━━",
            f"",
            f"💵 總收入：${totals['income']:,.0f}",
            f"💸 總支出：${totals['expense']:,.0f}",
            f"💰 淨餘額：${totals['balance']:,.0f}",
            f"📝 交易筆數：{len(transactions)} 筆",
        ]
        
        # 支出分類
        if category_stats:
            lines.extend([
                f"",
                f"{Emoji.CHART} 支出分類統計",
            ])
            
            for category, stats in category_stats.items():
                emoji = CATEGORY_EMOJI.get(category, '📦')
                bar = StatisticsService._create_progress_bar(stats['percentage'])
                lines.append(
                    f"{emoji} {category}"
                )
                lines.append(
                    f"   ${stats['amount']:,.0f} ({stats['percentage']:.1f}%) {stats['count']}筆"
                )
                lines.append(f"   {bar}")
        
        # 收入分類
        if income_stats:
            lines.extend([
                f"",
                f"{Emoji.BANK} 收入分類統計",
            ])
            
            for category, stats in income_stats.items():
                emoji = CATEGORY_EMOJI.get(category, '💵')
                lines.append(
                    f"{emoji} {category}: ${stats['amount']:,.0f} ({stats['percentage']:.1f}%)"
                )
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_export_csv(user_data: UserData, 
                         year: int = None, 
                         month: int = None) -> str:
        """匯出為 CSV 格式"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        transactions = StatisticsService.get_month_transactions(user_data, year, month)
        
        if not transactions:
            return "本月沒有任何交易記錄"
        
        lines = [
            f"📄 {year}年{month:02d}月 交易記錄匯出",
            f"━━━━━━━━━━━━━━━━",
            f"",
            "日期,時間,類型,類別,金額,備註"
        ]
        
        for t in sorted(transactions, key=lambda x: f"{x.date} {x.time}"):
            type_str = '收入' if t.is_income else '支出'
            note = t.note.replace(',', '，')  # 避免 CSV 格式問題
            lines.append(f"{t.date},{t.time},{type_str},{t.category},{t.amount},{note}")
        
        lines.extend([
            f"",
            f"━━━━━━━━━━━━━━━━",
            f"總計 {len(transactions)} 筆記錄",
            f"（複製以上內容存檔）"
        ])
        
        return '\n'.join(lines)
    
    @staticmethod
    def _create_progress_bar(percentage: float, length: int = 10) -> str:
        """建立進度條"""
        filled = int(percentage / 100 * length)
        filled = min(filled, length)
        empty = length - filled
        
        bar = '█' * filled + '░' * empty
        return f"[{bar}]"
