import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = '8559286512:AAFi9rSAdBv_gp4WBPxJNssI4Eh5BpJJrHM'
ADMIN_ID = 5182829694
GROUP_CHAT_ID = -1004402853740

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    keyboard = [[InlineKeyboardButton("💳 មើលព័ត៌មានបង់ប្រាក់", callback_data="show_qr")]]
    await update.message.reply_text(
        f"សួស្តី {user_name}! ស្វាគមន៍មកកាន់សេវាកម្មមើលរឿង VIP 🎬\n\nសូមចុចប៊ូតុងខាងក្រោមដើម្បីទទួលបានព័ត៌មានបង់ប្រាក់។",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_qr":
        payment_info = (
            "📥 **ព័ត៌មានសម្រាប់ការបង់ប្រាក់:**\n\n"
            "🏦 **ABA Bank:** `000 111 222` (Thel Vuthea)\n"
            "💵 **តម្លៃ VIP:** 2$ / ខែ\n\n"
            "**ការណែនាំ:**\n"
            "១. ផ្ទេរប្រាក់ទៅកាន់គណនីខាងលើ\n"
            "២. រួច **ផ្ញើរូបភាព Slip បង់ប្រាក់** មកកាន់ Bot នេះ\n"
            "៣. Admin នឹងពិនិត្យ រួចផ្ញើ Link ចូល Group ជូន!"
        )
        await update.effective_message.reply_text(payment_info, parse_mode='Markdown')

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])
        try:
            # បង្កើត Link អញ្ជើញចូល Group (ប្រៀបដូចជាសំបុត្រប្រើបាន ១ ដង)
            invite_link = await context.bot.create_chat_invite_link(chat_id=GROUP_CHAT_ID, member_limit=1)
            
            # ផ្ញើ Link ទៅកាន់អ្នកប្រើប្រាស់ដែលបានបង់ប្រាក់
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 **ការបង់ប្រាក់ត្រូវបានអនុម័ត!**\n\nនេះជា Link សម្រាប់ចូល Group របស់អ្នក:\n{invite_link.invite_link}",
                parse_mode='Markdown'
            )
            
            # កែប្រែ Caption លើរូបភាព Slip របស់ Admin (ដោះស្រាយ Error កន្លែងនេះ)
            old_caption = query.message.caption or ""
            await query.edit_message_caption(
                caption=f"{old_caption}\n\n✅ **បានអនុម័ត និងផ្ញើ Link រួចរាល់!**",
                parse_mode='Markdown'
            )
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ មានបញ្ហាក្នុងការបង្កើត Link: {e}")

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.message.photo[-1].get_file()
    admin_keyboard = [[InlineKeyboardButton(f"✅ Approve ({user.first_name})", callback_data=f"approve_{user.id}")]]
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file.file_id,
        caption=f"📩 **ទទួលបាន Slip បង់ប្រាក់ថ្មី!**\n\nពី៖ {user.first_name} (@{user.username})\nUser ID: `{user.id}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(admin_keyboard)
    )
    await update.message.reply_text("✅ ទទួលបានរូបភាព Slip រួចរាល់! ក្រុមការងារកំពុងពិនិត្យ ហើយនឹងផ្ញើ Link ជូនក្នុងពេលឆាប់ៗ។")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_slip))
    app.run_polling()
