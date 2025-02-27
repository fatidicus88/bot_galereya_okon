import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# Настройки
TOKEN = "7280451699:AAGHCaZSVWn7SEG9405gAjvDEilAWpdPdqY"
IMAGE_PATH = os.path.abspath("G:/fatidicus_ii_bot/images/start.png")  # Приветственная картинка
BALANCE58_IMAGE = os.path.abspath("G:/fatidicus_ii_bot/images/balans58.png")  # Картинка продукта "Баланс 58"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.db")
MANAGER_ID = 533725804  # Заменить на реальный ID менеджера

# Инициализация бота и базы данных
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для временного хранения выбора аксессуаров
user_accessories = {}

# Функция для инициализации базы данных
def init_db():
    try:
        print(f"Используемая база данных: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Логируем создание таблицы
        print("Создание таблицы user_selections...")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_selections (
            user_id INTEGER PRIMARY KEY,
            installation_location TEXT,
            temperature TEXT,
            noise_level TEXT,
            sunlight_preference TEXT,
            security_preference TEXT,
            accessories TEXT,
            phone_number TEXT
        )""")

        # Проверяем, есть ли колонка security_preference, если нет — добавляем
        cursor.execute("PRAGMA table_info(user_selections)")
        existing_columns = [column[1] for column in cursor.fetchall()]

        if "security_preference" not in existing_columns:
            print("Добавляем колонку security_preference в базу данных...")
            cursor.execute("ALTER TABLE user_selections ADD COLUMN security_preference TEXT")
        
        conn.commit()
        print("Таблица user_selections создана или уже существует.")
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        conn.close()

# Функция для сохранения данных пользователя
def save_user_data(user_id, column, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Сначала создаем запись, если ее нет
    cursor.execute("""
        INSERT OR IGNORE INTO user_selections (user_id) VALUES (?)
    """, (user_id,))

    # Затем обновляем нужный столбец
    cursor.execute(f"UPDATE user_selections SET {column} = ? WHERE user_id = ?", (value, user_id))

    conn.commit()
    conn.close()


# Функция для получения данных пользователя
def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT installation_location, temperature, noise_level, sunlight_preference, security_preference, accessories
        FROM user_selections WHERE user_id = ?
    """, (user_id,))
    
    user_data = cursor.fetchone()
    conn.close()

    if user_data is None:
        print(f"⚠ Данные пользователя {user_id} не найдены в базе!")
        return None

    print(f"✅ Данные пользователя {user_id}: {user_data}")  # Отладка
    return user_data

# Обработчик команды /start
@dp.message(Command("start"))
async def start_cmd(message: Message):
    if os.path.exists(IMAGE_PATH):
        await message.answer_photo(FSInputFile(IMAGE_PATH))
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать подбор", callback_data="start_selection")]
        ]
    )
    
    await message.answer(
        "Здравствуйте!\n\n"
        "Это чат-бот, который поможет Вам подобрать идеальное окно!\n\n"
        "Наша команда разработала алгоритм, который позволит вам за пару минут узнать, какое окно максимально соответствует Вашим потребностям.\n\n"
        "А еще Вы получите дополнительную скидку в подарок!",
        reply_markup=keyboard
    )

# Обработчик кнопки "Начать подбор"
@dp.callback_query(lambda c: c.data == "start_selection")
async def ask_premises_type(callback: CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Жилое помещение", callback_data="residential")],
            [InlineKeyboardButton(text="Нежилое (баня/гараж/склад)", callback_data="non_residential")]
        ]
    )
    await callback.message.answer("Ваше окно будет установлено в жилое помещение?", reply_markup=keyboard)

# Обработчик выбора типа помещения (Жилое)
@dp.callback_query(lambda c: c.data == "residential")
async def handle_residential(callback: CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="В квартиру", callback_data="apartment")],
            [InlineKeyboardButton(text="В коттедж", callback_data="cottage")],
            [InlineKeyboardButton(text="На дачу", callback_data="dacha")]
        ]
    )
    await callback.message.answer("Начнем наше путешествие к Вашему идеальному окну! 🪟\n\nКуда Вы планируете его установить?", reply_markup=keyboard)

