# VPN Telegram Bot

Бот для управления VPN-конфигурациями через Telegram с интеграцией с панелью 3X-UI.

![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📌 Возможности

- Создание и управление Reality-конфигурациями
- Генерация QR-кодов для быстрого подключения
- Инструкции по настройке для всех платформ (Windows, macOS, iOS, Android)
- Админ-панель с статистикой
- Ограничение количества конфигов на пользователя

## ⚙️ Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Hijackery/vpn-telegram-bot.git
   cd vpn-telegram-bot
2. Установите зависимости:

pip install -r requirements.txt
Настройте конфигурацию:

Отредактируйте config.py (см. раздел "Конфигурация")

Для работы Reality заполните: 
PUBLIC_KEY,
PRIVATE_KEY,
SHORT_ID

Запустите бота:
python bot.py

🔧 Конфигурация
Заполните данные в config.py:
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

🛠 Технологии
Python 3.8+

python-telegram-bot - Telegram Bot API

3X-UI - Панель управления Xray

SQLite - База данных

QRCode - Генерация QR-кодов

📋 Команды
Для пользователей:
/start - Главное меню

/help - Инструкции по настройке

➕ Создать конфиг - Создать новую конфигурацию

🗂 Мои конфиги - Просмотр и управление конфигами

Для администраторов:
/stats - Статистика пользователей

👑 Админ-панель - Управление ботом

📱 Поддерживаемые платформы
Windows: Invisible Man Xray

macOS: V2Box

iOS: V2RayTun

Android: V2RayTun

📄 Лицензия
Этот проект распространяется под лицензией MIT. См. файл LICENSE для получения дополнительной информации.

Примечание: Этот бот предназначен для легального использования. Разработчик не несет ответственности за неправомерное использование данного программного обеспечения.
