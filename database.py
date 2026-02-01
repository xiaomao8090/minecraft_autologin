import pymysql
import json
import os
from cryptography.fernet import Fernet
from datetime import datetime

class Database:
    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.port = int(os.environ.get('DB_PORT', 3306))
        self.user = os.environ.get('DB_USER', 'root')
        self.password = os.environ.get('DB_PASSWORD', '')
        self.database = os.environ.get('DB_NAME', 'minecraft_autologin')
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not set")
        self.cipher = Fernet(encryption_key.encode())
    
    def get_connection(self):
        return pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    
    def encrypt(self, text):
        if not text:
            return None
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt(self, encrypted_text):
        if not encrypted_text:
            return None
        return self.cipher.decrypt(encrypted_text.encode()).decode()
    
    def get_all_accounts(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, email, password, level, mcname, subscription, hypixel, capes, cookie_status, last_login, created_at, disabled FROM accounts")
                accounts = cursor.fetchall()
                for acc in accounts:
                    acc['password'] = self.decrypt(acc['password'])
                    acc['hypixel'] = json.loads(acc['hypixel']) if acc['hypixel'] else {}
                    acc['capes'] = json.loads(acc['capes']) if acc['capes'] else []
                return accounts
        finally:
            conn.close()
    
    def get_account(self, email):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM accounts WHERE email = %s", (email,))
                acc = cursor.fetchone()
                if acc:
                    acc['password'] = self.decrypt(acc['password'])
                    acc['hypixel'] = json.loads(acc['hypixel']) if acc['hypixel'] else {}
                    acc['capes'] = json.loads(acc['capes']) if acc['capes'] else []
                return acc
        finally:
            conn.close()
    
    def add_account(self, email, password, level=0, mcname='Unknown', subscription='', hypixel=None, capes=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO accounts (email, password, level, mcname, subscription, hypixel, capes, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (email, self.encrypt(password), level, mcname, subscription, json.dumps(hypixel or {}), json.dumps(capes or []), datetime.now()))
            conn.commit()
        finally:
            conn.close()
    
    def update_account(self, email, **kwargs):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                updates = []
                values = []
                if 'password' in kwargs:
                    updates.append("password = %s")
                    values.append(self.encrypt(kwargs['password']))
                if 'level' in kwargs:
                    updates.append("level = %s")
                    values.append(kwargs['level'])
                if 'mcname' in kwargs:
                    updates.append("mcname = %s")
                    values.append(kwargs['mcname'])
                if 'subscription' in kwargs:
                    updates.append("subscription = %s")
                    values.append(kwargs['subscription'])
                if 'hypixel' in kwargs:
                    updates.append("hypixel = %s")
                    values.append(json.dumps(kwargs['hypixel']))
                if 'capes' in kwargs:
                    updates.append("capes = %s")
                    values.append(json.dumps(kwargs['capes']))
                if 'cookie_status' in kwargs:
                    updates.append("cookie_status = %s")
                    values.append(kwargs['cookie_status'])
                if 'last_login' in kwargs:
                    updates.append("last_login = %s")
                    values.append(kwargs['last_login'])
                if 'disabled' in kwargs:
                    updates.append("disabled = %s")
                    values.append(kwargs['disabled'])
                values.append(email)
                cursor.execute(f"UPDATE accounts SET {', '.join(updates)} WHERE email = %s", values)
            conn.commit()
        finally:
            conn.close()
    
    def delete_account(self, email):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM accounts WHERE email = %s", (email,))
            conn.commit()
        finally:
            conn.close()
    
    def get_cookie(self, email):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT cookie_data FROM cookies WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result and result['cookie_data']:
                    decrypted = self.decrypt(result['cookie_data'])
                    return json.loads(decrypted)
                return None
        finally:
            conn.close()
    
    def save_cookie(self, email, cookie_data):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                encrypted = self.encrypt(json.dumps(cookie_data))
                cursor.execute("INSERT INTO cookies (email, cookie_data, updated_at) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE cookie_data = %s, updated_at = %s", (email, encrypted, datetime.now(), encrypted, datetime.now()))
            conn.commit()
        finally:
            conn.close()
    
    def delete_cookie(self, email):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM cookies WHERE email = %s", (email,))
            conn.commit()
        finally:
            conn.close()
    
    def get_all_cards(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM cards")
                return cursor.fetchall()
        finally:
            conn.close()
    
    def get_card(self, card_key):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM cards WHERE card_key = %s", (card_key,))
                return cursor.fetchone()
        finally:
            conn.close()
    
    def add_card(self, card_key, duration, duration_days, card_type='normal'):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO cards (card_key, duration, duration_days, type, created_at) VALUES (%s, %s, %s, %s, %s)", (card_key, duration, duration_days, card_type, datetime.now()))
            conn.commit()
        finally:
            conn.close()
    
    def use_card(self, card_key, expire_at):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE cards SET used = 1, used_at = %s, expire_at = %s WHERE card_key = %s", (datetime.now(), expire_at, card_key))
            conn.commit()
        finally:
            conn.close()
    
    def delete_card(self, card_key):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM cards WHERE card_key = %s", (card_key,))
            conn.commit()
        finally:
            conn.close()
    
    def verify_admin(self, username, password):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password FROM admin_users WHERE username = %s", (username,))
                result = cursor.fetchone()
                if result:
                    stored_password = self.decrypt(result['password'])
                    return stored_password == password
                return False
        finally:
            conn.close()