# Обработчик выбора типа помещения (Нежилое)
@dp.callback_query(lambda c: c.data == "non_residential")
async def handle_non_residential(callback: CallbackQuery):
    await callback.answer()
    await bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    await asyncio.sleep(2)
    
    product_text = (
        "Здесь мне есть что предложить сразу, без долгих разговоров!\n\n"
        "🔹 Баланс 58 \n\n"
        "💰 Стоимость - от 10 706 рублей*\n\n"
        "*Цена указана за двухстворчатое окно (1300×1400 мм) с одной поворотно-откидной створкой, без установки и доставки.\n\n"
        "✅ Трехкамерный профиль класса «Б» шириной 58 мм (соответствует ГОСТ 23166-99).\n"
        "✅ Однокамерный стеклопакет – оптимальный выбор по цене и качеству.\n"
        "✅ Фурнитура эконом-сегмента (2 точки прижима – достаточно для работы окна)."
    )
    
    await callback.message.answer(product_text)
    
    if os.path.exists(BALANCE58_IMAGE):
        await callback.message.answer_photo(FSInputFile(BALANCE58_IMAGE))
    
    await asyncio.sleep(2)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Записаться на замер", callback_data="schedule_measurement")],
            [InlineKeyboardButton(text="Покажи вариант поэффективнее", callback_data="better_option")],
            [InlineKeyboardButton(text="Пройти подбор заново", callback_data="restart")]
        ]
    )
    
    await callback.message.answer(
        "🤖 Хотите, запишу вас на бесплатный (по городу) замер?\n\n"
        "Это Вас ни к чему не обяжет!\n\n"
        "А еще я подарю Вам скидку и подарок!\n\n"
        "Или могу предложить Вам вариант чуть дороже, но эффективнее",
        reply_markup=keyboard
    )

# Обработчик выбора места установки окна
@dp.callback_query(lambda c: c.data in ["apartment", "cottage", "dacha"])
async def handle_installation_location(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    
    choices = {
        "apartment": "в квартиру",
        "cottage": "в коттедж",
        "dacha": "на дачу"
    }
    user_choice = choices.get(callback.data, "неизвестное место")
    
    # Сохраняем выбор в базу
    save_user_data(callback.from_user.id, "installation_location", user_choice)
    
    await callback.message.answer(f"🤖 Фиксирую *бип-бип*\n\nСтавим окно {user_choice}\n\nИдем дальше!")
    
    # Вопрос про температуру
    temperature_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Зимой холодно", callback_data="cold_winter")],
            [InlineKeyboardButton(text="Летом жарко", callback_data="hot_summer")],
            [InlineKeyboardButton(text="Зимой холодно, а летом жарко", callback_data="cold_and_hot")],
            [InlineKeyboardButton(text="Комфортно круглый год", callback_data="comfortable")]
        ]
    )
    await callback.message.answer("Главней всего - погода в доме! 🌈☀☔\n\nКак обстоят дела с температурой у вас дома?", reply_markup=temperature_keyboard)

# Обработчик выбора температуры в доме
@dp.callback_query(lambda c: c.data in ["cold_winter", "hot_summer", "cold_and_hot", "comfortable"])
async def handle_temperature_choice(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    temperature_choices = {
        "cold_winter": "Зимой холодно",
        "hot_summer": "Летом жарко",
        "cold_and_hot": "Зимой холодно, а летом жарко",
        "comfortable": "Комфортно круглый год"
    }
    user_temperature = temperature_choices.get(callback.data, "неизвестный вариант")

    # Сохраняем выбор в базу
    save_user_data(callback.from_user.id, "temperature", user_temperature)

    await callback.message.answer(f"🤖 Записал!\n\nУ вас {user_temperature}\n\nИдем дальше!")

    # Вопрос про шум
    noise_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, очень шумно!", callback_data="very_noisy")],
            [InlineKeyboardButton(text="Шум небольшой, но все равно мешает", callback_data="some_noise")],
            [InlineKeyboardButton(text="Нет, у нас очень тихое местечко", callback_data="quiet_place")]
        ]
    )
    await callback.message.answer(
        "Даже роботы знают, что для комфортной и уютной обстановки в доме важно отсутствие постороннего шума с улицы. 🔈🔈🔈\n\n"
        "Если Ваши окна выходят на оживленную дорогу или детскую площадку, Вы понимаете о чем речь.\n\n"
        "Подскажите, беспокоит ли Вас шум с улицы?", reply_markup=noise_keyboard)

