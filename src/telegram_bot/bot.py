#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections.abc
import os
import re
from typing import Dict, Any
import traceback

from google_auth_httplib2 import Request
from googleapiclient.discovery import build, Resource
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Document
from telegram.ext import Updater, PicklePersistence, CallbackContext, CallbackQueryHandler
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Filters
import yaml
import logging, logging.config
import sys
import threading
from google_auth_oauthlib.flow import Flow
from urllib.parse import urljoin

# default settings
settings: Dict[str, Any] = {
    'access': {
        'token': None,
        'god_id_list': [],
        'google_api': {
            'oauth20_secret_file': None
        }
    },
    'logging': {
        'version': 1.0,
        'formatters': {
            'default': {
                'format': '[{asctime}]{levelname: <5}({name}): {message}',
                'style': '{'
            }
        },
        'handlers': {
            'general': {
                'class': 'logging.handlers.WatchedFileHandler',
                'level': 'INFO',
                'filename': 'bot.log',
                'formatter': 'default'
            },
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default'
            },
            'unknown_messages': {
                'class': 'logging.handlers.WatchedFileHandler',
                'level': 'DEBUG',
                'filename': 'unknown_messages.log',
                'formatter': 'default'
            }
        },
        'loggers': {
            'unknown_messages': {
                'level': 'DEBUG',
                'handlers': ['unknown_messages']
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['general']
        },
    }
}


def recursive_update(target_dict, update_dict):
    if not isinstance(update_dict, collections.abc.Mapping):
        return target_dict
    for k, v in update_dict.items():
        if isinstance(v, collections.abc.Mapping):
            target_dict[k] = recursive_update(target_dict.get(k, {}), v)
        else:
            target_dict[k] = v
    return target_dict


if os.path.exists('conf.yaml'):
    with open('conf.yaml', 'rt') as conf:
        recursive_update(settings, yaml.safe_load(conf))
else:
    with open('conf.yaml', 'wt') as conf:
        yaml.dump(settings, conf)


logging.config.dictConfig(settings['logging'])


if not settings['access']['token']:
    logging.error('Empty bot token in conf.yaml (`access/token`)')
    sys.exit(1)





def md2_prepare(text, escape_chars=r'_*[]()~>#+-=|{}.!'):
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def start(update, context):
    user = update.effective_user
    chat = update.effective_chat
    update.message.reply_markdown(f'Hello, {user.username}!\n'
                                  f'Your user ID is `{user.id}`'
                                  f' and out chat ID is `{chat.id}`')


def user_message(update, context):
    awaiting_data = context.user_data.setdefault('awaiting_data', [])
    if awaiting_data:
        value_path, _ = awaiting_data.pop(0)
        value_dict = context.user_data
        key_list = value_path.split('/')
        for key in key_list[:-1]:
            value_dict = value_dict.setdefault(key, {})
        value_dict[key_list[-1]] = update.message.text
        update.message.reply_text('Got it!')
        if awaiting_data:
            update.message.reply_text(awaiting_data[0][1])
    else:
        logger = logging.getLogger('unknown_messages')
        logger.debug(f'{update.effective_user.id} {update.message.text}')
        update.message.reply_text("I don't understand what you mean, that's why I've logged your message")


def shutdown():
    updater.stop()
    updater.is_idle = False


def die(update, context):
    user = update.effective_user
    if user.id in settings['access']['god_id_list']:
        update.message.reply_text('My fight is over!')
        threading.Thread(target=shutdown).start()
    else:
        logging.warning(f'unauthorized attempt to kill: {user.name} (id={user.id})')
        update.message.reply_text('Sorry, but you have no power to kill me.')


def callbacks_handler(update, context):
    # type: (Update, CallbackContext) -> None

    q = update.callback_query
    answer = None
    if q.data == 'awaiting_data':
        answer = 'I am waiting for your answer'
        awaiting_data = context.user_data.get('awaiting_data', [])
        if awaiting_data:
            message = awaiting_data[0][1]
        else:
            message = answer
        update.effective_user.send_message(message)
    q.answer(answer)


def markdown_escape(text, escape_chars=r'_*[]()~`>#+-=|{}.!'):
    """based on telegram.utils.helpers.escape_markdown"""
    return re.sub('([{}])'.format(re.escape(escape_chars)), r'\\\1', text)


