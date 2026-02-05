import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo,
    ReplyKeyboardRemove
)
from aiogram.client.default import DefaultBotProperties

# ==================== НАСТРОЙКИ ====================
TOKEN = "8406827750:AAFj6wZlT0a6PKnShyXstrLZiguOddDu-VE"

CHANNEL_ID = -1002458862246
CHAT_ID = -1001790011004
THREAD_ID = 15708
# ===================================================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== КЛАВИАТУРЫ ====================
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Подготовить отчёт о рыбалке")]],
    resize_keyboard=True
)

# Функция для создания клавиатуры с кнопками "Назад" и "Начать сначала"
def get_back_kb(additional_buttons=None, include_restart=True):
    """Создает клавиатуру с кнопкой Назад и Начать сначала"""
    keyboard = []
    if additional_buttons:
        if isinstance(additional_buttons[0], list):
            keyboard.extend(additional_buttons)
        else:
            keyboard.append(additional_buttons)
    
    # Создаем строку с кнопками Назад и Начать сначала
    row = [KeyboardButton(text="◀️ Назад")]
    if include_restart:
        row.append(KeyboardButton(text="🔄 Начать сначала"))
    keyboard.append(row)
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Клавиатура для даты с кнопкой Назад
date_kb = get_back_kb([
    [KeyboardButton(text="Сегодня"), KeyboardButton(text="Вчера")],
    [KeyboardButton(text="Ввести вручную")]
])

# Клавиатура для типа водоема с кнопкой Назад
water_type_kb = get_back_kb([
    KeyboardButton(text="Платник"), 
    KeyboardButton(text="Бесплатник")
])

# Клавиатура для пропуска с кнопкой Назад
skip_kb_with_back = get_back_kb([KeyboardButton(text="Пропустить")])

# Простая клавиатура только с кнопками Назад и Начать сначала
back_kb_only = get_back_kb()

# ==================== СОСТОЯНИЯ ====================
class ReportStates(StatesGroup):
    date = State()
    water_type = State()
    place = State()
    location = State()
    catch = State()
    tackle = State()
    extra = State()
    media = State()
    preview = State()

# ==================== СЛУЖЕБНОЕ ====================
async def save_msg(state: FSMContext, message: types.Message):
    """Сохраняет ID сообщения для текущего шага"""
    data = await state.get_data()
    current_state = await state.get_state()
    
    step_messages = data.get("step_messages", {})
    step_msg_ids = step_messages.get(current_state, [])
    step_msg_ids.append(message.message_id)
    
    step_messages[current_state] = step_msg_ids
    await state.update_data(step_messages=step_messages)

async def delete_step_messages(user_id: int, state: FSMContext, step_state: str = None):
    """Удаляет сообщения определенного шага или всех шагов"""
    data = await state.get_data()
    step_messages = data.get("step_messages", {})
    media_message_ids = data.get("media_message_ids", [])
    status_msg_id = data.get("status_msg_id")
    
    deleted_count = 0
    
    # Всегда удаляем статусное сообщение если есть
    if status_msg_id:
        try:
            await bot.delete_message(user_id, status_msg_id)
            deleted_count += 1
        except:
            pass
    
    if step_state:
        # Удаляем сообщения только конкретного шага
        if step_state in step_messages:
            for mid in step_messages[step_state]:
                try:
                    await bot.delete_message(user_id, mid)
                    deleted_count += 1
                except:
                    pass
            step_messages[step_state] = []
    else:
        # Удаляем сообщения ВСЕХ шагов
        for step_state_key, msg_ids in step_messages.items():
            for mid in msg_ids:
                try:
                    await bot.delete_message(user_id, mid)
                    deleted_count += 1
                except:
                    pass
        
        # Удаляем медиа-сообщения
        for mid in media_message_ids:
            try:
                await bot.delete_message(user_id, mid)
                deleted_count += 1
            except:
                pass
        
        step_messages = {}
        media_message_ids = []
        status_msg_id = None
    
    await state.update_data(
        step_messages=step_messages, 
        media_message_ids=media_message_ids,
        status_msg_id=status_msg_id
    )
    return deleted_count

