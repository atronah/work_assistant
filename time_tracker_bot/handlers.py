from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f'Hello {u.username}, your ID is {u.id}')
    

async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Bye! I''m done.')
    await context.application.stop_running()