def format_time(h=0, m=0):
    if h is None or m is None:
        return '-'
    return f'{(int(h) + (m // 60)):02}:{int((60 * h + m) % 60):02}'


def gmail(update, context):
    # type: (Update, CallbackContext) -> [None, Resource]

    logger = logging.getLogger()
    gmail_settings = context.user_data.get('gmail', {})

    credentials = gmail_settings.get('credentials', None)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logger.debug(f'updating existing credentials')
            credentials.refresh(Request())
        else:
            logger.debug(f'requesting credentials')
            oauth_secret_filename = settings['access']['google_api']['oauth20_secret_file']
            flow = Flow.from_client_secrets_file(
                oauth_secret_filename,
                scopes=['https://www.googleapis.com/auth/gmail.modify'],
                redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                state=gmail_settings.get('oauth2_state', 'None')
            )

            if 'auth_code' in gmail_settings:
                auth_code = gmail_settings.pop('auth_code')
                flow.fetch_token(code=auth_code)
                credentials = flow.credentials
                gmail_settings['credentials'] = credentials
            else:
                auth_url, gmail_settings['oauth2_state'] = flow.authorization_url(prompt='consent')
                context.user_data.setdefault('awaiting_data', []).append(
                    ('gmail/auth_code',
                     'Please send me the auth code that you get from the link')
                )
                if update.effective_chat.type != 'private':
                    message = markdown_escape('Authentication required!'
                                              ' Please, go to the in a'
                                              ' [PRIVATE](https://t.me/a_work_assistant_bot) chat'
                                              ' to pass authentication process',
                                              r'!')
                    update.message.reply_markdown_v2(message)
                private_message = markdown_escape('To continue, you have to '
                                                  'sign in to your Google account '
                                                  'and allow requested access for that bot.\n'
                                                  'As a result, you''ll receive confirmation code '
                                                  'which you have to send to me in that chat.'
                                                  , r'.')
                private_reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton('Sign in to Google', url=auth_url, callback_data='awaiting_data')]
                ])
                update.effective_user.send_message(private_message,
                                                   parse_mode=ParseMode.MARKDOWN_V2,
                                                   reply_markup=private_reply_markup)
                return None
    gmail_api = build('gmail', 'v1', credentials=credentials)
    return gmail_api


def gmail_labels(update, context):
    # type: (Update, CallbackContext) -> None

    gmail_api = gmail(update, context)
    if gmail_api:
        response = gmail_api.users().labels().list(userId='me').execute()
        reply_text = ''
        for label in response.get('labels', []):
            reply_text += f"{label['name']} ({label['id']})\n"
        update.message.reply_text(reply_text)


def redmine_auth(update, context):
    if update.effective_chat.type != 'private':
        public_chat_message = markdown_escape("Access to Redmine hasn't setup yet!"
                                              ' Please, go to the in a'
                                              ' [PRIVATE](https://t.me/a_work_assistant_bot) chat'
                                              ' to setup it.',
                                              r'!.')
        update.message.reply_markdown_v2(public_chat_message)

    context.user_data.setdefault('awaiting_data', []).append(
        ('redmine/address',
         'Please send me the URL address of Redmine service')
    )
    context.user_data.setdefault('awaiting_data', []).append(
        ('redmine/auth_key',
         'Please send me the your auth key/token of Redmine service')
    )
    private_message = markdown_escape('To continue, you have to '
                                      'send me some data to access Redmine.'
                                      , r'.')
    update.effective_user.send_message(private_message,
                                       parse_mode=ParseMode.MARKDOWN_V2)
    update.effective_user.send_message(context.user_data['awaiting_data'][0][1])



def get_redmine(update, context):
    from redminelib import Redmine

    redmine_settings = context.user_data.get('redmine', {})
    redmine_address = redmine_settings.get('address', None)
    redmine_auth_key = redmine_settings.get('auth_key', None)

    redmine_client = None
    if redmine_address and redmine_auth_key:
        redmine_client = Redmine(redmine_address, key=redmine_auth_key)
        return redmine_client, redmine_address

    return None, redmine_address


