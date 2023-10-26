import os

from telegram.ext import ApplicationBuilder, CommandHandler, PicklePersistence

from .handlers import start_handler, stop_handler
from argparse import ArgumentParser


def run_bot():
    token = os.environ.get('TIME_TRACKER_BOT_TOKEN')
    
    persistence = PicklePersistence(filepath='bot.data', on_flush=False)
    
    app = ApplicationBuilder().token(token).persistence(persistence).build()
    
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('stop', stop_handler))

    app.run_polling()


parser = ArgumentParser(prog='time_tracker_bot')

credentials_group = parser.add_argument_group('credentials')
credentials_group.add_argument('-e', '--encrypt-credentials', action='store_true')
credentials_group.add_argument('-u', '--username', metavar='USERNAME')
credentials_group.add_argument('-p', '--password', metavar='PASSWORD')
credentials_group.add_argument('-n', '--name', metavar='NAME')
credentials_group.add_argument('-f', '--force-rewrite-token', action='store_true')
credentials_group.add_argument('-d', '--decrypt-credentials', action='store_true')
credentials_group.add_argument('-k', '--key', metavar='KEY')
running_group = parser.add_argument_group('running')
running_group.add_argument('--run', action='store_true')

args = parser.parse_args()

if args.encrypt_credentials:
    from getpass import getpass
    from .credentials import encrypt_credentials

    encrypt_credentials(args.name or input('Enter name: '),
                        args.key or getpass('Enter key (passphrase): '),
                        args.username or input('Enter username: '),
                        args.password or getpass('Enter password: '),
                        args.force_rewrite_token)
    print('Success!')
elif args.decrypt_credentials:
    from getpass import getpass
    from .credentials import decrypt_credentials
    username, password = decrypt_credentials(
                            args.name or input('Enter name: '),
                            args.key or getpass('Enter key (passphrase): '))
        
    print(f'{username=}')
    print(f'{password=}')
elif args.run:
    run_bot()





