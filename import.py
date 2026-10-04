##
#     Project: Telegram Logging Bot
# Description: Telegram bot to log messages in Telegram groups
#      Author: Fabio Castelli (Muflone) <muflone@muflone.com>
#   Copyright: 2026 Fabio Castelli
#     License: GPL-3+
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

import argparse
import datetime
import json
import os
import pathlib
from typing import TYPE_CHECKING

import telegram

from muflone_telegram_logging_bot.constants import APP_NAME, APP_VERSION
from muflone_telegram_logging_bot.databases import Databases
from muflone_telegram_logging_bot.plugins.groups import PluginGroups

if TYPE_CHECKING:
    from typing import Any


def main():
    # Get command line arguments
    parser = argparse.ArgumentParser(prog=f'{APP_NAME} v{APP_VERSION}')
    parser.add_argument('-f',
                        '--file',
                        type=str,
                        required=True,
                        help='JSON file path to import')
    options = parser.parse_args()
    with open(options.file, 'r') as file:
        data = json.load(file)
    # Determine the chat_id from type
    if data['type'] in ('personal_chat', ):
        chat_id = data['id']
    elif data['type'] in ('private_group', ):
        chat_id = data['id'] * -1
    else:
        chat_id = -1_000_000_000_000 - data['id']
    # Import messages
    import_messages(data=data,
                    chat_id=chat_id)


def import_messages(data: dict[str, Any],
                    chat_id: int):
    # Get database connection
    databases = Databases(filepath=pathlib.Path(os.environ.get('APP_DATA_DIR',
                                                               'data')))
    database = databases.get_database(directory_name=str(chat_id))
    connection = database.open()
    # Load messages
    plugin = PluginGroups(None)
    plugin.load_users_cache_from_db(chat_id=chat_id,
                                    database=database)
    messages_data = list(filter(lambda item:
                                item.get('action') != 'migrate_from_group' and
                                item.get('type') in ('service', 'message'),
                                data['messages']))
    messages_count = len(messages_data)
    for index, line in enumerate(iterable=messages_data, start=1):
        print(f'Importing message {index} of {messages_count}')
        chat = telegram.Chat(
            id=chat_id,
            type=line['type'])
        if line['type'] == 'service':
            # Set user only
            user = telegram.User(
                id=int(line['actor_id']
                       .replace('user', '')
                       .replace('channel', '')),
                first_name=line['actor'],
                is_bot=False)
        elif line['type'] == 'message':
            # Set user
            user = telegram.User(
                id=int(line['from_id']
                       .replace('user', '')
                       .replace('channel', '')),
                first_name=line['from'],
                is_bot=False)
            # Save message
            message = telegram.Message(
                message_id=int(line['id']),
                date=(
                    datetime.datetime.fromtimestamp(
                        timestamp=int(line['date_unixtime']),
                        tz=datetime.timezone.utc)
                    if 'date_unixtime' in line
                    else None),
                chat=chat,
                from_user=user,
                reply_to_message=(
                    telegram.Message(
                        message_id=line['reply_to_message_id'],
                        date=None,
                        chat=chat)
                    if line.get('reply_to_message_id')
                    else None),
                text=(''.join([item['text']
                              for item in line['text_entities']])
                      if 'text_entities' in line
                      else None),
                caption=line.get('caption'),
                edit_date=(
                    datetime.datetime.fromtimestamp(
                        timestamp=int(line['edited_unixtime']),
                        tz=datetime.timezone.utc)
                    if 'edited_unixtime' in line
                    else None),
            )
            plugin.save_message(connection=connection,
                                chat=chat,
                                message=message,
                                user=user)
        plugin.save_user(connection=connection,
                         user=user,
                         chat=chat,
                         timestamp=datetime.datetime.fromtimestamp(
                             timestamp=int(line.get(
                                 'edited_unixtime',
                                 line['date_unixtime'])),
                             tz=datetime.timezone.utc))
    # Save and close
    connection.commit()
    connection.close()


if __name__ == '__main__':
    main()
