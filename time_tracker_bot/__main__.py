import os

from telegram.ext import ApplicationBuilder, CommandHandler

from .handlers import start_handler, stop_handler


token = os.environ.get('TIME_TRACKER_BOT_TOKEN')
app = ApplicationBuilder().token(token).build()

    
app.add_handler(CommandHandler('start', start_handler))
app.add_handler(CommandHandler('stop', stop_handler))

app.run_polling()