def redmine_ticket_info(redmine_client, redmine_address, ticket_number):
    info = {}
    try:
        ticket_data = redmine_client.issue.get(ticket_number)
        info['id'] = ticket_number
        info['title'] = getattr(ticket_data, "subject", "-")
        info['status'] = getattr(ticket_data, "status", "-")
        info['assigned_to'] = getattr(ticket_data, "assigned_to", "-")
        info['total_time'] = getattr(ticket_data, "total_spent_hours", "-")
        info['link'] = urljoin(redmine_address, f'issues/{ticket_number}')

        for time_entry in ticket_data.time_entries:
            info.setdefault('notes', []).append({
                    'subject':time_entry.comments,
                    'type': time_entry.activity.name,
                    'created': time_entry.created_on,
                    'spent_on': time_entry.spent_on,
                    'from_user': time_entry.user.name,
                    'hours': time_entry.hours,
                    'attrs': []
                    })
    except Exception as e:
        info['exception'] = e
        info['traceback'] = traceback.format_exc()

    return info


def redmine(update, context):
    # type: (Update, CallbackContext) -> None

    redmine_client, redmine_address = get_redmine(update, context)
    if redmine_client:
        message = ''
        for ticket_number in ','.join(context.args).split(','):
            ticket_info = redmine_ticket_info(redmine_client, redmine_address, ticket_number)
            if not ticket_info.get('exception'):
                ticket_name = md2_prepare(f'#{ticket_number}: {ticket_info["title"]}')
                message += f'[{ticket_name}]({ticket_info["link"]})\n'
                message += md2_prepare(f'[{ticket_info["status"]}]'
                                       f' {ticket_info["assigned_to"]}'
                                       f' ({format_time(ticket_info["total_time"])})\n')
                if ('-f' in context.args):
                    for ticket_note in ticket_info["notes"]:
                        message += md2_prepare(f' - {ticket_note["spent_on"]} {format_time(ticket_note["hours"])} {ticket_note["from_user"]} \n')
                message += '\n'
            else:
                caption = f"Exception for #{ticket_number}:\n{ticket_info.get('exception')}"
                trace_log = ticket_info.get('traceback')
                if trace_log:
                    import tempfile
                    with tempfile.TemporaryFile() as tf:
                        tf.write(trace_log.encode('utf-8'))
                        tf.seek(0)
                        update.message.reply_document(tf, caption=caption, filename='traceback.txt')
                else:
                    update.message.reply_text(caption)
        update.message.reply_text(message or 'No data', parse_mode=ParseMode.MARKDOWN_V2)
    else:
        redmine_auth(update, context)


def otrs_auth(update, context):
    if update.effective_chat.type != 'private':
        public_chat_message = markdown_escape("Access to OTRS hasn't setup yet!"
                                              ' Please, go to the in a'
                                              ' [PRIVATE](https://t.me/a_work_assistant_bot) chat'
                                              ' to setup it.',
                                              r'!.')
        update.message.reply_markdown_v2(public_chat_message)

    context.user_data.setdefault('awaiting_data', []).append(
        ('otrs/address',
         'Please send me the URL address of OTRS service')
    )
    context.user_data.setdefault('awaiting_data', []).append(
        ('otrs/username',
         'Please send me the your username for OTRS service')
    )
    context.user_data.setdefault('awaiting_data', []).append(
        ('otrs/password',
         'Please send me the your password for OTRS service')
    )
    private_message = markdown_escape('To continue, you have to '
                                      'send me some data to access OTRS.'
                                      , r'.')
    update.effective_user.send_message(private_message,
                                       parse_mode=ParseMode.MARKDOWN_V2)
    update.effective_user.send_message(context.user_data['awaiting_data'][0][1])


def get_otrs(update, context):
    from otrs.ticket.template import GenericTicketConnectorSOAP
    from otrs.client import GenericInterfaceClient
    from otrs.ticket.objects import Ticket, Article, DynamicField, Attachment

    otrs_settings = context.user_data.get('otrs', {})
    otrs_address = otrs_settings.get('address', None)
    otrs_username = otrs_settings.get('username', None)
    otrs_password = otrs_settings.get('password', None)
    webservice_name = 'GenericTicketConnectorSOAP'

    if otrs_address and otrs_username and otrs_password:
        client = GenericInterfaceClient(otrs_address, tc=GenericTicketConnectorSOAP(webservice_name))
        client.tc.SessionCreate(user_login=otrs_username, password=otrs_password)
        return client, otrs_address

    return None, None


