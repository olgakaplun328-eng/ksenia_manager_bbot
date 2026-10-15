import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logging.getLogger('httpx').setLevel(logging.WARNING)
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
WAIT_PRODUCT, WAIT_HEIGHT, WAIT_MEASUREMENTS, WAIT_FIT, WAIT_CONFIRM, WAIT_NAME, WAIT_PHONE, WAIT_CITY, WAIT_BRANCH = range(9)


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📏 Підібрати розмір', callback_data='size')],
        [InlineKeyboardButton('🛍️ Хочу замовити', callback_data='order')],
        [InlineKeyboardButton('👩‍💼 Зв’язатися з менеджером', callback_data='manager')],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text('Вітаю! 👋 Я помічник магазину одягу.\nНадішліть фото товару або напишіть його назву/посилання.', reply_markup=menu())
    return WAIT_PRODUCT

async def menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == 'manager':
        await q.message.reply_text('Опишіть питання текстом. Для прямого зв’язку з менеджером потрібне окреме налаштування.')
    else:
        await q.message.reply_text('Надішліть фото товару або напишіть його назву чи посилання.')
    return WAIT_PRODUCT

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.photo:
        context.user_data['product'] = 'Фото надіслано; модель не розпізнана автоматично'
        await msg.reply_text('Фото отримав 📷 Автоматичне розпізнавання ще не підключене. Напишіть назву або посилання товару.')
        return WAIT_PRODUCT
    context.user_data['product'] = (msg.text or '').strip()
    await msg.reply_text('Який ваш зріст у сантиметрах? Наприклад: 172')
    return WAIT_HEIGHT

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['height'] = update.message.text.strip()
    await update.message.reply_text('Напишіть мірки в сантиметрах, якщо знаєте (груди, талія, стегна). Якщо не знаєте — напишіть «не знаю».')
    return WAIT_MEASUREMENTS

async def measurements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['measurements'] = update.message.text.strip()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton('Вільніше', callback_data='fit_loose'), InlineKeyboardButton('По фігурі', callback_data='fit_regular')], [InlineKeyboardButton('Обтисло', callback_data='fit_tight'), InlineKeyboardButton('Не знаю', callback_data='fit_unknown')]])
    await update.message.reply_text('Як хочете, щоб одяг сидів?', reply_markup=kb)
    return WAIT_FIT

async def fit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data['fit'] = {'fit_loose':'вільніше','fit_regular':'по фігурі','fit_tight':'обтисло','fit_unknown':'не знаю'}.get(q.data, 'не вказано')
    await q.message.reply_text('Дякую! Точний розмір треба звірити з таблицею конкретної моделі. Бажаєте замовити?', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Так, замовити', callback_data='confirm_yes')], [InlineKeyboardButton('Поки ні', callback_data='confirm_no')]]))
    return WAIT_CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == 'confirm_no':
        await q.message.reply_text('Добре! Якщо виникнуть питання, напишіть сюди.')
        return ConversationHandler.END
    await q.message.reply_text('Напишіть ім’я та прізвище отримувача.')
    return WAIT_NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text('Вкажіть номер телефону для доставки.')
    return WAIT_PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text.strip()
    await update.message.reply_text('Вкажіть місто або населений пункт.')
    return WAIT_CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text.strip()
    await update.message.reply_text('Вкажіть службу доставки та номер/адресу відділення або поштомата.')
    return WAIT_BRANCH

async def branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['branch'] = update.message.text.strip()
    summary = ('🛍️ НОВЕ ЗАМОВЛЕННЯ\n'
        f"Товар: {context.user_data.get('product', 'не вказано')}\n"
        f"Зріст: {context.user_data.get('height', 'не вказано')}\n"
        f"Мірки: {context.user_data.get('measurements', 'не вказано')}\n"
        f"Посадка: {context.user_data.get('fit', 'не вказано')}\n"
        f"Отримувач: {context.user_data.get('name', 'не вказано')}\n"
        f"Телефон: {context.user_data.get('phone', 'не вказано')}\n"
        f"Місто: {context.user_data.get('city', 'не вказано')}\n"
        f"Доставка: {context.user_data.get('branch', 'не вказано')}\n"
        f"Telegram ID клієнта: {update.effective_user.id}")
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=summary)
        except Exception:
            logging.exception('Не вдалося надіслати замовлення адміністратору')
            await update.message.reply_text('Дані зібрані, але сповістити менеджера не вдалося. Спробуйте пізніше.')
            return ConversationHandler.END
    else:
        logging.warning('ADMIN_CHAT_ID is not configured; order not forwarded.')
    await update.message.reply_text('Дякую! Дані зібрані. Менеджер має підтвердити наявність, розмір і ціну.\nАвтоматична оплата та надсилання рахунку поки не налаштовані.')
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text('Скасовано. Щоб почати знову, введіть /start.')
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text('/start — почати; /cancel — скасувати. Автоматичне визначення товару/розміру та оплата ще не підключені.')

def main():
    if not BOT_TOKEN:
        raise RuntimeError('Не задано BOT_TOKEN. Додайте його у Railway → сервіс → Variables.')
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(entry_points=[CommandHandler('start', start)], states={
        WAIT_PRODUCT: [CallbackQueryHandler(menu_choice, pattern='^(size|order|manager)$'), MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), product)],
        WAIT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
        WAIT_MEASUREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, measurements)],
        WAIT_FIT: [CallbackQueryHandler(fit, pattern='^fit_')],
        WAIT_CONFIRM: [CallbackQueryHandler(confirm, pattern='^confirm_')],
        WAIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        WAIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        WAIT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        WAIT_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, branch)],
    }, fallbacks=[CommandHandler('cancel', cancel)], allow_reentry=True)
    app.add_handler(conv)
    app.add_handler(CommandHandler('help', help_cmd))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
