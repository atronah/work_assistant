import os

from telegram import Update
from telegram.ext import ContextTypes

from .credentials import decrypt_credentials
from .otrs_tools import get_otrs_client


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(f'Hello {u.username}, your ID is {u.id}')


async def die_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    owner_id = os.environ.get('TIME_TRACKER_BOT_OWNER_ID')
    if str(u.id) == owner_id:
        await update.message.reply_text(f'Bye! I''m done.')
        await context.application.stop_running()
    else:
        await update.message.reply_text(f'You cannot kill me, stranger. Only owner can.')


async def signin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    credentials = context.user_data.setdefault('credentials', dict())
    if credentials:
        reply_text = 'You are already signed in. Sign out first'
    elif len(context.args) == 2:
        name, key = context.args
        
        try: 
            endpoint = os.environ.get('TIME_TRACKER_BOT_OTRS_ENDPOINT')
            username, password = decrypt_credentials(name, key)
            otrs_client = get_otrs_client(endpoint, username, password)

            credentials['name'] = name
            credentials['key'] = key
            reply_text = 'Success. Credentials were saved'
        except Exception as e:
            reply_text = str(e)
    else:
        reply_text = '\n'.join(['Error: incorrect number of arguments',
                                'Usage:', 
                                '/signin NAME KEY'])
    # remove message with private data in security reason
    await update.message.delete()
    await update.effective_chat.send_message(reply_text)


async def signout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    credentials = context.user_data.setdefault('credentials', dict())
    if credentials:
        del context.user_data['credentials']
        reply_text = 'You are signed out'
    else:
        reply_text = 'You are NOT signed in yet'
    await update.message.reply_text(reply_text)