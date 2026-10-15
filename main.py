import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "-1004295486814")

(
    WAIT_PRODUCT, WAIT_HEIGHT, WAIT_MEASUREMENTS, WAIT_FIT, WAIT_CONFIRM,
    WAIT_NAME, WAIT_PHONE, WAIT_CITY, WAIT_BRANCH, WAIT_PAYMENT
) = range(10)

PAYMENT_INFO = (
    "🏦 *Реквізити для оплати*\n\n"
    "*Установа банку:* ПриватБанк\n"
    "*IBAN:* `UA273052990000026004015510852`\n"
    "*МФО банку:* 305299\n"
    "*Отримувач платежу:* ПАВЛІВ ОКСАНА БОГДАНІВНА\n"
    "*ЄДРПОУ:* 3316604824\n"
    "*Валюта рахунку:* UAH\n"
    "*Призначення платежу:* оплата за товар\n\n"
    "Для оплати відкрийте розділ «Платежі» у своєму банківському застосунку "
    "та введіть IBAN."
)

COD_INFO = (
    "📍 Відправляємо за повною оплатою або накладним платежем із передплатою 300 грн.\n\n"
    "На Новій пошті можете приміряти товар. Якщо все підходить — забираєте посилку. "
    "Якщо не підходить — разом із працівником пошти оформлюєте легке повернення.\n\n"
    "⚠️ Накладний платіж доступний лише у відділеннях Нової пошти. "
    "Після прибуття посилка зберігається 3 дні. У разі відмови від посилки передплата не повертається.\n\n"
    "Зверніть увагу: у пунктах приймання-видачі накладного платежу немає."
)

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📏 Підібрати розмір", callback_data="size")],
        [InlineKeyboardButton("🛍️ Хочу замовити", callback_data="order")],
        [InlineKeyboardButton("👩‍💼 Зв’язатися з менеджером", callback_data="manager")],
    ])

def persistent_menu():
    return ReplyKeyboardMarkup(
        [["📏 Підібрати розмір", "🛍️ Замовити"],
         ["👩‍💼 Менеджер"]],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Оберіть дію або надішліть фото"
    )

async def bottom_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    context.user_data.clear()
    if text == "👩‍💼 Менеджер":
        await update.effective_message.reply_text(
            "👩‍💼 Зв’язатися з менеджером\\n\\n"
            "📞 Оксана: 066 497 6073\\n"
            "📸 Наша сторінка Instagram ❣️\\n"
            "https://www.instagram.com/by_ks_jeans",
            reply_markup=persistent_menu(),
            disable_web_page_preview=True,
        )
        return WAIT_PRODUCT
    if text == "📏 Підібрати розмір":
        context.user_data["intent"] = "size"
        await update.effective_message.reply_text(
            "Надішліть фото товару або скриншот.\\n\\n"
            "Виміряйте бюст, талію на 1–2 пальці вище пупка та стегна в найширшому місці.\\n"
            "Допоможу Вам з розміром ❤️",
            reply_markup=persistent_menu(),
        )
        return WAIT_PRODUCT
    await update.effective_message.reply_text(
        "Надішліть фото товару або скриншот, який бажаєте замовити.",
        reply_markup=persistent_menu(),
    )
    context.user_data["intent"] = "order"
    return WAIT_PRODUCT

def order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Так, бажаю", callback_data="confirm_yes")],
        [InlineKeyboardButton("Ні, пізніше", callback_data="confirm_no")],
    ])

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Повна оплата", callback_data="pay_full")],
        [InlineKeyboardButton("📦 Накладений платіж (+ передплата 300 грн)", callback_data="pay_cod")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Вітаю! 👋 Я помічник магазину жіночого одягу.\n"
        "Надішліть фото товару, який вас цікавить, або напишіть його назву/посилання.",
        reply_markup=menu()
    )
    return WAIT_PRODUCT

async def menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "manager":
        await q.message.reply_text(
            "👩‍💼 Зв’язатися з менеджером\n\n"
            "📞 Оксана: 066 497 6073\n"
            "📸 Наша сторінка Instagram ❣️\n"
            "https://www.instagram.com/by_ks_jeans",
            disable_web_page_preview=True,
        )
        return WAIT_PRODUCT
    if q.data == "size":
        context.user_data["intent"] = "size"
        await q.message.reply_text(
            "Надішліть фото моделі одягу. Щоб підібрати розмір точніше, також знадобляться "
            "зріст і мірки грудей, талії та стегон. За одним фото одягу неможливо надійно "
            "визначити ваш розмір."
        )
        return WAIT_PRODUCT
    context.user_data["intent"] = "order"
    await q.message.reply_text("Надішліть фото товару або напишіть його назву чи посилання.")
    return WAIT_PRODUCT

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.photo:
        photo = msg.photo[-1]
        context.user_data["product"] = "Фото товару (додано до замовлення)"
        context.user_data["photo_file_id"] = photo.file_id
        await msg.reply_text(
            "Виміряйте бюст, талію на 1–2 пальці вище пупка та стегна в найширшому місці.\n\n"
            "Допоможу Вам з розміром 😊"
        )
        return WAIT_MEASUREMENTS
    context.user_data["product"] = (msg.text or "").strip()
    await msg.reply_text("Який ваш зріст у сантиметрах? Наприклад: 168")
    return WAIT_HEIGHT

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "Напишіть мірки в сантиметрах: груди, талія та стегна. "
        "Якщо не знаєте — напишіть «не знаю»."
    )
    return WAIT_MEASUREMENTS