async def show_start(user_id: int, state: FSMContext = None):
    """Показывает стартовое сообщение"""
    try:
        msg = await bot.send_message(
            chat_id=user_id,
            text="🎣 **Бот отчётов о рыбалке - Славянский район**\n\n"
                 "Добро пожаловать! Этот бот помогает рыбакам делиться своими успехами в нашем районе.\n\n"
                 "📋 **Что нужно сделать:**\n\n"
                 "1️⃣ Нажмите «Подготовить отчёт о рыбалке»\n"
                 "2️⃣ Укажите дату, место и тип водоёма\n"
                 "3️⃣ Опишите ваш улов и снасти\n"
                 "4️⃣ Добавьте фото/видео\n"
                 "5️⃣ Отправьте отчёт в общий чат\n\n"
                 "📍 **Куда публикуются отчёты:**\n\n"
                 "✅ Чат «Рыбалка в Славянском районе»\n"
                 "✅ Обсуждение с участниками\n"
                 "✅ Все могут комментировать ваши успехи\n\n"
                 "⚠️ **Важно:**\n\n"
                 "📸 Фото/видео обязательны для отчёта\n"
                 "✏️ Все данные сохраняются в отчёте\n"
                 "↩️ Можно вернуться назад и исправить информацию",
            reply_markup=start_kb
        )
        if state:
            await save_msg(state, msg)
        return msg
    except:
        return None

async def update_buttons_message(user_id: int, chat_id: int, state: FSMContext, media_count: int):
    """Обновляет сообщение с кнопками"""
    data = await state.get_data()
    status_msg_id = data.get("status_msg_id")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ Предпросмотр отчёта", callback_data="preview_report")],
        [InlineKeyboardButton(text="📤 Отправить отчёт", callback_data="send_report")]
    ])
    
    # УДАЛЯЕМ старое сообщение с кнопками если есть
    if status_msg_id:
        try:
            await bot.delete_message(chat_id, status_msg_id)
        except:
            pass
    
    # Создаем НОВОЕ сообщение с кнопками
    msg = await bot.send_message(
        chat_id=chat_id,
        text=f"✅ **Загружено {media_count} медиа. Добавляйте ещё или нажмите «👁️ Предпросмотр отчёта».**",
        reply_markup=kb
    )
    
    await save_msg(state, msg)
    await state.update_data(status_msg_id=msg.message_id)
    return msg

