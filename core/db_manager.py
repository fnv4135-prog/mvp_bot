# core/db_manager.py
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path="portfolio_bots.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Создаём таблицы при первом запуске"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей и их режимов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                current_mode TEXT DEFAULT 'subscription',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица для логов действий (для демо аналитики)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                bot_mode TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица для демо-данных бота подписок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_type TEXT,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")

    def get_user_mode(self, user_id: int) -> str:
        """Получить текущий режим бота для пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT current_mode FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()

        return result[0] if result else "subscription"

    def set_user_mode(self, user_id: int, username: str, mode: str):
        """Установить режим бота для пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли пользователь
        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,)
        )

        if cursor.fetchone():
            # Обновляем существующего
            cursor.execute(
                "UPDATE users SET current_mode = ?, last_activity = ?, username = ? WHERE user_id = ?",
                (mode, datetime.now().isoformat(), username, user_id)
            )
        else:
            # Создаём нового
            cursor.execute(
                "INSERT INTO users (user_id, username, current_mode, last_activity) VALUES (?, ?, ?, ?)",
                (user_id, username, mode, datetime.now().isoformat())
            )

        conn.commit()
        conn.close()

    def log_action(self, user_id: int, action_type: str, bot_mode: str, details: str = ""):
        """Логируем действие пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO user_actions 
               (user_id, action_type, bot_mode, details) 
               VALUES (?, ?, ?, ?)''',
            (user_id, action_type, bot_mode, details)
        )

        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику пользователя (для демо)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Количество действий по ботам
        cursor.execute('''
            SELECT bot_mode, COUNT(*) as count 
            FROM user_actions 
            WHERE user_id = ? 
            GROUP BY bot_mode
        ''', (user_id,))

        bot_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # Последняя активность
        cursor.execute(
            "SELECT last_activity FROM users WHERE user_id = ?",
            (user_id,)
        )
        last_activity = cursor.fetchone()

        conn.close()

        return {
            "bot_usage": bot_stats,
            "last_activity": last_activity[0] if last_activity else None,
            "total_actions": sum(bot_stats.values())
        }


# Глобальный экземпляр
db_manager = DatabaseManager()