async def measurements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["measurements"] = (update.message.text or "").strip()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Вільніше", callback_data="fit_loose"),
         InlineKeyboardButton("По фігурі", callback_data="fit_regular")],
        [InlineKeyboardButton("Обтисло", callback_data="fit_tight"),
         InlineKeyboardButton("Не знаю", callback_data="fit_unknown")]
    ])
    await update.message.reply_text("Як хочете, щоб одяг сидів?", reply_markup=kb)
    return WAIT_FIT

async def fit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["fit"] = {
        "fit_loose": "вільніше", "fit_regular": "по фігурі",
        "fit_tight": "обтисло", "fit_unknown": "не знаю"
    }.get(q.data, "не вказано")
    await q.message.reply_text(
        "Дякую! Я передам дані менеджеру для перевірки розміру за таблицею конкретної моделі.\n\n"
        "Бажаєте замовити?",
        reply_markup=order_keyboard()
    )
    return WAIT_CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "confirm_no":
        await q.message.reply_text("Добре 😊 Повертайтеся, коли будете готові замовити.")
        context.user_data.clear()
        return ConversationHandler.END
    await q.message.reply_text("Напишіть ім’я та прізвище отримувача.")
    return WAIT_NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = (update.message.text or "").strip()
    await update.message.reply_text("Вкажіть номер телефону для доставки.")
    return WAIT_PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = (update.message.text or "").strip()
    await update.message.reply_text("Вкажіть місто або населений пункт.")
    return WAIT_CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = (update.message.text or "").strip()
    await update.message.reply_text("Вкажіть службу доставки та номер/адресу відділення або поштомата.")
    return WAIT_BRANCH

async def branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["branch"] = (update.message.text or "").strip()
    await update.message.reply_text("Оберіть спосіб оплати:", reply_markup=payment_keyboard())
    return WAIT_PAYMENT

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    method = "Повна оплата" if q.data == "pay_full" else "Накладений платіж із передплатою 300 грн"
    context.user_data["payment_method"] = method

    summary = (
        "🛍️ НОВЕ ЗАМОВЛЕННЯ\n"
        f"Товар: {context.user_data.get('product', 'не вказано')}\n"
        f"Зріст: {context.user_data.get('height', 'не вказано')}\n"
        f"Мірки: {context.user_data.get('measurements', 'не вказано')}\n"
        f"Посадка: {context.user_data.get('fit', 'не вказано')}\n"
        f"Спосіб оплати: {method}\n"
        f"Отримувач: {context.user_data.get('name', 'не вказано')}\n"
        f"Телефон: {context.user_data.get('phone', 'не вказано')}\n"
        f"Місто: {context.user_data.get('city', 'не вказано')}\n"
        f"Доставка: {context.user_data.get('branch', 'не вказано')}\n"
        f"Telegram ID клієнта: {update.effective_user.id}"
    )
    if ADMIN_CHAT_ID:
        try:
            admin_id = int(ADMIN_CHAT_ID)
            await context.bot.send_message(chat_id=admin_id, text=summary)
            if context.user_data.get("photo_file_id"):
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=context.user_data["photo_file_id"],
                    caption="Фото товару до замовлення"
                )
        except Exception:
            logging.exception("Не вдалося надіслати замовлення адміністратору")
            await q.message.reply_text("Дані зібрані, але сповістити менеджера не вдалося. Спробуйте пізніше.")
            context.user_data.clear()
            return ConversationHandler.END

    if q.data == "pay_full":
        await q.message.reply_text(PAYMENT_INFO, parse_mode="Markdown")
    else:
        await q.message.reply_text(COD_INFO)
    await q.message.reply_text(
        "Дякуємо за замовлення! 🛍️ Менеджер підтвердить наявність, розмір і ціну. "
        "Якщо виникнуть питання — напишіть у цей чат."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text("Скасовано. Щоб почати знову, введіть /start.")
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "/start — почати оформлення замовлення\n"
        "/cancel — скасувати\n\n"
        "Розмір перевіряється за мірками та таблицею конкретної моделі; "
        "фото товару саме по собі не визначає розмір автоматично."
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задано BOT_TOKEN. Додайте його у Railway → сервіс → Variables.")
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"^(📏 Підібрати розмір|🛍️ Замовити|👩‍💼 Менеджер)$"), bottom_menu_text),
        ],
        states={
            WAIT_PRODUCT: [
                MessageHandler(filters.Regex(r"^(📏 Підібрати розмір|🛍️ Замовити|👩‍💼 Менеджер)$"), bottom_menu_text),
                CallbackQueryHandler(menu_choice, pattern="^(size|order|manager)$"),
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), product)
            ],
            WAIT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            WAIT_MEASUREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, measurements)],
            WAIT_FIT: [CallbackQueryHandler(fit, pattern="^fit_")],
            WAIT_CONFIRM: [CallbackQueryHandler(confirm, pattern="^confirm_")],
            WAIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            WAIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            WAIT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            WAIT_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, branch)],
            WAIT_PAYMENT: [CallbackQueryHandler(payment, pattern="^pay_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_cmd))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
