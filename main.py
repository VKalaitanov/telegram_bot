# -*- coding: utf-8 -*-


import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputTextMessageContent, InlineQuery, \
    InlineQueryResultArticle, ContentTypes, ChatType
import aiosqlite
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import types

API_TOKEN = 'token'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
# Создаем хранилище для состояний
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Определение состояния для получения отзыва
class FeedbackForm(StatesGroup):
    Feedback = State()


# Database setup
DATABASE = 'start_users.db'


async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS start_user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                telegram_id INTEGER UNIQUE
            )
        ''')
        await db.commit()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Путь к файлу с изображением
    # image_path = 'home\\ruvds-user\\tickets\\1.jpg'
    image_path = '1.jpg'
    # Отправка изображения с подписью и кнопками
    with open(image_path, 'rb') as photo:
        await message.reply_photo(
            photo,
            caption=f"🙋Привет, {message.from_user.first_name}!\n\n🤖Я официальный бот поддержки клиентов магазина *StickerWay*. \n\n🆘Я создан для того чтобы помогать Вам.\n\n👇Здесь Вы можете:\n\n"
                    "🏷️ - Ознакомиться со всеми видами наших наклеек и этикеток\n"
                    "📦 - Заказать наклейки напрямую у производителя\n"
                    "📰 - Узнать о новостях и новинках\n"
                    "📑 - Просмотреть инструкции и полезные материалы по работе с этикетками\n"
                    "❓ - Задать вопрос представителю Бренда\n"
                    "📝 - Написать нам, если у вас есть проблема с нашими товарами",
            reply_markup=InlineKeyboardMarkup().row(
                InlineKeyboardButton('📚 Каталог', callback_data='catalog'),
                InlineKeyboardButton('🛠️ Поддержка', callback_data='support')
            ).row(
                InlineKeyboardButton('📰 Новости', url='https://t.me/sticker_way/24')
            ).row(
                InlineKeyboardButton('🛒 Ozon', url='https://www.ozon.ru/brand/stickerway-101097965/'),
                InlineKeyboardButton('🛍️ Wildberries', url='https://www.wildberries.ru/brands/868382-StickerWay')
            )
        )


@dp.callback_query_handler(lambda c: c.data == 'about_us')
async def about_us_callback(callback_query: types.CallbackQuery):
    about_us_text = (
        "🏷️ *StickerWay* - ваш надежный партнер в мире этикеток и наклеек!\n\n"
        "Мы - магазин, который не просто продает этикетки, мы создаем истории, подчеркиваем индивидуальность "
        "и помогаем вашему бизнесу процветать.\n\n"
        "Наши продукты соответствуют самым высоким стандартам качества и доступны по привлекательным ценам.\n\n"
        "Выбирая *StickerWay*, вы получаете:\n"
        "✅ Широкий ассортимент этикеток для любых нужд\n"
        "✅ Персонализированный сервис и консультации экспертов\n"
        "✅ Гарантию качества и быструю доставку\n\n"
        "Присоединяйтесь к нам сегодня и давайте сделаем ваш бренд неповторимым! 💼"
    )

    ozon_button = InlineKeyboardButton('🛒 Ozon', url='https://www.ozon.ru/brand/stickerway-101097965/')
    wildberries_button = InlineKeyboardButton('🛍️ Wildberries',
                                              url='https://www.wildberries.ru/brands/868382-StickerWay')
    InlineKeyboardButton('🏠 На главную', callback_data='home')

    reply_markup = InlineKeyboardMarkup(row_width=2).add(ozon_button, wildberries_button)

    await bot.send_message(callback_query.from_user.id, about_us_text, reply_markup=reply_markup, parse_mode='Markdown')


# Обработчик нажатия кнопки "Оставить отзыв"
# Обработчик нажатия кнопки "Оставить отзыв"
@dp.callback_query_handler(lambda c: c.data == 'feedback')
async def process_feedback_callback(callback_query: types.CallbackQuery):
    await FeedbackForm.Feedback.set()
    await callback_query.answer()
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('❌ Отмена', callback_data='cancel_feedback'))
    await bot.send_message(
        callback_query.from_user.id,
        "🌟 Мы всегда рады вашему мнению и ценим ваше внимание к нашему сервису. \n\n"
        "📝 Пожалуйста, поделитесь вашим отзывом или предложением. \n"
        "💬 Ваше мнение важно для нас!",
        reply_markup=keyboard
    )


# Обработчик отмены отзыва
@dp.callback_query_handler(lambda c: c.data == 'cancel_feedback', state=FeedbackForm.Feedback)
async def process_cancel_feedback_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.answer("Отправка отзыва отменена.")
    await bot.send_message(
        callback_query.from_user.id,
        "❌ Отправка отзыва была отменена. Вы можете вернуться в меню, нажав на кнопку ниже:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('🏠 На главную', callback_data='home'))
    )


# Обработчик текстового сообщения с отзывом
@dp.message_handler(state=FeedbackForm.Feedback)
async def process_feedback_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['feedback'] = message.text

    # Формируем кликабельную ссылку на пользователя
    user_link = f"[{message.from_user.full_name}](tg://user?id={message.from_user.id})"
    if message.from_user.username:
        user_link = f'<a href="https://t.me/{message.from_user.username}">{message.from_user.full_name}</a>'

    # Формируем превью страницы пользователя
    user_preview = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.full_name}</a>'
    if message.from_user.username:
        user_preview = f'<a href="https://t.me/{message.from_user.username}">{message.from_user.full_name}</a>'

    # Отправляем отзыв в группу с превью страницы пользователя
    # -4256534684
    await bot.send_message(
        -1002195788596,
        f"Новый отзыв от пользователя {user_preview} (ID: {message.from_user.id}):\n\n{message.text}",
        parse_mode=types.ParseMode.HTML
    )

    # Уведомляем пользователя и добавляем кнопку на главную
    await message.answer(
        "🙏 Спасибо за ваш отзыв!\n\n"
        "💼 Ваше мнение очень важно для нас. Мы всегда готовы улучшать наш сервис благодаря вашим отзывам.\n\n"
        "🏠 Вы можете вернуться в меню, нажав на кнопку ниже:",
        reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('🏠 На главную', callback_data='home')),
        parse_mode=types.ParseMode.MARKDOWN
    )

    # Возвращаемся в начальное состояние
    await state.finish()

# Заказать бота
# @dp.callback_query_handler(lambda c: c.data == 'place_order')
# async def handle_place_order(callback_query: types.CallbackQuery):
#     questions = (
#         "Для оформления заявки, пожалуйста, ответьте на следующие вопросы:\n"
#         "1️⃣ Какого типа бот вам нужен?\n"
#         "2️⃣ Какой функционал должен быть у бота?\n"
#         "3️⃣ Есть ли какие-либо особые требования к боту?\n"
#         "4️⃣ Какие системы должны быть интегрированы с ботом?\n"
#         "5️⃣ Какие сроки рассматриваются для разработки?\n\n"
#         "🔹 *После того как сформулированы все вопросы напишите Администратору.*"
#     )
#
#     keyboard = InlineKeyboardMarkup()
#     keyboard.add(InlineKeyboardButton("📩 Написать", url="https://t.me/BOTS_FATHERR"))
#     keyboard.add(InlineKeyboardButton("🏠 На главную", callback_data="home"))
#     await bot.send_message(callback_query.from_user.id, questions, reply_markup=keyboard, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == 'support')
async def process_support_callback(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()

    faq_button = InlineKeyboardButton('📋 Частые вопросы', callback_data='faq')
    feedback_button = InlineKeyboardButton('📩 Обратная связь', callback_data='feedback')
    buy_in_bulk_button = InlineKeyboardButton('🛒 Купить наклейки большой партией', callback_data='buy_in_bulk')
    offer_design_button = InlineKeyboardButton('✏️ Предложить дизайн/цвет/надпись наклейки',
                                               callback_data='offer_design')
    damaged_items_button = InlineKeyboardButton('🆘 Проблема с заказом (повреждён, перепутан, задержка доставки)',
                                                callback_data='damaged_items')
    # order_bot_button = InlineKeyboardButton('🤖 Заказать бота', callback_data='place_order')
    home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')

    keyboard.row(faq_button, feedback_button)
    keyboard.row(buy_in_bulk_button)
    keyboard.row(offer_design_button)
    keyboard.add(damaged_items_button)
    # keyboard.add(order_bot_button)  # Adding the order bot button
    keyboard.add(home_button)  # Ensuring the home button is the last one

    # Путь к файлу с изображением
    # image_path = 'home\\ruvds-user\\tickets\\2.png'
    image_path = '2.png'

    # Отправка изображения с подписью и кнопками
    with open(image_path, 'rb') as photo:
        await bot.send_photo(
            callback_query.from_user.id,
            photo,
            caption="📢 Добро пожаловать в раздел поддержки! 🛠️\n\n"
                    "Выберите одну из следующих опций, чтобы узнать больше или связаться с нами:\n\n"
                    "📋 *Частые вопросы* - получите ответы на наиболее распространенные вопросы.\n"
                    "📩 *Обратная связь* - отправьте нам сообщение с вашими вопросами или предложениями.\n\n"
                    "Спасибо, что выбрали нас! Наша команда готова помочь вам в любое время. 🤖✨",
            reply_markup=keyboard
        )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'home')
async def back_to_home_callback(callback_query: types.CallbackQuery):
    # Путь к файлу с изображением
    #image_path = 'home\\ruvds-user\\tickets\\1.jpg'
    image_path = '1.jpg'

    # Отправка изображения с подписью и кнопками
    with open(image_path, 'rb') as photo:
        await bot.send_photo(
            callback_query.from_user.id,
            photo,
            caption=f"🙋Привет, {callback_query.from_user.first_name}!\n\n🤖Я официальный бот поддержки клиентов магазина *StickerWay*. \n\n🆘Я создан для того чтобы помогать Вам.\n\n👇Здесь Вы можете:\n\n"
                    "🏷️ - Ознакомиться со всеми видами наших наклеек и этикеток\n"
                    "📦 - Заказать наклейки напрямую у производителя\n"
                    "📰 - Узнать о новостях и новинках\n"
                    "📑 - Просмотреть инструкции и полезные материалы по работе с этикетками\n"
                    "❓ - Задать вопрос представителю Бренда\n"
                    "📝 - Написать нам, если у вас есть проблема с нашими товарами",
            reply_markup=InlineKeyboardMarkup().row(
                InlineKeyboardButton('📚 Каталог', callback_data='catalog'),
                InlineKeyboardButton('🛠️ Поддержка', callback_data='support')
            ).row(
                InlineKeyboardButton('📰 Новости', url='https://t.me/sticker_way/24')
            ).row(
                InlineKeyboardButton('🛒 Ozon', url='https://www.ozon.ru/brand/stickerway-101097965/'),
                InlineKeyboardButton('🛍️ Wildberries', url='https://www.wildberries.ru/brands/868382-StickerWay')
            )
        )
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'damaged_items')
async def process_damaged_items_callback(callback_query: types.CallbackQuery):
    # Сообщение для пользователей с проблемами с доставкой или заказом
    damaged_items_message = (
        "📦 *Поврежденные наклейки/не тот товар/задержали доставку*\n\n"
        "Если у вас возникли проблемы с доставкой (поврежденные наклейки, неправильный товар, задержка доставки и т. д.), "
        "пожалуйста, свяжитесь с нами, и мы постараемся решить вашу проблему как можно скорее.\n\n"
        "Пожалуйста, опишите вашу проблему как можно подробнее.\n\n"
        "Спасибо за ваше понимание и терпение! 📦🤝"
    )

    # Создание клавиатуры с inline кнопкой для обратной связи и кнопкой "На главную"
    write_to_admin_button = InlineKeyboardButton('📝 Написать', url='https://t.me/Bogosann')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    reply_markup = InlineKeyboardMarkup().add(write_to_admin_button, back_to_home_button)

    # Отправка сообщения о проблеме с доставкой и кнопки для написания администратору и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        damaged_items_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'offer_design')
async def process_offer_design_callback(callback_query: types.CallbackQuery):
    # Сообщение для предложения дизайна/цвета/надписи наклейки
    offer_design_message = (
        "✏️ *Предложение дизайна/цвета/надписи наклейки*\n\n"
        "Если у вас есть свои идеи по дизайну, цвету или надписи на наклейке, мы готовы их рассмотреть "
        "и воплотить в жизнь!\n\n"
        "Пожалуйста, напишите администратору с описанием вашего предложения и прикрепите, если есть, "
        "визуализацию или описание.\n\n"
        "Спасибо за вашу инициативу! 🎨✨"
    )

    # Создание inline кнопки для написания администратору
    write_to_admin_button = InlineKeyboardButton('📝 Написать', url='https://t.me/Bogosann')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')

    # Создание клавиатуры с inline кнопкой и кнопкой "На главную"
    reply_markup = InlineKeyboardMarkup().add(write_to_admin_button, back_to_home_button)

    # Отправка сообщения для предложения дизайна/цвета/надписи наклейки с кнопкой для написания администратору и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        offer_design_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'buy_in_bulk')
async def process_buy_in_bulk_callback(callback_query: types.CallbackQuery):
    # Сообщение для заказа большой партии
    bulk_order_message = (
        "🛒 *Заказ наклеек большой партией*\n\n"
        "Для оформления заказа большой партии наклеек, пожалуйста, напишите администратору "
        "со списком желаемых товаров и количеством каждого, а также укажите свои контактные данные "
        "для связи.\n\n"
        "Спасибо за выбор *StickerWay*!"
    )

    # Создание inline кнопки для написания администратору
    write_to_admin_button = InlineKeyboardButton('📝 Написать', url='https://t.me/Bogosann')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')

    # Создание клавиатуры с inline кнопкой и кнопкой "На главную"
    reply_markup = InlineKeyboardMarkup().add(write_to_admin_button, back_to_home_button)

    # Отправка сообщения для заказа большой партии с кнопкой для написания администратору и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        bulk_order_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'faq')
async def process_faq_callback(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    printer_setup_button = InlineKeyboardButton('🖨️ Настройка принтера Xprinter 365B',
                                                url='https://telegra.ph/Rukovodstvo-po-pechati-05-22')
    thermal_printing_button = InlineKeyboardButton('🏷️ Термотрансферная печать', callback_data='thermal_printing')
    no_ribbon_printing_button = InlineKeyboardButton('🚫 Печать без риббона', callback_data='no_ribbon_printing')
    printer_compatibility_button = InlineKeyboardButton('🖨️📱 Совместимость принтеров',
                                                        callback_data='printer_compatibility')
    improve_print_quality_button = InlineKeyboardButton('🖨️ Улучшить качество печати',
                                                        callback_data='improve_print_quality')
    calibrate_printer_button = InlineKeyboardButton('🛠️ Калибровка принтера', callback_data='calibrate_printer')
    label_writing_button = InlineKeyboardButton('🖋️ Надпись на этикетках', callback_data='label_writing')

    keyboard.row(printer_setup_button)
    keyboard.row(thermal_printing_button)
    keyboard.row(no_ribbon_printing_button)
    keyboard.row(printer_compatibility_button)
    keyboard.row(improve_print_quality_button)
    keyboard.row(calibrate_printer_button)
    keyboard.add(label_writing_button)

    # Путь к файлу с изображением
    # image_path = 'home\\ruvds-user\\tickets\\3.png'
    image_path = '3.png'
    # Отправка изображения с подписью и кнопками
    with open(image_path, 'rb') as photo:
        await bot.send_photo(
            callback_query.from_user.id,
            photo,
            caption="📋 Часто задаваемые вопросы:\n\n"
            ,
            reply_markup=keyboard
        )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'label_writing')
async def process_label_writing_callback(callback_query: types.CallbackQuery):
    response_message = (
        "🖋️ На наших этикетках можно писать ручкой и маркером."
    )

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button).add(back_to_home_button)

    # Отправка сообщения о возможности писать на этикетках и кнопок "Назад к вопросам" и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        response_message,
        reply_markup=keyboard
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'calibrate_printer')
async def process_calibrate_printer_callback(callback_query: types.CallbackQuery):
    response_message = (
        "🛠️ Если принтер с трудом тянет ленту, возможно вы слишком плотно прижали ее внутри принтера. "
        "Ослабьте натяжение ленты, немного его размотайте, чтобы принтеру было легче тянуть рулон. "
        "Проверьте, что вы не плотно зажали рулон, а он может свободно двигаться на держателе."
    )

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button).add(back_to_home_button)

    # Отправка сообщения с решением проблемы и кнопок "Назад к вопросам" и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        response_message,
        reply_markup=keyboard
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'improve_print_quality')
async def process_improve_print_quality_callback(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    pale_printing_button = InlineKeyboardButton('🖨️ Бледная печать', callback_data='pale_printing')
    blurry_printing_button = InlineKeyboardButton('🔍 Получается нечеткая', callback_data='blurry_printing')

    keyboard.add(pale_printing_button, blurry_printing_button)

    # Создание клавиатуры с кнопками "Бледная печать" и "Получается нечеткая"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard.row(back_to_questions_button).add(back_to_home_button)

    # Отправка сообщения с кнопками "Бледная печать" и "Получается нечеткая"
    await bot.send_message(
        callback_query.from_user.id,
        "Выберите один из вариантов:",
        reply_markup=keyboard
    )
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'pale_printing')
async def process_pale_printing_callback(callback_query: types.CallbackQuery):
    message_text = (
        "🖨️ *Решение проблемы 'Бледной печати'*:\n\n"
        "Вам необходимо зайти в раздел 'Настройки печати', далее вкладка 'Параметры'. Здесь есть бегунок напротив значения 'Интенсивность цвета'. Попробуйте увеличить интенсивность и уменьшить скорость печати.\n\n"
        "Также хотим напомнить, что качество печати напрямую зависит от качества головки принтера - ее нужно периодически чистить от пыли, ворса, случайно прилипших остатков бумаги (используйте для этого безворсовую салфетку)."
    )

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button, back_to_home_button)

    # Отправка сообщения с решением проблемы и кнопками "Назад к вопросам" и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'blurry_printing')
async def process_blurry_printing_callback(callback_query: types.CallbackQuery):
    message_text = (
        "🔍 *Решение проблемы 'Нечеткой печати'*:\n\n"
        "Вам необходимо зайти во вкладку 'Графика'. В окошке 'Сглаживание' поставьте значение 'Нет'. Если это действие не помогло – необходимо поменять качество исходного изображения или его формат (JPG, PNG и т.д.)."
    )

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button, back_to_home_button)

    # Отправка сообщения с решением проблемы и кнопками "Назад к вопросам" и "На главную"
    await bot.send_message(
        callback_query.from_user.id,
        message_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'thermal_printing')
async def process_thermal_printing_callback(callback_query: types.CallbackQuery):
    response_message = "Наши этикетки подходят для термотрансферной печати с риббоном. 🏷️"

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button, back_to_home_button)

    # Отправка сообщения с информацией о термотрансферной печати и кнопками "Назад к вопросам" и "На главную"
    await bot.send_message(callback_query.from_user.id, response_message, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'no_ribbon_printing')
async def process_no_ribbon_printing_callback(callback_query: types.CallbackQuery):
    response_message = "Да, наши этикетки можно использовать только с термопринтером, без использования риббона. 🚫"

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button, back_to_home_button)

    # Отправка сообщения с информацией о том, что этикетки можно использовать без риббона и кнопками "Назад к вопросам" и "На главную"
    await bot.send_message(callback_query.from_user.id, response_message, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'printer_compatibility')
async def process_printer_compatibility_callback(callback_query: types.CallbackQuery):
    response_message = (
        "Наши этикетки не совместимы со следующими моделями принтеров:\n\n"
        "• Pop mix\n"
        "• NIIMBOT\n"
        "• Phomemo\n"
        "• Peripage\n"
        "• Детские принтеры\n\n"
        "🖨️📱"
    )

    # Создание клавиатуры с кнопками "Назад к вопросам" и "На главную"
    back_to_questions_button = InlineKeyboardButton('⬅️ Назад к вопросам', callback_data='faq')
    back_to_home_button = InlineKeyboardButton('🏠 На главную', callback_data='home')
    keyboard = InlineKeyboardMarkup().row(back_to_questions_button, back_to_home_button)

    # Отправка сообщения с информацией о несовместимости принтеров и кнопками "Назад к вопросам" и "На главную"
    await bot.send_message(callback_query.from_user.id, response_message, reply_markup=keyboard)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'catalog')
async def catalog_callback(callback_query: types.CallbackQuery):
    catalog_text = (
        "🏷️ *StickerWay* предлагает широкий ассортимент качественных наклеек и этикеток для различных целей.\n\n"
        "Выберите категорию товаров для ознакомления с ассортиментом:\n"
    )

    # Создание кнопок для категорий товаров
    category_buttons = [
        InlineKeyboardButton('🌈 Цветные термоэтикетки 58*40,30*20', url='https://t.me/sticker_way/22'),
        InlineKeyboardButton('🟡 Термоэтикетки 40*40 круглые', url='https://t.me/sticker_way/20'),
        InlineKeyboardButton('🎉 Праздничные наклейки', url='https://t.me/sticker_way/18'),
        InlineKeyboardButton('📔 Наклейки на тетради/школьные', url='https://t.me/sticker_way/16'),
        InlineKeyboardButton('⚪️  Для маркировки (пустые поля)', url='https://t.me/sticker_way/12'),
        InlineKeyboardButton('☘️ Наклейки Натуральный продукт', url='https://t.me/sticker_way/8'),
        InlineKeyboardButton('🎁 Наклейки Подарок', url='https://t.me/sticker_way/6'),
        InlineKeyboardButton('🙏🏻 Спасибо за заказ', url='https://t.me/sticker_way/4'),
        InlineKeyboardButton('🤲🏻Ручная работа', url='https://t.me/sticker_way/2'),
        InlineKeyboardButton('🧼 Мыло ручной работы', url='https://t.me/sticker_way/10'),
        InlineKeyboardButton('🗃Разное', url='https://t.me/sticker_way/14'),
        InlineKeyboardButton('🏠 На главную', callback_data='home')
    ]

    # Добавление кнопок в разметку
    reply_markup = InlineKeyboardMarkup(row_width=2)
    for button in category_buttons:
        reply_markup.row(button)

    await bot.send_message(callback_query.from_user.id, catalog_text, reply_markup=reply_markup, parse_mode='Markdown')


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)
