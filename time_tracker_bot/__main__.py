import os

from telegram.ext import ApplicationBuilder, CommandHandler

from .handlers import start_handler, stop_handler
from argparse import ArgumentParser


def run_bot():
    token = os.environ.get('TIME_TRACKER_BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('stop', stop_handler))

    app.run_polling()


parser = ArgumentParser(prog='time_tracker_bot')

credentials_group = parser.add_argument_group('credentials')
credentials_group.add_argument('--encrypt-credentials', metavar='DST_FILENAME')
credentials_group.add_argument('--username', metavar='USERNAME')
credentials_group.add_argument('--password', metavar='PASSWORD')
credentials_group.add_argument('--decrypt-credentials', metavar='SRC_FILENAME')
credentials_group.add_argument('--key', metavar='KEY')
credentials_group.add_argument('--credentials', metavar='KEY')
running_group = parser.add_argument_group('running')
running_group.add_argument('--run', action='store_true')

args = parser.parse_args()

if args.encrypt_credentials or args.decrypt_credentials:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes

    if args.encrypt_credentials:
        with open(args.encrypt_credentials, 'wb') as dst:
            key = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_EAX)
            encrypted, tag = cipher.encrypt_and_digest(f'{args.username} {args.password}'.encode())
            [ dst.write(x) for x in (cipher.nonce, tag, encrypted) ]
            print(f'Success! Your key to send bot is "{key.hex()}"')
    elif args.decrypt_credentials:
        with open(args.decrypt_credentials, 'rb') as src:
            nonce, tag, encrypted = [ src.read(x) for x in (16, 16, -1) ]
            cipher = AES.new(bytes.fromhex(args.key), AES.MODE_EAX, nonce=nonce)
            decrypted = cipher.decrypt_and_verify(encrypted, tag)
            print(decrypted)

if args.run:
    run_bot()