def otrs_ticket_info(otrs_client, otrs_address, ticket_number):
    info = {}

    if otrs_client:
        try:
            ticket = otrs_client.tc.TicketGet(ticket_number, get_articles=True, get_dynamic_fields=True, get_attachments=False)
            info['id'] = ticket_number
            info['title'] = ticket.attrs.get('Title', '-')
            info['status'] = ticket.attrs.get('State', '-')
            info['assigned_to'] = ticket.attrs.get('Owner', '-')
            info['comment'] = ticket.attrs.get('Owner', '-')
            plan_time_str = ticket.attrs.get('DynamicField_Plantime', None)
            info['total_time'] = int(plan_time_str) if plan_time_str is not None else None
            info['link'] = urljoin(otrs_address, f'otrs/index.pl?Action=AgentTicketZoom;TicketID={ticket_number}')
            info['attrs'] = ticket.attrs

            for article in ticket.articles():
                info.setdefault('notes', []).append({
                        'subject':article.attrs.get('Subject', '-'),
                        'type': article.attrs.get('ArticleType'),
                        'created': article.attrs.get('Created', '-'),
                        'spent_on': None,
                        'from_user': article.attrs.get('FromRealname', '-'),
                        'hours': None,
                        'attrs': article.attrs
                        })
        except Exception as e:
            info['exception'] = e
            info['traceback'] = traceback.format_exc()

    return info


def otrs(update, context):
    # type: (Update, CallbackContext) -> None

    otrs_client, otrs_address = get_otrs(update, context)

    if otrs_client:
        issues = [int(i) for i in ','.join(context.args).split(',') if i.isdigit()]
        message = ''
        for num in issues:
            info = otrs_ticket_info(otrs_client, otrs_address, num)
            if not info.get('exception'):
                issue_name = md2_prepare(f"#{num}: {info['title']}")
                message += f'[{issue_name}]({info["link"]})\n'
                formatted_time = format_time(m=info['total_time'])
                message += md2_prepare(f"[{info['status']}] (Плановое время: {formatted_time})\n")
                if ('-f' in context.args):
                    for note in info.get('notes', []):
                        # I use subject template `(Ф:0+30) comment`
                        # for adding internal note/article about spent time
                        if note.get('type') == 'note-internal' \
                                and note.get('subject', '').startswith('('):
                            message += md2_prepare(f"- {note['created']} ({note['from_user']}): {note['subject']}\n")
                message += '\n'
            else:
                caption = f"Exception for #{num}:\n{info.get('exception')}"
                trace_log = info.get('traceback')
                if trace_log:
                    import tempfile
                    with tempfile.TemporaryFile() as tf:
                        tf.write(trace_log.encode('utf-8'))
                        tf.seek(0)
                        update.message.reply_document(tf, caption=caption, filename='traceback.txt')
                else:
                    update.message.reply_text(caption)
        update.message.reply_text(message or 'No data', parse_mode=ParseMode.MARKDOWN_V2)
    else:
        otrs_auth(update, context)



def help(update: Update, context: CallbackContext):
    help_lines = [
        '- /help - shows that message',
        '- /otrs_auth - starts process of authentication in OTRS (requests a few data, required to get access to OTRS)',
        '- /otrs `TASK_ID[,TASK_ID]` - shows info about tasks from OTRS with specified `TASK_ID`',
        '- /redmine_auth - starts process of authentication in Redmine',
        '- /redmine `TASK_ID[,TASK_ID]` - shows info about tasks in Redmine with specified `TASK_ID`',
    ]
    update.message.reply_markdown_v2(md2_prepare('\n'.join(help_lines)))


def error_handler(update: Update, context: CallbackContext):
    context.bot.send_message(update.effective_chat.id,
                             f'Internal exception: {str(context.error)}')
    raise context.error


def test(update: Update, context: CallbackContext):
    from pprint import pformat
    import tempfile

    for ticket_number in ','.join(context.args).split(','):
        if not otrs_num.isdigit():
            update.message.reply_text(f'incorrect arg: "{otrs_num}"')
            continue

        with tempfile.TemporaryFile() as f:
            otrs_client, otrs_address = get_otrs(update, context)
            if otrs_client:
                info = otrs_ticket_info(otrs_client, otrs_address, int(ticket_number))
                f.write(pformat(info).encode('utf-8'))
                f.seek(0)

            redmine_client, redmine_address = get_redmine(update, context)
            if redmine_client:
                info = redmine_ticket_info(redmine_client, redmine_address, int(ticket_number))
                f.write(pformat(info).encode('utf-8'))

            f.seek(0)
            update.message.reply_document(f, filename=f'{ticket_number}.txt')


