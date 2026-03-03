import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class Database:
    _instance = None

    def __init__(self):
        self.connection = None
        self.connect()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            print("✅ Подключение к MySQL успешно")
        except Error as e:
            print(f"❌ Ошибка подключения: {e}")
            raise

    def get_cursor(self):
        if not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
