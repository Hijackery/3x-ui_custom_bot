import os

class Config:
    # Telegram
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    ADMIN_IDS = [123456789]  # Ваш Telegram ID
    TECH_WORK_CHAT_ID = -100123456  # Чат для уведомлений
    
    # 3X-UI
    XUI_URL = "http://your-xui-panel.com:54321"
    XUI_LOGIN = "admin"
    XUI_PASSWORD = "your_password"
    
    # Reality
    PUBLIC_KEY = "your_public_key"
    PRIVATE_KEY = "your_private_key"
    SHORT_ID = "your_short_id"
    SERVER_NAMES = ["www.google.com", "www.cloudflare.com"]
    
    # Server
    SERVER_IP = "your.server.ip"
    DOMAIN = "yourdomain.com"
    
    # Limits
    MAX_CONFIGS_PER_USER = 10
    PORT_RANGE = (30000, 40000)
    DEFAULT_FLOW = "xtls-rprx-vision"
    DEFAULT_EXPIRE_DAYS = 0

config = Config()