def eternity(update: Update, context: CallbackContext):
    attachment_info = context.user_data.get('attachment', None)

    if not attachment_info:
        update.message.reply_text('Send me csv file before')
        return


    mime_type = attachment_info.get('mime_type', None)
    if mime_type not in ('text/csv', 'text/comma-separated-values'):
        update.message.reply_text(f"'text/csv' expected, but {mime_type} got")
        return

    file_id = attachment_info.get('file_id', None)
    if not file_id:
        update.message.reply_text('Empty file_id')
        return

    source_file = context.bot.get_file(file_id)
    if not source_file:
        update.message.reply_text("Couldn't get file by its file_id {file_id}")
        return

    downloaded_path = source_file.download()
    if not os.path.isfile(downloaded_path):
        update.message.reply_text(f"Could't find file {downloaded_path}")
        return

    try:
        import csv

        otrs_client, otrs_address = get_otrs(update, context)
        redmine_client, redmine_address = get_redmine(update, context)

        summary = {}
        task_number_pattern = re.compile(r'(\d+)\..*')
        with open(downloaded_path, newline='', encoding='utf-8') as f:
            cr = csv.reader(f)
            header = next(cr)
            if not (header and ','.join(header) == 'day,start time,stop time,duration,hierarchy path,activity name,note,tags'):
                update.message.reply_text(f"Unsupported csv structurem {header}")
                return



            for row in cr:
                date, start, end, duration, client, task, comment, tags = row
                if date == 'day':
                    continue
                if 'archive' in client:
                    continue 

                task_key = task
                otrs_info = {}
                redmine_info = {}

                match = task_number_pattern.match(task)
                if match:
                    task_key = match.group(1)
                    if otrs_client and int(task_key) < 99999:
                        otrs_info = otrs_ticket_info(otrs_client, otrs_address, task_key)
                    if redmine_client and int(task_key) > 100000:
                        redmine_info = redmine_ticket_info(redmine_client, redmine_address, task_key)


                task_info = summary.setdefault(client, {}).setdefault(task_key, {})
                task_info['otrs_info'] = otrs_info
                task_info['redmine_info'] = redmine_info
                eternity_info = task_info.setdefault('eternity_info', {})

                eternity_info[f'{date} {start} - {end}'] = {
                    'duration': duration,
                    'comment': comment,
                    'tags': tags,
                }

        if 'report' in context.args:
            import tempfile
            with tempfile.TemporaryFile() as f:
                f.write(f'# Report from {update.message.document.file_name}\n\n'.encode('utf-8'))

                for client in sorted(summary.keys()):
                    f.write(f'## {client or "-"}\n\n'.encode('utf-8'))

                    for task_key in sorted(summary[client].keys()):
                        task_info = summary[client][task_key]
                        f.write(f'### {task_key}\n\n'.encode('utf-8'))

                        eternity_info = task_info['eternity_info']
                        f.write(f'- Eternity\n'.encode('utf-8'))
                        for time_key in sorted(eternity_info.keys()):
                            comment = eternity_info[time_key]['comment']
                            tags = eternity_info[time_key]['tags']
                            duration = eternity_info[time_key]['duration']
                            f.write(f'    - {time_key} ({duration}, {tags}):'.encode('utf-8'))
                            if '\n' in comment:
                                f.write(f'\n'.encode('utf-8'))
                                f.write(f'        ```'.encode('utf-8'))
                                for line in comment.split('\n'):
                                    f.write(f'        {line}\n'.encode('utf-8'))
                                f.write(f'        ```'.encode('utf-8'))
                            else:
                                f.write(f' {comment}'.encode('utf-8'))
                            f.write(f'\n'.encode('utf-8'))

                        otrs_info = task_info['otrs_info']
                        ticket_id = otrs_info.get('id', None)
                        exception = otrs_info.get('exception', None)
                        if ticket_id or exception:
                            f.write(f'- OTRS'.encode('utf-8'))
                            ticket_status = otrs_info.get('status', None)
                            ticket_link= otrs_info.get('link', None)
                            ticket_title = otrs_info.get('title', '')
                            ticket_total_time = redmine_info.get('total_time', None)
                            if ticket_total_time:
                                ticket_total_time = format_time(m=ticket_total_time)
                            ticket_notes = otrs_info.get('notes', [])
                            if ticket_id:
                                f.write(f' ({ticket_status}, {ticket_total_time}):'.encode('utf-8'))
                                f.write(f' [#{ticket_id} {ticket_title}]({ticket_link})\n'.encode('utf-8'))
                            elif exception:
                                f.write(f': Exception {exception}\n'.encode('utf-8'))
                            for time_note in ticket_notes:
                                if (time_note.get('type') == 'note-internal'
                                        and time_note.get('subject', '').startswith('(')):
                                    f.write(f"    - {time_note['created']} ({time_note['from_user']}): {time_note['subject']}\n".encode('utf-8'))

                        redmine_info = task_info['redmine_info']
                        ticket_id = redmine_info.get('id', None)
                        exception = redmine_info.get('exception', None)
                        if ticket_id or exception:
                            f.write(f'- Redmine'.encode('utf-8'))
                            ticket_status = redmine_info.get('status', None)
                            ticket_link= redmine_info.get('link', None)
                            ticket_title = redmine_info.get('title', '')
                            ticket_total_time = redmine_info.get('total_time', None)
                            if ticket_total_time:
                                ticket_total_time = format_time(h=ticket_total_time)
                            ticket_notes = redmine_info.get('notes', [])
                            if ticket_id:
                                f.write(f' ({ticket_status}, {ticket_total_time}):'.encode('utf-8'))
                                f.write(f' [#{ticket_id} {ticket_title}]({ticket_link})\n'.encode('utf-8'))
                            elif exception:
                                f.write(f': Exception {exception}\n'.encode('utf-8'))
                            for time_note in ticket_notes:
                                f.write(f"    - {time_note['spent_on']} ({time_note['from_user']}, {format_time(h=time_note['hours'])}): {time_note['subject']}\n".encode('utf-8'))
                        f.write(f'\n\n\n'.encode('utf-8'))
                f.seek(0)
                update.message.reply_document(f, filename=f'Report.md')
        else:
            for client, tasks in sorted(summary.items(), key=lambda kv: kv[0]):
                message = md2_prepare(f'{client}\n')
                for task_key, task_info in sorted(tasks.items(), key=lambda kv: kv[0]):
                    info = task_info['otrs_info'] or task_info['redmine_info']
                    task_id = info.get('id')
                    if not task_id:
                        continue
                    task_title = info.get('title')
                    task_link = info.get('link')
                    link_caption = md2_prepare(f'#{task_id} {task_title}')
                    task_status = info.get('status', None)
                    message += md2_prepare(f'- ') + f'[#{link_caption}]({task_link})' + md2_prepare(f' ({task_status})\n')
                if message:
                    context.bot.send_message(update.effective_chat.id, message) 
    finally:
        os.remove(downloaded_path)



