import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = '8559286512:AAFi9rSAdBv_gp4WBPxJNssI4Eh5BpJJrHM'
ADMIN_ID = 5182829694
GROUP_CHAT_ID = -1004402853740

# 🔑 Bakong API Token របស់អ្នក
BAKONG_TOKEN = '35e7a52b60bc4c20b968'
BAKONG_ACCOUNT = 'vuthea_thel@abaa' # ដាក់ Bakong ID ឬ ABA Account របស់អ្នក (ឧ. phone_number@abaa)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    keyboard = [[InlineKeyboardButton("💳 មើលព័ត៌មានបង់ប្រាក់ (KHQR Auto)", callback_data="show_qr")]]
    await update.message.reply_text(
        f"សួស្តី {user_name}! ស្វាគមន៍មកកាន់សេវាកម្មមើលរឿង VIP 🎬\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីទទួលបាន QR Code បង់ប្រាក់ស្វ័យប្រវត្តិ។",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def generate_bakong_qr(user_id):
    """ហៅ API ទៅ Bakong ដើម្បីបង្កើត Dynamic KHQR Code"""
    url = "https://api-bakong.nbc.gov.kh/v1/generate_khqr"
    headers = {"Authorization": f"Bearer {BAKONG_TOKEN}"}
    payload = {
        "accountId": BAKONG_ACCOUNT,
        "amount": 2.00,
        "currency": "USD",
        "merchantName": "VIP Movie Group",
        "billNumber": f"ORDER-{user_id}"
    }
    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json().get('data', {})
            return data.get('md5'), data.get('qr')
    except Exception as e:
        logging.error(f"Error generating KHQR: {e}")
    return None, None

def check_bakong_payment(md5_hash):
    """ពិនិត្យមើលថាតើមានប្រាក់ 들어လာ ឬនៅតាមរយៈ MD5 Hash"""
    url = f"https://api-bakong.nbc.gov.kh/v1/check_transaction_by_md5/{md5_hash}"
    headers = {"Authorization": f"Bearer {BAKONG_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get('responseCode') == 0 and res_data.get('data'):
                return True
    except Exception as e:
        logging.error(f"Error checking payment: {e}")
    return False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_qr":
        user_id = query.from_user.id
        await query.message.reply_text("⏳ កំពុងបង្កើត Dynamic KHQR Code សូមរង់ចាំបន្តិច...")
        
        md5_hash, qr_data = generate_bakong_qr(user_id)
        
        payment_info = (
            "📥 ព័ត៌មានសម្រាប់ការបង់ប្រាក់:\n\n"
            "💵 តម្លៃ VIP: 2.00$ / ខែ\n\n"
            "ការណែនាំ:\n"
            "១. ស្កែន QR Code ខាងលើ ឬប្រើប្រាស់ App ធនាគារបស់អ្នក\n"
            "២. ពេលបង់ប្រាក់រួចរាល់ ប្រព័ន្ធនឹងផ្ញើ Link ចូល Group ដោយស្វ័យប្រវត្តិ (Auto-Approve)!"
        )
        
        if qr_data:
            # បង្កើតរូប QR Code តាមរយៈ QR API Service
            qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}"
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=qr_image_url,
                caption=payment_info
            )
            
            # ចាប់ផ្តើមរត់ Loop ឆែកមើលការបង់ប្រាក់ស្វ័យប្រវត្តិរយៈពេល ៣ នាទី
            for _ in range(36): # ឆែករៀងរាល់ ៥ វិនាទីម្តង (36 x 5s = 180s)
                await asyncio.sleep(5)
                if check_bakong_payment(md5_hash):
                    # ពេលបង់ប្រាក់ជោគជ័យ -> Auto Generate Link & Send!
                    invite_link = await context.bot.create_chat_invite_link(chat_id=GROUP_CHAT_ID, member_limit=1)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎉 ទទួលបានការបង់ប្រាក់ជោគជ័យ!\n\nនេះជា Link សម្រាប់ចូល Group VIP របស់អ្នក:\n{invite_link.invite_link}"
                    )
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"✅ User ID `{user_id}` បានបង់ប្រាក់ 2$ តាម KHQR ជោគជ័យ (Auto-Approved)!"
                    )
                    return
        else:
            await query.message.reply_text(payment_info)

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])
        try:
            invite_link = await context.bot.create_chat_invite_link(chat_id=GROUP_CHAT_ID, member_limit=1)
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 ការបង់ប្រាក់ត្រូវបានអនុម័ត!\n\nនេះជា Link សម្រាប់ចូល Group របស់អ្នក:\n{invite_link.invite_link}"
            )
            old_caption = query.message.caption or ""
            await query.edit_message_caption(caption=f"{old_caption}\n\n✅ បានអនុម័ត និងផ្ញើ Link រួចរាល់!")
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ មានបញ្ហាក្នុងការបង្កើត Link: {e}")

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.message.photo[-1].get_file()
    admin_keyboard = [[InlineKeyboardButton(f"✅ Approve ({user.first_name})", callback_data=f"approve_{user.id}")]]
    
    username_str = f" (@{user.username})" if user.username else ""
    caption_text = f"📩 ទទួលបាន Slip បង់ប្រាក់ថ្មី!\n\nពី៖ {user.first_name}{username_str}\nUser ID: {user.id}"
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file.file_id,
        caption=caption_text,
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )
    await update.message.reply_text("✅ ទទួលបានរូបភាព Slip រួចរាល់! ក្រុមការងារកំពុងពិនិត្យ ហើយនឹងផ្ញើ Link ជូនក្នុងពេលឆាប់ៗ។")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_slip))
    app.run_polling()
