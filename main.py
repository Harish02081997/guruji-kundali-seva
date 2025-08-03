import logging
import csv
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler

BOT_TOKEN = "8422375930:AAHxRspRh_Ke6q8RPASMmuH9Kbl9CLbNP3A"
RAZORPAY_KEY_ID = "rzp_live_XlFFKckEFxqvnb"
RAZORPAY_KEY_SECRET = "5Mw01AJWo0kxxPYqM3FutyI8"

(RAASHI, NAME, PHONE, GENDER, STATE, DOB, TOB, EMAIL) = range(8)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

time_slots = [
    ["12:00 AM – 3:00 AM", "3:01 AM – 6:00 AM"],
    ["6:01 AM – 9:00 AM", "9:01 AM – 12:00 PM"],
    ["12:01 PM – 3:00 PM", "3:01 PM – 6:00 PM"],
    ["6:01 PM – 9:00 PM", "9:01 PM – 12:00 AM"]
]

raashi_keyboard = [
    ["मेष", "वृषभ", "मिथुन"],
    ["कर्क", "सिंह", "कन्या"],
    ["तुला", "वृश्चिक", "धनु"],
    ["मकर", "कुम्भ", "मीन"]
]

gender_keyboard = [["पुरुष", "महिला", "अन्य"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001F64F पवित्र ज्योतिष सेवा में आपका स्वागत है।\nमैं गुरुजी, आपकी कुंडली के माध्यम से मार्गदर्शन करूंगा।\n\nकृपया नीचे से अपनी राशि चुनें:",
        reply_markup=ReplyKeyboardMarkup(raashi_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return RAASHI

async def get_raashi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['raashi'] = update.message.text
    await update.message.reply_text("बहुत बढ़िया। अब कृपया अपना पूरा नाम बताएं:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("अब अपना मोबाइल नंबर भेजें:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("लिंग चुनें:", reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gender'] = update.message.text
    await update.message.reply_text("आपका राज्य बताएं:", reply_markup=ReplyKeyboardRemove())
    return STATE

async def get_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = update.message.text
    await update.message.reply_text("अपनी जन्म तिथि बताएं (dd-mm-yyyy):")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dob'] = update.message.text
    await update.message.reply_text("जन्म का समय चुनें:", reply_markup=ReplyKeyboardMarkup(time_slots, one_time_keyboard=True, resize_keyboard=True))
    return TOB

async def get_tob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tob'] = update.message.text
    await update.message.reply_text("अब कृपया अपना ईमेल पता साझा करें:", reply_markup=ReplyKeyboardRemove())
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    user = context.user_data

    with open('kundali_data.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([user['raashi'], user['name'], user['phone'], user['gender'], user['state'], user['dob'], user['tob'], user['email']])

    payment_link = generate_payment_link(user['name'], user['email'], user['phone'])

    summary = f"\n🙏 आपकी जानकारी इस प्रकार है:\n\nराशि: {user['raashi']}\nनाम: {user['name']}\nमोबाइल: {user['phone']}\nलिंग: {user['gender']}\nराज्य: {user['state']}\nजन्म तिथि: {user['dob']}\nजन्म समय: {user['tob']}\nईमेल: {user['email']}\n\nकृपया ₹49 का भुगतान करें इस लिंक पर:\n{payment_link}\n\nभुगतान के बाद आपकी कुंडली 24 घंटे के भीतर ईमेल पर भेज दी जाएगी। 🙏"

    await update.message.reply_text(summary)
    return ConversationHandler.END

def generate_payment_link(name, email, contact):
    url = "https://api.razorpay.com/v1/payment_links"
    payload = {
        "amount": 4900,
        "currency": "INR",
        "accept_partial": False,
        "description": "Kundali Service by Guruji",
        "customer": {
            "name": name,
            "contact": contact,
            "email": email
        },
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "callback_url": "https://telegram.me/guruji_kundali_bot",
        "callback_method": "get"
    }
    response = requests.post(url, auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET), json=payload)
    return response.json().get("short_url", "[लिंक जनरेट नहीं हुआ]")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RAASHI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_raashi)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_state)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            TOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tob)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()
