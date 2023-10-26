from telegram import Update
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f'Hello {u.username}, your ID is {u.id}')
    

async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Bye! I''m done.')
    await context.application.stop_running()


async def signin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    credentials = context.user_data.setdefault('credentials', dict())
    if credentials:
        reply_text = 'You are already signed in. Sign out first'
    elif len(context.args) == 2:
        name, key = context.args
        credentials['name'] = name
        credentials['key'] = key
        reply_text = 'Credentials were saved'
    else:
        reply_text = '\n'.join(['Error: incorrect number of arguments',
                                'Usage:', 
                                '/signin NAME KEY'])
    await update.message.reply_text(reply_text)

async def signout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    credentials = context.user_data.setdefault('credentials', dict())
    if credentials:
        del context.user_data['credentials']
        reply_text = 'You are signed out'
    else:
        reply_text = 'You are NOT signed in yet'
    await update.message.reply_text(reply_text)