# Обработчик выбора уровня шума
@dp.callback_query(lambda c: c.data in ["very_noisy", "some_noise", "quiet_place"])
async def handle_noise_choice(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    
    noise_choices = {
        "very_noisy": "Да, очень шумно!",
        "some_noise": "Шум небольшой, но все равно мешает",
        "quiet_place": "Нет, у нас очень тихое местечко"
    }
    user_noise = noise_choices.get(callback.data)

    # Сохраняем выбор
    save_user_data(callback.from_user.id, "noise_level", user_noise)

    await callback.message.answer(f"🤖 *бииип* \n\nПишу: \"{user_noise}\"\n\nЯ почти понял, какое окно Вам предложить!")

    # Вопрос про солнце
    sunlight_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, интересно", callback_data="sunlight_yes")],
            [InlineKeyboardButton(text="Нет, солнце мне совершенно не мешает", callback_data="sunlight_no")]
        ]
    )
    await callback.message.answer(
        "☀ Витамин Д очень полезен для здоровья!\n\n"
        "Однако, если Ваши окна выходят на солнечную сторону, то жарким летом это может доставлять неудобства и дискомфорт.\n\n"
        "Решить эту проблему позволяет мультифункциональный стеклопакет.\n\n"
        "Скажите, Вам было бы интересно такое предложение?",
        reply_markup=sunlight_keyboard
    )

# Обработчик выбора солнцезащиты
@dp.callback_query(lambda c: c.data in ["sunlight_yes", "sunlight_no"])
async def handle_sunlight_choice(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    sunlight_choices = {
        "sunlight_yes": "Да, интересно",
        "sunlight_no": "Нет, солнце мне совершенно не мешает"
    }
    user_sunlight = sunlight_choices.get(callback.data)

    # Сохраняем выбор
    save_user_data(callback.from_user.id, "sunlight_preference", user_sunlight)

    await asyncio.sleep(1)
    await callback.message.answer("🤖 Так, это я зафиксировал!\n\nМы почти у цели!")

    # Вопрос про безопасность
    security_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="security_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="security_no")]
        ]
    )
    await callback.message.answer(
        "🏰 Мой дом - моя крепость!\n\n"
        "Мы всегда хотим чувствовать себя дома в полной безопасности. У нас есть отличное предложение по дополнительной защите от взлома. "
        "Это особенно актуально для владельцев загородных домов и жителей первых этажей.\n\n"
        "Скажите, Вам это интересно?",
        reply_markup=security_keyboard
    )

# Обработчик выбора безопасности
@dp.callback_query(lambda c: c.data in ["security_yes", "security_no"])
async def handle_security_choice(callback: CallbackQuery):
    await callback.answer()

    security_choices = {
        "security_yes": "Да",
        "security_no": "Нет"
    }
    user_security = security_choices.get(callback.data, "неизвестный вариант")

    # Сохраняем выбор в базу
    save_user_data(callback.from_user.id, "security_preference", user_security)

    await asyncio.sleep(1)
    await callback.message.answer("🤖 Отлично, теперь давайте выберем аксессуары для Вашего окна!")
    
    # Переход к выбору аксессуаров
    await ask_accessories(callback)

# Функция для выбора аксессуаров
async def ask_accessories(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    user_accessories[user_id] = []  # Очищаем список аксессуаров

    await send_accessories_keyboard(callback.message, user_id)

async def send_accessories_keyboard(message, user_id):
    """Формирование и отправка клавиатуры с выбором аксессуаров."""
    accessories_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=("✅" if "Москитная сетка" in user_accessories[user_id] else "☑") + " Москитная сетка",
                callback_data="acc_mosquito")],
            [InlineKeyboardButton(
                text=("✅" if "Подоконник" in user_accessories[user_id] else "☑") + " Подоконник",
                callback_data="acc_windowsill")],
            [InlineKeyboardButton(
                text=("✅" if "Откосы" in user_accessories[user_id] else "☑") + " Откосы",
                callback_data="acc_slopes")],
            [InlineKeyboardButton(
                text=("✅" if "Детский замок" in user_accessories[user_id] else "☑") + " Детский замок",
                callback_data="acc_child_lock")],
            [InlineKeyboardButton(
                text=("✅" if "Система ступенчатого проветривания" in user_accessories[user_id] else "☑") +
                     " Система ступенчатого проветривания",
                callback_data="acc_ventilation")],
            [InlineKeyboardButton(
                text=("✅" if "Ничего не нужно" in user_accessories[user_id] else "☑") + " Ничего не нужно",
                callback_data="acc_nothing")],
            [InlineKeyboardButton(text="✔ Подтвердить", callback_data="confirm_accessories")]
        ]
    )

    await message.answer(
        "🔹 Выберите аксессуары для Вашего окна (можно выбрать несколько):",
        reply_markup=accessories_keyboard
    )