# ==================== ОБРАБОТКА КНОПКИ "НАЗАД" ====================
@dp.message(lambda m: m.text == "◀️ Назад")
async def go_back(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    
    # Сохраняем текущее сообщение "Назад"
    await save_msg(state, message)
    
    # Определяем предыдущее состояние
    state_transitions = {
        ReportStates.date.state: None,  # Нет предыдущего, очищаем всё
        ReportStates.water_type.state: ReportStates.date.state,
        ReportStates.place.state: ReportStates.water_type.state,
        ReportStates.location.state: ReportStates.place.state,
        ReportStates.catch.state: ReportStates.location.state,
        ReportStates.tackle.state: ReportStates.catch.state,
        ReportStates.extra.state: ReportStates.tackle.state,
        ReportStates.media.state: ReportStates.extra.state,
        ReportStates.preview.state: ReportStates.media.state,
    }
    
    previous_state = state_transitions.get(current_state)
    
    if current_state == ReportStates.date.state:
        # Удаляем ВСЕ сообщения и очищаем состояние
        await delete_step_messages(user_id, state)
        await state.clear()
        await show_start(user_id, state)
        
    elif current_state == ReportStates.water_type.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.date)
        
        msg = await message.answer(
            "📅 **Дата рыбалки (обязательно):**\n\n"
            "Можете выбрать:\n"
            "• «Сегодня» – автоматически поставит текущую дату\n"
            "• «Вчера» – автоматически поставит вчерашнюю дату\n"
            "• «Ввести вручную» – напишите дату в формате ДД.ММ.ГГГГ (например, 26.01.2026)",
            reply_markup=date_kb
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.place.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.water_type)
        
        msg = await message.answer(
            "💰 **Тип водоёма (обязательно):**\n\n"
            "• Платник – платная рыбалка\n"
            "• Бесплатник – бесплатная рыбалка",
            reply_markup=water_type_kb
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.location.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.place)
        
        msg = await message.answer(
            "📍 **Укажите водоём ловли (обязательно):**\n\n"
            "Примеры:\n"
            "• Река Кубань\n"
            "• 28 канал\n"
            "• Лиман Фуртовый\n"
            "• Пруд 'Золотая рыбка'",
            reply_markup=back_kb_only
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.catch.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.location)
        
        msg = await message.answer(
            "📍 **Укажите геопозицию рыболовной точки (можно пропустить):**\n\n"
            "Можете указать:\n"
            "• Координаты точки\n"
            "• Точку на карте\n"
            "• Ориентировочное место ловли\n\n"
            "Примеры:\n"
            "• Координаты: 45.123456, 38.123456\n"
            "• Отправьте точку на карте\n"
            "• Район хутора Верхний\n\n"
            "Или нажмите «Пропустить»",
            reply_markup=skip_kb_with_back
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.tackle.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.catch)
        
        msg = await message.answer(
            "🎣 **Что поймали? (обязательно):**\n\n"
            "Можно указать количество и вес по желанию.\n\n"
            "Примеры:\n"
            "• Судак – 3 шт\n"
            "• Карп – 2 шт\n"
            "• Окунь, плотва, карась\n"
            "• Щука + окунь 5 шт",
            reply_markup=back_kb_only
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.extra.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.tackle)
        
        msg = await message.answer(
            "🪝 **Снасти и наживка (можно пропустить):**\n\n"
            "Примеры:\n"
            "• Спиннинг, плетёнка 0.14\n"
            "• Фидер, леска 0.25\n"
            "• Наживка: червь, кукуруза\n"
            "• Прикормка самодельная",
            reply_markup=skip_kb_with_back
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.media.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.extra)
        
        # Очищаем медиа из состояния
        await state.update_data(
            media=[],
            media_message_ids=[],
            status_msg_id=None,
            last_media_group=None
        )
        
        msg = await message.answer(
            "📝 **Дополнительная информация (можно пропустить):**\n\n"
            "Можно указать:\n"
            "✓ Погодные условия\n"
            "✓ Время ловли\n"
            "✓ Особенности клёва\n"
            "✓ Интересные моменты\n"
            "✓ Советы другим рыбакам\n"
            "✓ **Для платников:** цены, режим работы, удобства",
            reply_markup=skip_kb_with_back
        )
        await save_msg(state, msg)
        
    elif current_state == ReportStates.preview.state:
        # Удаляем сообщения текущего и предыдущего шагов
        await delete_step_messages(user_id, state, current_state)
        await delete_step_messages(user_id, state, previous_state)
        await state.set_state(ReportStates.media)
        
        data = await state.get_data()
        media = data.get("media", [])
        
        if media:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👁️ Предпросмотр отчёта", callback_data="preview_report")],
                [InlineKeyboardButton(text="📤 Отправить отчёт", callback_data="send_report")]
            ])
            
            msg = await message.answer(
                f"✅ **Загружено {len(media)} медиа. Добавляйте ещё или нажмите «👁️ Предпросмотр отчёта».**",
                reply_markup=kb
            )
            await save_msg(state, msg)
            await state.update_data(status_msg_id=msg.message_id)
        
    else:
        await delete_step_messages(user_id, state)
        await state.clear()
        await show_start(user_id, state)

