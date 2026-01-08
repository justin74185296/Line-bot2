"""
資料儲存服務
使用 JSON 文件儲存，支援 Replit 環境
"""
import os
import json
import threading
from typing import Optional, Dict
from datetime import datetime

from models.user_data import UserData
from config import Config


class StorageService:
    """資料儲存服務 - 使用 JSON 文件"""
    
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
        
        self._data_dir = Config.DATA_DIR
        self._users_file = os.path.join(self._data_dir, 'users.json')
        self._cache: Dict[str, UserData] = {}
        self._file_lock = threading.Lock()
        
        # 確保資料目錄存在
        os.makedirs(self._data_dir, exist_ok=True)
        
        # 載入現有資料
        self._load_all_data()
        
        self._initialized = True
    
    def _load_all_data(self) -> None:
        """載入所有用戶資料"""
        try:
            if os.path.exists(self._users_file):
                with open(self._users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        self._cache[user_id] = UserData.from_dict(user_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"載入資料時發生錯誤: {e}")
            self._cache = {}
    
    def _save_all_data(self) -> None:
        """儲存所有用戶資料"""
        with self._file_lock:
            try:
                data = {user_id: user_data.to_dict() 
                        for user_id, user_data in self._cache.items()}
                
                # 先寫入臨時文件，再重命名（原子操作）
                temp_file = self._users_file + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                os.replace(temp_file, self._users_file)
            except IOError as e:
                print(f"儲存資料時發生錯誤: {e}")
    
    def get_user(self, user_id: str) -> UserData:
        """取得用戶資料，若不存在則建立新用戶"""
        if user_id not in self._cache:
            self._cache[user_id] = UserData(user_id=user_id)
            self._save_all_data()
        else:
            # 更新最後活動時間
            self._cache[user_id].update_last_active()
        
        return self._cache[user_id]
    
    def save_user(self, user_data: UserData) -> None:
        """儲存用戶資料"""
        self._cache[user_data.user_id] = user_data
        self._save_all_data()
    
    def delete_user(self, user_id: str) -> bool:
        """刪除用戶資料"""
        if user_id in self._cache:
            del self._cache[user_id]
            self._save_all_data()
            return True
        return False
    
    def get_all_users(self) -> Dict[str, UserData]:
        """取得所有用戶資料"""
        return self._cache.copy()
    
    def user_exists(self, user_id: str) -> bool:
        """檢查用戶是否存在"""
        return user_id in self._cache
    
    def get_users_with_reminders(self) -> Dict[str, UserData]:
        """取得有設定提醒的用戶"""
        return {
            user_id: user_data 
            for user_id, user_data in self._cache.items() 
            if user_data.reminders
        }
    
    def get_users_with_budget(self) -> Dict[str, UserData]:
        """取得有設定預算的用戶"""
        return {
            user_id: user_data 
            for user_id, user_data in self._cache.items() 
            if user_data.budget.has_budget()
        }
    
    def backup_data(self) -> str:
        """備份資料，返回備份檔案路徑"""
        backup_file = os.path.join(
            self._data_dir, 
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with self._file_lock:
            try:
                data = {user_id: user_data.to_dict() 
                        for user_id, user_data in self._cache.items()}
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                return backup_file
            except IOError as e:
                print(f"備份資料時發生錯誤: {e}")
                return ''


# 全域儲存服務實例
storage = StorageService()