def process_attachment(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in settings['access']['god_id_list']:
        update.message.reply_text(f'Your user ID is {user.id}')
        username = f'{user.username} ({user.name}, {user.full_name})'
        update.message.reply_text(f'{username}, I cannot proccess that file for you, you have no permissions (your ID is {user.id})')
        return

    attachment = update.message.effective_attachment
    context.user_data['attachment'] = {
        'file_id': attachment.file_id,
        'mime_type': attachment.mime_type
    }

    update.message.reply_text("Thank's, I'll use it for you later")


def main():
    data_storage = PicklePersistence('bot.data')
    updater = Updater(token=settings['access']['token'],
                      persistence=data_storage,
                      use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('die', die))
    dispatcher.add_handler(CommandHandler('gmail_labels', gmail_labels))
    dispatcher.add_handler(CommandHandler('redmine', redmine))
    dispatcher.add_handler(CommandHandler('redmine_auth', redmine_auth))
    dispatcher.add_handler(CommandHandler('otrs', otrs))
    dispatcher.add_handler(CommandHandler('otrs_auth', otrs_auth))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('test', test))
    dispatcher.add_handler(CommandHandler('eternity', eternity))
    dispatcher.add_handler(CallbackQueryHandler(callbacks_handler))
    dispatcher.add_handler(MessageHandler(Filters.attachment, process_attachment))

    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.status_update, user_message))

    dispatcher.add_error_handler(error_handler)

    logging.info('start polling...')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
