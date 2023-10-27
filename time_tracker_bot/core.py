import os

from .credentials import decrypt_credentials
from .otrs_tools import get_otrs_client


async def connect_to_otrs(credentials):
    endpoint = os.environ.get('TIME_TRACKER_BOT_OTRS_ENDPOINT')
    username, password = decrypt_credentials(credentials['name'], credentials['key'])

    otrs_client = await get_otrs_client(endpoint, username, password)
    return otrs_client