# ==================== ОБРАБОТКА КНОПКИ "НАЧАТЬ СНАЧАЛА" ====================
@dp.message(lambda m: m.text == "🔄 Начать сначала")
async def restart_report(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Сохраняем текущее сообщение "Начать сначала"
    await save_msg(state, message)
    
    # Удаляем ВСЕ сообщения
    deleted = await delete_step_messages(user_id, state)
    print(f"🔄 Начать сначала: удалено {deleted} сообщений")
    
    # Очищаем состояние
    await state.clear()
    
    # Показываем стартовое сообщение
    await show_start(user_id, state)

# ==================== START ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await delete_step_messages(message.from_user.id, state)
    await state.clear()
    await show_start(message.from_user.id, state)

@dp.message(lambda m: m.text == "Подготовить отчёт о рыбалке")
async def start_report(message: types.Message, state: FSMContext):
    await delete_step_messages(message.from_user.id, state)
    await state.clear()
    
    await save_msg(state, message)

    msg = await message.answer(
        "📅 **Дата рыбалки (обязательно):**\n\n"
        "Можете выбрать:\n"
        "• «Сегодня» – автоматически поставит текущую дату\n"
        "• «Вчера» – автоматически поставит вчерашнюю дату\n"
        "• «Ввести вручную» – напишите дату в формате ДД.ММ.ГГГГ (например, 26.01.2026)",
        reply_markup=date_kb
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.date)

# ==================== ШАГИ ====================
@dp.message(ReportStates.date)
async def step_date(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    
    if message.text == "Сегодня":
        date_str = datetime.now().strftime("%d.%m.%Y")
        await state.update_data(date=date_str)
        await process_date_step(message, state)
        
    elif message.text == "Вчера":
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%d.%m.%Y")
        await state.update_data(date=date_str)
        await process_date_step(message, state)
        
    elif message.text == "Ввести вручную":
        msg = await message.answer(
            "✏️ Введите дату в формате ДД.ММ.ГГГГ (например: 26.01.2026):",
            reply_markup=get_back_kb([], include_restart=True)  # Только Назад и Начать сначала
        )
        await save_msg(state, msg)
        return
        
    elif not message.text.strip():
        msg = await message.answer("❌ Дата обязательна", reply_markup=date_kb)
        await save_msg(state, msg)
        return
        
    else:
        date_text = message.text.strip()
        try:
            datetime.strptime(date_text, "%d.%m.%Y")
            await state.update_data(date=date_text)
            await process_date_step(message, state)
        except ValueError:
            msg = await message.answer(
                "❌ Неверный формат даты!\n"
                "Используйте формат ДД.ММ.ГГГГ (например: 26.01.2026)",
                reply_markup=date_kb
            )
            await save_msg(state, msg)

async def process_date_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    msg = await message.answer(f"✅ Дата сохранена: {data['date']}")
    await save_msg(state, msg)
    
    msg = await message.answer(
        "💰 **Тип водоёма (обязательно):**\n\n"
        "• Платник – платная рыбалка\n"
        "• Бесплатник – бесплатная рыбалка",
        reply_markup=water_type_kb
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.water_type)

@dp.message(ReportStates.water_type)
async def step_water_type(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    
    if message.text not in ["Платник", "Бесплатник"]:
        msg = await message.answer(
            "❌ Пожалуйста, выберите один из вариантов:",
            reply_markup=water_type_kb
        )
        await save_msg(state, msg)
        return
    
    await state.update_data(water_type=message.text)
    
    msg = await message.answer("✅ Тип водоёма сохранен", reply_markup=ReplyKeyboardRemove())
    await save_msg(state, msg)
    
    msg = await message.answer(
        "📍 **Укажите водоём ловли (обязательно):**\n\n"
        "Примеры:\n"
        "• Река Кубань\n"
        "• 28 канал\n"
        "• Лиман Фуртовый\n"
        "• Пруд 'Золотая рыбка'",
        reply_markup=back_kb_only
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.place)

@dp.message(ReportStates.place)
async def step_place(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    if not message.text.strip():
        msg = await message.answer("❌ Водоём обязателен", reply_markup=back_kb_only)
        await save_msg(state, msg)
        return
    await state.update_data(place=message.text.strip())

    msg = await message.answer(
        "📍 **Укажите геопозицию рыболовной точки (можно пропустить):**\n\n"
        "Можете указать:\n"
        "• Координаты точки\n"
        "• Точку на карте\n"
        "• Ориентировочное место ловли\n\n"
        "Примеры:\n"
        "• Координаты: 45.123456, 38.123456\n"
        "• Отправьте точку на карте\n"
        "• Район хутора Верхний\n\n"
        "Или нажмите «Пропустить»",
        reply_markup=skip_kb_with_back
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.location)

@dp.message(ReportStates.location)
async def step_location(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    
    if message.text == "Пропустить":
        await state.update_data(location=None)
    else:
        await state.update_data(location=message.text.strip())
    
    msg = await message.answer(
        "🎣 **Что поймали? (обязательно):**\n\n"
        "Можно указать количество и вес по желанию.\n\n"
        "Примеры:\n"
        "• Судак – 3 шт\n"
        "• Карп – 2 шт\n"
        "• Окунь, плотва, карась\n"
        "• Щука + окунь 5 шт",
        reply_markup=back_kb_only
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.catch)

@dp.message(ReportStates.catch)
async def step_catch(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    if not message.text.strip():
        msg = await message.answer("❌ Улов обязателен", reply_markup=back_kb_only)
        await save_msg(state, msg)
        return
    await state.update_data(catch=message.text.strip())

    msg = await message.answer(
        "🪝 **Снасти и наживка (можно пропустить):**\n\n"
        "Примеры:\n"
        "• Спиннинг, плетёнка 0.14\n"
        "• Фидер, леска 0.25\n"
        "• Наживка: червь, кукуруза\n"
        "• Прикормка самодельная",
        reply_markup=skip_kb_with_back
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.tackle)

@dp.message(ReportStates.tackle)
async def step_tackle(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    await state.update_data(tackle=None if message.text == "Пропустить" else message.text)

    msg = await message.answer(
        "📝 **Дополнительная информация (можно пропустить):**\n\n"
        "Можно указать:\n"
        "✓ Погодные условия\n"
        "✓ Время ловли\n"
        "✓ Особенности клёва\n"
        "✓ Интересные моменты\n"
        "✓ Советы другим рыбакам\n"
        "✓ **Для платников:** цены, режим работы, удобства",
        reply_markup=skip_kb_with_back
    )
    await save_msg(state, msg)
    await state.set_state(ReportStates.extra)

@dp.message(ReportStates.extra)
async def step_extra(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    await save_msg(state, message)
    await state.update_data(extra=None if message.text == "Пропустить" else message.text)

    msg = await message.answer(
        "📸 **Добавьте фото или видео (обязательно):**\n\n"
        "Можно отправить:\n"
        "✅ Фото улова\n"
        "✅ Видео процесса ловли\n"
        "✅ Фото места рыбалки\n"
        "✅ Видео с поклёвкой\n\n"
        "📌 Нужно хотя бы одно фото или видео.\n"
        "📌 Можно отправить несколько файлов.",
        reply_markup=back_kb_only
    )
    await save_msg(state, msg)

    await state.update_data(
        media=[],
        status_msg_id=None,
        media_message_ids=[],
        last_media_group=None
    )
    await state.set_state(ReportStates.media)

# ==================== МЕДИА ====================
# Словарь для хранения временных данных о медиа-группах
media_group_cache = {}

@dp.message(ReportStates.media)
async def step_media(message: types.Message, state: FSMContext):
    if message.text in ["◀️ Назад", "🔄 Начать сначала"]:
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    data = await state.get_data()
    media = data.get("media", [])
    media_message_ids = data.get("media_message_ids", [])
    
    # Проверяем тип сообщения
    if message.photo or message.video:
        # Сохраняем медиа
        if message.photo:
            media.append(InputMediaPhoto(media=message.photo[-1].file_id))
        elif message.video:
            media.append(InputMediaVideo(media=message.video.file_id))
        
        media_message_ids.append(message.message_id)
        
        # Сохраняем обновленные данные
        await state.update_data(
            media=media,
            media_message_ids=media_message_ids
        )
        
        # Если это группа медиа, ждем немного чтобы получить все сообщений группы
        if message.media_group_id:
            # Добавляем в кэш
            if user_id not in media_group_cache:
                media_group_cache[user_id] = {}
            
            if message.media_group_id not in media_group_cache[user_id]:
                media_group_cache[user_id][message.media_group_id] = {
                    'count': 0,
                    'timer': None
                }
            
            media_group_cache[user_id][message.media_group_id]['count'] += 1
            
            # Устанавливаем таймер для обновления кнопок
            if media_group_cache[user_id][message.media_group_id]['timer']:
                media_group_cache[user_id][message.media_group_id]['timer'].cancel()
            
            # Ждем 0.5 секунды для получения всех сообщений группы
            timer = asyncio.create_task(
                update_buttons_after_delay(user_id, chat_id, state, len(media), message.media_group_id)
            )
            media_group_cache[user_id][message.media_group_id]['timer'] = timer
        else:
            # Одиночное медиа - сразу обновляем кнопки
            await update_buttons_message(user_id, chat_id, state, len(media))
    
    else:
        msg = await message.answer("❌ Здесь можно отправлять только фото или видео", reply_markup=back_kb_only)
        await save_msg(state, msg)
        return

async def update_buttons_after_delay(user_id: int, chat_id: int, state: FSMContext, media_count: int, media_group_id: str):
    """Обновляет кнопки после задержки для медиа-групп"""
    await asyncio.sleep(0.5)  # Ждем 0.5 секунды
    
    # Проверяем, все ли еще в кэше
    if user_id in media_group_cache and media_group_id in media_group_cache[user_id]:
        # Обновляем кнопки
        await update_buttons_message(user_id, chat_id, state, media_count)
        
        # Удаляем из кэша
        del media_group_cache[user_id][media_group_id]
        if not media_group_cache[user_id]:
            del media_group_cache[user_id]

# ==================== ПРЕДПРОСМОТР ОТЧЁТА ====================
@dp.callback_query(lambda c: c.data == "preview_report")
async def preview_report(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    
    data = await state.get_data()
    user = cb.from_user
    media = data.get("media", [])

    if not media:
        await cb.answer("❌ Нет медиа для предпросмотра!", show_alert=True)
        return

    # Формируем текст отчета для предпросмотра
    link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    text = (
        "📋 **ПРЕДПРОСМОТР ОТЧЁТА**\n\n"
        f"👤 **Автор:** {user.full_name}\n"
        f"📅 **Дата рыбалки:** {data['date']}\n"
        f"💰 **Тип водоёма:** {data.get('water_type', 'Не указано')}\n"
        f"📍 **Водоём:** {data['place']}\n"
    )
    
    if data.get("location"):
        text += f"📍 **Геопозиция:** {data['location']}\n"
    
    text += f"🎣 **Улов:** {data['catch']}\n"
    
    if data.get("tackle"):
        text += f"🪝 **Снасти/наживка:** {data['tackle']}\n"
    if data.get("extra"):
        text += f"📝 **Доп. информация:** {data['extra']}\n"
    
    text += f"\n📸 **Медиафайлов:** {len(media)}\n\n"
    text += "⚠️ **Это предпросмотр. Отчёт будет отправлен в:**\n"
    text += "✅ Чат «Рыбалка в Славянском районе»\n"
    text += "✅ Канал с отчётами\n\n"
    
    # Сначала отправляем текст предпросмотра БЕЗ кнопок
    preview_text_msg = await cb.message.answer(text)
    await save_msg(state, preview_text_msg)
    
    # Если есть медиа - отправляем медиагруппу (максимум 10 файлов в группе)
    if media:
        # Разбиваем медиа на группы по 10 (ограничение Telegram)
        media_groups = []
        for i in range(0, len(media), 10):
            media_groups.append(media[i:i+10])
        
        # Отправляем первую группу медиа с текстом
        if len(media_groups) > 0:
            # Копируем медиа для отправки
            first_group = []
            for m in media_groups[0]:
                if isinstance(m, InputMediaPhoto):
                    first_group.append(InputMediaPhoto(media=m.media))
                elif isinstance(m, InputMediaVideo):
                    first_group.append(InputMediaVideo(media=m.media))
            
            # Отправляем медиагруппу
            try:
                sent_messages = await bot.send_media_group(
                    chat_id=cb.message.chat.id,
                    media=first_group
                )
                # Сохраняем ID отправленных медиа-сообщений
                for msg in sent_messages:
                    await save_msg(state, msg)
            except Exception as e:
                print(f"⚠️ Ошибка при отправке медиагруппы: {e}")
                # Если не удалось отправить группой, отправляем по одному
                for m in media[:3]:  # Ограничиваем первым медиа для предпросмотра
                    try:
                        if isinstance(m, InputMediaPhoto):
                            msg = await bot.send_photo(
                                chat_id=cb.message.chat.id,
                                photo=m.media
                            )
                            await save_msg(state, msg)
                        elif isinstance(m, InputMediaVideo):
                            msg = await bot.send_video(
                                chat_id=cb.message.chat.id,
                                video=m.media
                            )
                            await save_msg(state, msg)
                    except:
                        pass
    
    # Теперь отправляем кнопки после медиа
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить отправку", callback_data="send_report")],
        [InlineKeyboardButton(text="✏️ Редактировать отчёт", callback_data="edit_report")]
    ])
    
    # Отправляем кнопки отдельным сообщением
    buttons_msg = await cb.message.answer("**Выберите действие:**", reply_markup=kb)
    await save_msg(state, buttons_msg)
    
    await state.set_state(ReportStates.preview)

@dp.callback_query(lambda c: c.data == "edit_report")
async def edit_report(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    
    # Возвращаем к шагу медиа
    await state.set_state(ReportStates.media)
    
    data = await state.get_data()
    media = data.get("media", [])
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ Предпросмотр отчёта", callback_data="preview_report")],
        [InlineKeyboardButton(text="📤 Отправить отчёт", callback_data="send_report")]
    ])
    
    # Удаляем старое сообщение с кнопками, если оно есть в предпросмотре
    try:
        await cb.message.delete()
    except:
        pass
    
    # Отправляем новое сообщение с кнопками
    msg = await cb.message.answer(
        f"✅ **Загружено {len(media)} медиа. Добавляйте ещё или нажмите «👁️ Предпросмотр отчёта».**",
        reply_markup=kb
    )
    await save_msg(state, msg)
    await state.update_data(status_msg_id=msg.message_id)

# ==================== ОТПРАВКА ====================
@dp.callback_query(lambda c: c.data == "send_report")
async def send_report(cb: types.CallbackQuery, state: FSMContext):
    print("✅ Функция send_report вызвана!")
    
    data = await state.get_data()
    user = cb.from_user
    print(f"✅ Пользователь: {user.id}")

    media = data.get("media", [])
    print(f"✅ Количество медиа: {len(media)}")
    
    if not media:
        await cb.answer("❌ Сначала отправьте хотя бы одно фото или видео!", show_alert=True)
        return

    link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    # Формируем финальный текст отчета С ЭМОДЗИ
    text = (
        f"👤 <b>Автор:</b> <a href='{link}'>{user.full_name}</a>\n"
        f"📅 <b>Дата рыбалки:</b> {data['date']}\n"
        f"💰 <b>Тип водоёма:</b> {data.get('water_type', 'Не указано')}\n"
        f"📍 <b>Водоём:</b> {data['place']}\n"
    )
    
    if data.get("location"):
        text += f"📍 <b>Геопозиция:</b> {data['location']}\n"
    
    text += f"🎣 <b>Улов:</b> {data['catch']}\n"
    
    if data.get("tackle"):
        text += f"🪝 <b>Снасти/наживка:</b> {data['tackle']}\n"
    if data.get("extra"):
        text += f"📝 <b>Доп. информация:</b> {data['extra']}\n"

    print(f"✅ Текст отчета подготовлен")
    
    # 1. Отправляем медиагруппу в канал
    media[0].caption = text
    try:
        sent = await bot.send_media_group(CHANNEL_ID, media)
        first_id = sent[0].message_id
        print(f"✅ Медиа отправлено в канал, ID первого сообщения: {first_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки в канал: {e}")
        await cb.answer("❌ Ошибка при отправке отчёта", show_alert=True)
        return

    channel_num = str(CHANNEL_ID)[4:]

    # Кнопки для канала (ссылка на комментарии БЕЗ ?comment=1 - для телефона)
    channel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Комментарии",
                url=f"https://t.me/c/{channel_num}/{first_id}"
            ),
            InlineKeyboardButton(
                text="📤 Отправить отчёт",
                url=f"https://t.me/{(await bot.get_me()).username}?start=from_chat"
            )
        ]
    ])
    
    try:
        await bot.edit_message_reply_markup(CHANNEL_ID, first_id, reply_markup=channel_kb)
        print(f"✅ Кнопки добавлены к сообщению в канале")
    except Exception as e:
        print(f"⚠️ Не удалось добавить кнопки в канале: {e}")

    # 2. Отправляем медиагруппу в чат С ТЕКСТОМ (с эмодзи)
    try:
        chat_media = []
        for i, m in enumerate(media):
            if isinstance(m, InputMediaPhoto):
                chat_media.append(InputMediaPhoto(media=m.media))
            elif isinstance(m, InputMediaVideo):
                chat_media.append(InputMediaVideo(media=m.media))
        
        # Добавляем текст с эмодзи к первому медиа в группе
        chat_media[0].caption = text
        
        # Отправляем медиагруппу в чат
        sent_chat = await bot.send_media_group(
            chat_id=CHAT_ID,
            media=chat_media,
            message_thread_id=THREAD_ID
        )
        chat_first_id = sent_chat[0].message_id if sent_chat else None
        print(f"✅ Медиа с текстом отправлено в чат (все {len(media)} файлов)")
        
    except Exception as e:
        print(f"⚠️ Не удалось отправить медиа в чат: {e}")
        try:
            # Пробуем отправить текстовое сообщение отдельно
            text_msg = await bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode="HTML",
                message_thread_id=THREAD_ID
            )
            print(f"✅ Текстовый отчёт отправлен в чат")
        except Exception as e2:
            print(f"❌ Не удалось отправить текст в чат: {e2}")
    
    # 3. Отправляем отдельное сообщение с кнопками в чат (с разделительной полосой 16 символов)
    print("✅ Отправляю кнопки в чат...")
    chat_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Комментарии",
                url=f"https://t.me/c/{channel_num}/{first_id}"
            ),
            InlineKeyboardButton(
                text="📤 Отправить отчёт",
                url=f"https://t.me/{(await bot.get_me()).username}?start=from_chat"
            )
        ]
    ])
    
    try:
        # Отправляем сообщение с разделительной полосой (16 символов, тонкая)
        buttons_msg = await bot.send_message(
            chat_id=CHAT_ID,
            text="────────────────",  # 16 символов тонкой полосы
            reply_markup=chat_kb,
            message_thread_id=THREAD_ID
        )
        print(f"✅ Кнопки отправлены в чат, ID: {buttons_msg.message_id}")
    except Exception as e:
        print(f"❌ Не удалось отправить кнопки в чат: {e}")

    # 4. Отправляем сообщение об успешной отправке пользователю
    print("✅ Отправляю сообщение об успехе пользователю...")
    success_msg = await bot.send_message(
        chat_id=user.id,
        text="✅ Отчёт отправлен в чат «Рыбалка в Славянском районе»."
    )
    print(f"✅ Сообщение об успехе отправлено, ID: {success_msg.message_id}")
    
    await save_msg(state, success_msg)

    # 5. Ждем 5 секунд
    print("⏳ Жду 5 секунд...")
    await asyncio.sleep(5)
    
    # 6. Удаляем ВСЕ сообщения (включая медиа)
    print("🗑️ Начинаю удаление сообщений...")
    deleted = await delete_step_messages(user.id, state)
    
    print(f"✅ Удалено {deleted} сообщений (включая медиа)")

    # 7. Показываем кнопку "Подготовить отчёт о рыбалке"
    print("🔄 Показываю кнопку 'Подготовить отчёт о рыбалке'...")
    await show_start(user.id, state)
    
    # 8. Очищаем состояние
    await state.clear()
    print("✅ Состояние очищено, бот готов к новому отчёту")