# Обработчик выбора аксессуаров
@dp.callback_query(lambda c: c.data.startswith("acc_"))
async def handle_accessory_choice(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    if user_id not in user_accessories:
        user_accessories[user_id] = []

    accessory_mapping = {
        "acc_mosquito": "Москитная сетка",
        "acc_windowsill": "Подоконник",
        "acc_slopes": "Откосы",
        "acc_child_lock": "Детский замок",
        "acc_ventilation": "Система ступенчатого проветривания",
        "acc_nothing": "Ничего не нужно"
    }

    chosen_accessory = accessory_mapping.get(callback.data)

    # Если выбрали "Ничего не нужно", сбрасываем все другие выборы
    if callback.data == "acc_nothing":
        user_accessories[user_id] = ["Ничего не нужно"]
    else:
        if chosen_accessory in user_accessories[user_id]:
            user_accessories[user_id].remove(chosen_accessory)
        else:
            # Если выбрано "Ничего не нужно", убираем его
            if "Ничего не нужно" in user_accessories[user_id]:
                user_accessories[user_id].remove("Ничего не нужно")
            user_accessories[user_id].append(chosen_accessory)

    # Обновляем клавиатуру с выбором аксессуаров
    await callback.message.delete()
    await send_accessories_keyboard(callback.message, user_id)

# Обработчик подтверждения аксессуаров
@dp.callback_query(lambda c: c.data == "confirm_accessories")
async def confirm_accessories(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    selected_accessories = user_accessories.get(user_id, [])

    if not selected_accessories:
        selected_accessories = ["Ничего не выбрано"]

    # Сохраняем в базу данных
    save_user_data(user_id, "accessories", ", ".join(selected_accessories))

    await callback.message.answer("✅ Ваши аксессуары сохранены! Теперь подберу для вас идеальное окно...")
    
    # Переход к подбору окна
    await show_selected_window(callback)

# Функция для подбора окна
async def show_selected_window(callback: CallbackQuery):
    user_id = callback.from_user.id
    selected_window = select_window(user_id)
    
    if selected_window:
        # Отправляем описание окна
        await callback.message.answer(
            f"🤖 Вот что я подобрал для Вас:\n\n"
            f"🔹 {selected_window['name']}\n\n"
            f"{selected_window['description']}"
        )

        # Получаем путь к изображению
        image_path = os.path.join(os.path.dirname(__file__), "images", selected_window["image"])

        # Проверяем, существует ли файл
        if os.path.exists(image_path):
            print("✅ Файл найден, отправляем фото...")
            await callback.message.answer_photo(FSInputFile(image_path))
        else:
            print("❌ Файл не найден! Проверьте путь.")
            await callback.message.answer("⚠ Не удалось найти изображение продукта. Возможно, файл отсутствует.")

        # Предложение записаться на замер или пройти подбор заново
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Записаться на замер", callback_data="schedule_measurement")],
                [InlineKeyboardButton(text="Пройти подбор заново", callback_data="restart")]
            ]
        )
        await callback.message.answer(
            "🤖 Хотите записаться на бесплатный замер или пройти подбор заново?",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer("🤖 К сожалению, я не смог подобрать окно по вашим критериям.")

# Функция для подбора окна на основе данных пользователя
def select_window(user_id):
    """Функция подбирает окно на основе выбора пользователя."""
    print(f"Используемая база данных: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем данные пользователя
    cursor.execute("""
        SELECT installation_location, temperature, noise_level, sunlight_preference, security_preference
        FROM user_selections WHERE user_id = ?
    """, (user_id,))
    
    user_data = cursor.fetchone()
    conn.close()

    if not user_data:
        return None  # Если данных нет, возвращаем None

    installation_location, temperature, noise_level, sunlight_preference, security_preference = user_data

    # Логируем полученные данные
    print(f"Данные пользователя {user_id}:")
    print(f"Место установки: {installation_location}")
    print(f"Температура: {temperature}")
    print(f"Уровень шума: {noise_level}")
    print(f"Солнцезащита: {sunlight_preference}")
    print(f"Безопасность: {security_preference}")

    # --- Подбор окна по критериям ---

    # 🔹 Премиум 70 (высший приоритет)
    # Условие: "Да, интересно" для солнцезащиты
    if sunlight_preference == "Да, интересно":
        return {
            "name": "Премиум 70",
            "description": (
                "Премиум 70 - окно премиум-класса для квартир и загородных домов. "
                "✅ Пятикамерный профиль класса «А» (гарантия 40 лет). "
                "✅ Двухкамерный мультифункциональный стеклопакет (тепло+шумоизоляция). "
                "✅ Австрийская фурнитура со встроенной системой климат-контроля."
                "\n\n💰 Цена: от 14 923 рублей."
            ),
            "image": "premium70.png"
        }

    # 🔹 Комфорт-лайт 58
    # Условие: "квартира" или "дача", "Комфортно круглый год", "тихое местечко", "солнце не мешает", "нет" для безопасности
    if (installation_location in ["в квартиру", "на дачу"] and
        temperature == "Комфортно круглый год" and
        noise_level == "Нет, у нас очень тихое местечко" and
        sunlight_preference == "Нет, солнце мне совершенно не мешает" and
        security_preference == "Нет"):
        return {
            "name": "Комфорт-лайт 58",
            "description": (
                "Комфорт-лайт 58 - экономичный вариант для квартир и дач. "
                "✅ Трехкамерный профиль класса «Б». "
                "✅ Однокамерный стеклопакет (оптимально для теплых домов). "
                "✅ Немецкая фурнитура с микровентиляцией."
                "\n\n💰 Цена: от 11 939 рублей."
            ),
            "image": "komfortlite58.jpg"
        }

    # 🔹 Комфорт 58 (во всех остальных случаях)
    return {
        "name": "Комфорт 58",
        "description": (
            "Комфорт 58 - отличное окно для квартиры или дачи. "
            "✅ Трехкамерный профиль класса «А» (гарантия 40 лет). "
            "✅ Двухкамерный энергосберегающий стеклопакет. "
            "✅ Немецкая фурнитура с микровентиляцией."
            "\n\n💰 Цена: от 14 553 рублей."
        ),
        "image": "comfort58.png"
    }

# Обработчик кнопки "Пройти подбор заново"
@dp.callback_query(lambda c: c.data == "restart")
async def restart_selection(callback: CallbackQuery):
    await callback.answer()
    await start_cmd(callback.message)

# Обработчик кнопки "Записаться на замер"
@dp.callback_query(lambda c: c.data == "schedule_measurement")
async def schedule_measurement(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🤖 Отлично, записываю Вас на замер!\n\n"
        "Кстати, как обещал - дарю Вам дополнительную скидку 3% на Ваш заказ! 😊 Ваш промокод - \"Робот\". Сообщите его менеджеру."
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await callback.message.answer("Отправьте мне Ваш номер телефона (внизу кнопка).", reply_markup=keyboard)

# Обработчик получения номера телефона
@dp.message(lambda message: message.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number

    # Сохраняем номер телефона в базу
    save_user_data(user_id, "phone_number", phone_number)

    # Получаем данные пользователя
    user_data = get_user_data(user_id)

    if not user_data:
        await message.answer("Ошибка! Не удалось получить ваши данные.")
        return

    installation_location, temperature, noise_level, sunlight_preference, security_preference, accessories = user_data

     # Если аксессуары пустые, подставляем "Не выбрано"
    accessories_text = accessories if accessories else "Не выбрано"

    # Формируем сообщение для менеджера
    manager_message = (
        f"🔔 **Новая заявка на замер!**\n\n"
        f"👤 **Пользователь ID:** {user_id}\n"
        f"🏠 **Место установки:** {installation_location}\n"
        f"🌡 **Температура:** {temperature}\n"
        f"🔊 **Уровень шума:** {noise_level}\n"
        f"☀ **Солнцезащита:** {sunlight_preference}\n"
        f"🔒 **Безопасность:** {security_preference}\n"
        f"🛠 **Аксессуары:** {accessories_text}\n"
        f"📞 **Номер телефона:** {phone_number}"
    )

    # Отправляем сообщение менеджеру
    await bot.send_message(MANAGER_ID, manager_message)

    # Подтверждаем пользователю, что заявка отправлена
    await message.answer("✅ Ваш номер телефона сохранен. Менеджер скоро с вами свяжется!")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())