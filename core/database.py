# core/database.py
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
import os


class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.load_data()

    def load_data(self):
        """Загружаем данные из файла"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"users": {}, "payments": {}, "trials": {}}

    def save_data(self):
        """Сохраняем данные в файл"""
        with open(self.users_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получаем пользователя по ID"""
        return self.data["users"].get(str(user_id))

    def create_user(self, user_id: int, username: str = None):
        """Создаем нового пользователя"""
        user_data = {
            "id": user_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "trial_used": False,
            "subscription_end": None,
            "has_paid": False,
            "balance": 0
        }
        self.data["users"][str(user_id)] = user_data
        self.save_data()
        return user_data

    def set_trial_used(self, user_id: int, days: int = 3):
        """Активируем trial период"""
        user = self.get_user(user_id)
        if user:
            user["trial_used"] = True
            user["subscription_end"] = (datetime.now() + timedelta(days=days)).isoformat()
            self.save_data()
            return True
        return False

    def set_paid_subscription(self, user_id: int, days: int = 30):
        """Активируем платную подписку"""
        user = self.get_user(user_id)
        if user:
            user["has_paid"] = True
            user["subscription_end"] = (datetime.now() + timedelta(days=days)).isoformat()
            self.save_data()
            return True
        return False

    def get_user_status(self, user_id: int) -> Dict:
        """Получаем статус пользователя"""
        user = self.get_user(user_id)
        if not user:
            return {"active": False, "type": "none", "days_left": 0}

        if user["subscription_end"]:
            end_date = datetime.fromisoformat(user["subscription_end"])
            days_left = (end_date - datetime.now()).days
            if days_left > 0:
                sub_type = "trial" if not user["has_paid"] else "paid"
                return {"active": True, "type": sub_type, "days_left": days_left}

        return {"active": False, "type": "expired", "days_left": 0}

    def add_payment(self, user_id: int, amount: float, description: str):
        """Добавляем запись о платеже"""
        payment_id = f"pay_{datetime.now().timestamp()}"
        payment = {
            "id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.data["payments"][payment_id] = payment
        self.save_data()
        return payment


# Глобальный экземпляр базы данных
db = Database()