# ==================== ОБРАБОТКА НАЖАТИЯ КНОПКИ ИЗ ЧАТА ====================
@dp.message(lambda m: m.text and "/start" in m.text)
async def cmd_start_full(message: types.Message, state: FSMContext):
    # Проверяем, есть ли параметр from_chat в команде start
    if "from_chat" in message.text:
        # Если пользователь пришел из чата по кнопке
        await delete_step_messages(message.from_user.id, state)
        await state.clear()
        await show_start(message.from_user.id, state)
    else:
        # Обычный старт
        await delete_step_messages(message.from_user.id, state)
        await state.clear()
        await show_start(message.from_user.id, state)

# ==================== ЗАПУСК ====================
async def main():
    print("🤖 Бот запущен...")
    print("📊 Ожидаю сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🚀 Запуск Flask веб-сервера...")
    
    # ЗАПУСКАЕМ Flask ПЕРВЫМ и ЖДЁМ
    import threading
    import time
    
    def start_flask():
        port = int(os.environ.get("PORT", 10000))
        print(f"🌐 Flask запускается на порту {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Ждем 3 секунды чтобы Flask успел запуститься
    time.sleep(3)
    
    # Теперь запускаем бота
    print("🤖 Запуск Telegram бота...")
    asyncio.run(main())
