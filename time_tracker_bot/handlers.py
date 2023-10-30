import argparse
import os

from otrs.ticket.objects import Article
from telegram import Update
from telegram.ext import ContextTypes

from .core import connect_to_otrs


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
        credentials['name'] = name
        credentials['key'] = key
        
        try:
            await connect_to_otrs(credentials)
            reply_text = 'Success. Credentials were saved'
        except Exception as e:
            del credentials
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
        reply_text = 'You have been signed out'
    else:
        reply_text = 'You are NOT signed in yet'
    await update.message.reply_text(reply_text)


async def post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    credentials = context.user_data.setdefault('credentials', dict())
    if not credentials:
        await update.message.reply_text('You have to sign in before')
        return


    parser = argparse.ArgumentParser()
    parser.add_argument('ticket_number', metavar='TICKET_NUMBER')
    parser.add_argument('fact_time', metavar='FACT_TIME', default=0)

    message_text_lines = update.message.text.split('\n')

    if len(message_text_lines) < 3:
        raise Exception('3 or more lines required'
                        ' (one with command, next with article title and others with article body)')
    args = parser.parse_args(message_text_lines[0].split(' ')[1:])
    article_title = message_text_lines[1]
    message_body = '\n'.join(message_text_lines[2:])

    new_article = Article(Subject=article_title,
                          Body=message_body,
                          Charset='UTF8',
                          MimeType='text/plain',
                          TimeUnit=args.fact_time)

    otrs_client, _ = await connect_to_otrs(context.user_data.get('credentials'))
    otrs_client.tc.TicketUpdate(args.ticket_number, article=new_article)






