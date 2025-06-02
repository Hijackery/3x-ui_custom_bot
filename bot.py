import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from config import Config
from database import Database
from xui_client import XUIClient, XUIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class VPNBot:
    def __init__(self):
        self.db = Database()
        self.xui = XUIClient()
        self.app = Application.builder().token(Config.TOKEN).build()
        self._register_handlers()
        self.app.add_error_handler(self._error_handler)

    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        handlers = [
            CommandHandler("start", self._start),
            CommandHandler("help", self._show_help),
            CallbackQueryHandler(self._callback_handler),
            CommandHandler("stats", self._stats),
            CommandHandler("speedtest", self._speedtest),
            CommandHandler("backup", self._backup),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        ]
        for handler in handlers:
            self.app.add_handler(handler)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Exception while handling update: {context.error}", exc_info=context.error)
        
        error_text = "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        if isinstance(context.error, XUIError):
            error_text = f"❌ Ошибка сервера: {str(context.error)}"
        
        try:
            if update and hasattr(update, 'message'):
                await update.message.reply_text(error_text)
            elif update and hasattr(update, 'callback_query'):
                await update.callback_query.message.reply_text(error_text)
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        if not self.db.get_user(user.id):
            self.db.add_user({
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name
            })
        
        welcome_text = (
            "🌟 Привет! 🌟\n\n"
            "Я - твой персональный помощник по настройке VPN соединения.\n\n"
            "✨ Что я умею:\n"
            "🔹 Создавать индивидуальные конфигурации\n"
            "🔹 Хранить все твои подключения\n"
            "🔹 Предоставлять инструкции для всех устройств\n\n"
            "Начни с кнопки ➕ Создать конфиг или посмотри инструкции"
        )
        
        await update.message.reply_text(welcome_text)
        await self._show_main_menu(update, is_admin=(user.id in Config.ADMIN_IDS))

    async def _show_main_menu(self, update: Update, is_admin: bool = False):
        """Отображение главного меню"""
        buttons = [
            [InlineKeyboardButton("➕ Создать конфиг", callback_data="create")],
            [InlineKeyboardButton("🗂 Мои конфиги", callback_data="list")],
            [InlineKeyboardButton("📲 Инструкции", callback_data="help")],
            [InlineKeyboardButton("❤️ Поддержать проект", callback_data="donate")],
        ]
        
        if is_admin:
            buttons.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        if update.message:
            await update.message.reply_text("🔐 VPN Manager", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text("🔐 VPN Manager", reply_markup=reply_markup)

    async def _show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать инструкции по установке"""
        instructions = (
            "📲 <b>Инструкции по установке:</b>\n\n"
            "<b>Windows:</b>\n"
            "1. Скачайте программу <a href='https://github.com/invisible-xray/invisible-man-xray/releases'>Invisible Man Xray</a>\n"
            "2. Запустите программу и нажмите 'Импорт'\n"
            "3. Вставьте ссылку на конфиг или QR-код\n"
            "4. Нажмите 'Подключиться'\n\n"
            
            "<b>macOS:</b>\n"
            "1. Установите <a href='https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690'>V2Box</a> из App Store\n"
            "2. Откройте приложение и нажмите '+'\n"
            "3. Выберите 'Импорт из буфера обмена' или 'Сканировать QR-код'\n"
            "4. Нажмите 'Подключиться'\n\n"
            
            "<b>iOS:</b>\n"
            "1. Установите <a href='https://apps.apple.com/us/app/v2raytun/id6446814690'>V2RayTun</a> из App Store\n"
            "2. Откройте приложение и нажмите '+'\n"
            "3. Выберите 'Импорт из буфера обмена' или 'Сканировать QR-код'\n"
            "4. Включите соединение\n\n"
            
            "<b>Android:</b>\n"
            "1. Установите <a href='https://play.google.com/store/apps/details?id=com.v2raytun.app'>V2RayTun</a> из Play Market\n"
            "2. Откройте приложение и нажмите '+'\n"
            "3. Выберите 'Импорт из буфера обмена' или 'Сканировать QR-код'\n"
            "4. Включите соединение\n\n"
            
            "Для создания конфига используйте кнопку '➕ Создать конфиг' в главном меню."
        )
        
        await update.message.reply_text(
            instructions,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка inline-кнопок"""
        query = update.callback_query
        await query.answer()
        
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {str(e)}")
        
        if query.data == "create":
            await self._create_config(query)
        elif query.data == "list":
            await self._list_configs(query)
        elif query.data == "help":
            await self._show_help_callback(query)
        elif query.data.startswith("delete_"):
            await self._confirm_delete(query, query.data[7:])
        elif query.data.startswith("confirm_"):
            await self._delete_config(query, query.data[8:])
        elif query.data.startswith("view_"):
            await self._show_config_details(query, query.data[5:])
        elif query.data == "donate":
            await self._show_donate_info(query)
        elif query.data == "admin":
            await self._show_admin_panel(query)
        elif query.data == "cancel":
            await self._show_main_menu(update, is_admin=(query.from_user.id in Config.ADMIN_IDS))

    async def _show_help_callback(self, query):
        """Показать инструкции по установке (для callback)"""
        instructions = (
"📚 <b>Подробное руководство по установке</b>\n\n"
            
            "🖥 <b>Для Windows:</b>\n"
            "1. Скачайте <b>Invisible Man Xray</b> по ссылке:\n"
            "   <a href='https://github.com/invisible-xray/invisible-man-xray/releases'>Скачать для Windows</a>\n"
            "2. Распакуйте архив в удобную папку\n"
            "3. Запустите файл <code>invisible-man-xray.exe</code> (может потребоваться отключить антивирус)\n"
            "4. В главном окне нажмите кнопку <b>'Импорт'</b>\n"
            "5. Вставьте ссылку на конфиг или отсканируйте QR-код\n"
            "6. Нажмите <b>'Подключиться'</b>\n"
            "7. Для автоматического запуска: ПКМ по ярлыку → Свойства → В поле 'Объект' добавьте <code>-autostart</code>\n\n"
            
            "🍎 <b>Для macOS:</b>\n"
            "1. Установите <b>V2Box</b> из App Store:\n"
            "   <a href='https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690'>Скачать V2Box</a>\n"
            "2. После установки откройте приложение\n"
            "3. Нажмите <b>'+'</b> в правом верхнем углу\n"
            "4. Выберите:\n"
            "   - <b>'Импорт из буфера обмена'</b> (если скопировали ссылку)\n"
            "   - <b>'Сканировать QR-код'</b> (используйте камеру)\n"
            "5. Нажмите <b>'Подключиться'</b>\n"
            "6. Перейдите в <b>Системные настройки → Network →</b> разрешите подключение\n\n"
            
            "📱 <b>Для iOS:</b>\n"
            "1. Установите <b>V2RayTun</b> из App Store:\n"
            "   <a href='https://apps.apple.com/us/app/v2raytun/id6446814690'>Скачать V2RayTun</a>\n"
            "2. Откройте приложение → Нажмите <b>'+'</b>\n"
            "3. Выберите способ импорта:\n"
            "   - Вставьте ссылку в поле <b>'Import from clipboard'</b>\n"
            "   - Или нажмите <b>'Scan QR Code'</b> для сканирования\n"
            "4. Нажмите <b>'Save'</b> затем переключите соединение\n"
            "5. При первом запуске разрешите <b>VPN конфигурацию</b> в всплывающем окне\n\n"
            
            "🤖 <b>Для Android:</b>\n"
            "1. Установите <b>V2RayTun</b> из Play Market:\n"
            "   <a href='https://play.google.com/store/apps/details?id=com.v2raytun.app'>Скачать V2RayTun</a>\n"
            "2. Откройте приложение → Тапните <b>'+'</b> внизу экрана\n"
            "3. Выберите:\n"
            "   - <b>'Import config from clipboard'</b> для ссылки\n"
            "   - <b>'Scan QR code'</b> для QR-кода\n"
            "4. Нажмите <b>'Save'</b> → Включите переключатель\n"
            "5. Разрешите создание VPN подключения при первом запуске\n\n"
            
            "🔧 <b>Решение проблем:</b>\n"
            "- Если подключение не работает: перезапустите клиент\n"
            "- Проверьте дату и время на устройстве\n"
            "- Обновите клиент до последней версии\n"
            "- Для Windows: добавьте исключение в антивирус\n\n"
        )
        
        await query.message.reply_text(
            instructions,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
            ])
        )

    async def _create_config(self, query):
        """Создание нового конфига"""
        user_id = query.from_user.id
        current_count = self.db.count_user_configs(user_id)
        if current_count >= Config.MAX_CONFIGS_PER_USER:
            await query.message.reply_text(
                f"❌ Достигнут лимит {Config.MAX_CONFIGS_PER_USER} конфигов!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗂 Управление конфигами", callback_data="list")]
                ])
            )
            return
        
        try:
            port = random.randint(*Config.PORT_RANGE)
            config = await self.xui.create_inbound(port)
            config_id = self.db.create_config(user_id, config)
            
            remaining = Config.MAX_CONFIGS_PER_USER - current_count - 1
            
            config_text = (
                f"✅ Конфиг успешно создан!\n\n"
                f"🔹 Порт: <code>{port}</code>\n"
                f"🔹 ID: <code>{config['uuid']}</code>\n"
                f"🔹 Имя: <code>{config['email']}</code>\n"
                f"🔹 Осталось конфигов: {remaining}\n\n"
                f"<b>Ссылка для подключения:</b>\n"
                f"<code>{config['data']}</code>\n\n"
                f"<b>Параметры для ручного ввода:</b>\n"
                f"Адрес: <code>{Config.SERVER_IP}</code>\n"
                f"Порт: <code>{port}</code>\n"
                f"ID: <code>{config['uuid']}</code>\n"
                f"Ключ: <code>{Config.PUBLIC_KEY}</code>\n"
                f"SNI: <code>{random.choice(Config.SERVER_NAMES)}</code>\n"
                f"Short ID: <code>{Config.SHORT_ID}</code>"
            )
            
            await query.message.reply_photo(
                photo=config['qr_code'],
                caption=config_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                ])
            )
        except XUIError as e:
            logger.error(f"Ошибка создания конфига: {str(e)}")
            await query.message.reply_text(
                "❌ Ошибка при создании конфига. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                ])
            )

    async def _list_configs(self, query):
        """Список конфигов пользователя"""
        configs = self.db.get_user_configs(query.from_user.id)
        if not configs:
            await query.message.reply_text(
                "У вас нет активных конфигов",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать конфиг", callback_data="create")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                ])
            )
            return
        
        buttons = []
        for config in configs:
            buttons.append([
                InlineKeyboardButton(f"👁 {config['email']}", callback_data=f"view_{config['id']}"),
                InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{config['id']}")
            ])
        
        buttons.append([InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")])
        
        await query.message.reply_text(
            "Ваши активные конфиги:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def _show_config_details(self, query, config_id):
        """Показать детали конфига с QR-кодом"""
        config = self.db.conn.execute(
            "SELECT * FROM configs WHERE id = ? AND is_active = 1",
            (config_id,)
        ).fetchone()
        
        if not config:
            await query.message.reply_text(
                "Конфиг не найден или был удален",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗂 Мои конфиги", callback_data="list")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                ])
            )
            return
        
        qr_code = self.xui._generate_qr_code(config['data'])
        
        config_text = (
            f"🔹 Конфиг: <code>{config['email']}</code>\n"
            f"🔹 Порт: <code>{config['port']}</code>\n"
            f"🔹 ID: <code>{config['uuid']}</code>\n\n"
            f"<b>Ссылка для подключения:</b>\n"
            f"<code>{config['data']}</code>\n\n"
            f"<b>Параметры для ручного ввода:</b>\n"
            f"Адрес: <code>{Config.SERVER_IP}</code>\n"
            f"Порт: <code>{config['port']}</code>\n"
            f"ID: <code>{config['uuid']}</code>\n"
            f"Ключ: <code>{Config.PUBLIC_KEY}</code>\n"
            f"SNI: <code>{random.choice(Config.SERVER_NAMES)}</code>\n"
            f"Short ID: <code>{Config.SHORT_ID}</code>"
        )
        
        await query.message.reply_photo(
            photo=qr_code,
            caption=config_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗂 Мои конфиги", callback_data="list")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
            ])
        )

    async def _show_donate_info(self, query):
        """Показать информацию для поддержки проекта"""
        donate_text = ()
        
        await query.message.reply_text(
            donate_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
            ])
        )

    async def _confirm_delete(self, query, config_id):
        """Подтверждение удаления конфига"""
        await query.message.reply_text(
            "⚠️ Вы уверены, что хотите удалить этот конфиг?",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Да", callback_data=f"confirm_{config_id}"),
                    InlineKeyboardButton("❌ Нет", callback_data="cancel")
                ]
            ])
        )

    async def _delete_config(self, query, config_id):
        """Удаление конфига"""
        try:
            configs = self.db.get_user_configs(query.from_user.id)
            target_config = next((c for c in configs if c["id"] == config_id), None)
            
            if not target_config:
                await query.message.reply_text("Конфиг не найден!")
                return
            
            success = await self.xui.delete_inbound(target_config["inbound_id"])
            if success:
                self.db.delete_config(config_id)
                remaining = Config.MAX_CONFIGS_PER_USER - self.db.count_user_configs(query.from_user.id)
                
                await query.message.reply_text(
                    f"✅ Конфиг успешно удален!\n"
                    f"🔹 Осталось конфигов: {remaining}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                    ])
                )
            else:
                await query.message.reply_text(
                    "❌ Не удалось удалить конфиг",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                    ])
                )
        except XUIError as e:
            logger.error(f"Ошибка удаления конфига: {str(e)}")
            await query.message.reply_text(
                "⚠️ Ошибка сервера при удалении",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
                ])
            )

    async def _show_admin_panel(self, query):
        """Панель администратора"""
        stats = self.db.get_detailed_stats()
        total_users = len(self.db.conn.execute("SELECT id FROM users").fetchall())
        active_configs = len(self.db.conn.execute(
            "SELECT id FROM configs WHERE is_active = 1"
        ).fetchall())
        
        await query.message.reply_text(
            f"👑 Админ-панель\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"🔗 Активных конфигов: {active_configs}\n\n"
            f"Последние регистрации:\n" + "\n".join(
                f"{row['date']}: {row['new_users']} новых"
                for row in stats[:5]
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Полная статистика", callback_data="full_stats")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="cancel")]
            ])
        )

    async def _stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика для админов"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            return
        
        stats = self.db.get_detailed_stats()
        response = ["📊 Статистика за 30 дней:\nДата | Новые пользователи"]
        response.extend(f"{row['date']} | {row['new_users']}" for row in stats)
        
        await update.message.reply_text("\n".join(response))

    async def _speedtest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Тест скорости сервера"""
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            speed = st.download() / 1_000_000  # Мбит/с
            
            await update.message.reply_text(
                f"📶 Скорость подключения: {speed:.2f} Мбит/с\n"
                f"🏠 Сервер: {st.results.server['name']}"
            )
        except ImportError:
            await update.message.reply_text("❌ Модуль speedtest-cli не установлен")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    async def _backup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создание резервной копии (для админов)"""
        if update.effective_user.id not in Config.ADMIN_IDS:
            return
        
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"vpnbot_backup_{timestamp}.db"
            
            shutil.copy2("vpnbot.db", backup_file)
            
            await update.message.reply_text(f"✅ Резервная копия создана: {backup_file}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка создания бэкапа: {str(e)}")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if update.message.text.lower() == "техработы" and update.effective_user.id in Config.ADMIN_IDS:
            await update.message.reply_text("Отправьте сообщение о техработах:")
            context.user_data["awaiting_tech_work"] = True
        elif update.effective_user.id in Config.ADMIN_IDS and context.user_data.get("awaiting_tech_work"):
            await self.notify_tech_work(update.message.text)
            await update.message.reply_text("✅ Уведомление отправлено")
            context.user_data["awaiting_tech_work"] = False

    async def notify_tech_work(self, message: str):
        """Отправка уведомления о техработах"""
        try:
            await self.app.bot.send_message(
                chat_id=Config.TECH_WORK_CHAT_ID,
                text=f"⚠️ Технические работы:\n{message}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {str(e)}")

    def run(self):
        """Запуск бота"""
        self.app.run_polling()

if __name__ == "__main__":
    bot = VPNBot()
    bot.run()
