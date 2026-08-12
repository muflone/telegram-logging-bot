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

import asyncio
from typing import TYPE_CHECKING

import telegram

from .base import BaseCommand
from ..database import Database
from .. import extras

if TYPE_CHECKING:
    import sqlite3
    from typing import Callable, Optional

    import telegram.ext


class CommandMembersCount(BaseCommand):
    trigger: Optional[str] = 'members_count'
    description: Optional[str] = 'Collect members count statistics'

    def get_reply_text(self,
                       update: telegram.Update,
                       context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                       *args,
                       **kwargs
                       ) -> Optional[str]:
        """
        Get text to reply for trigger

        :return: returned string
        """
        return 'Members count statistics collected'

    async def execute(self,
                      update: telegram.Update,
                      context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                      *args,
                      **kwargs
                      ) -> None:
        """
        Get reply text and send response
        """
        await self.collect_members_count(source=f'/{self.trigger}')
        return await super().execute(update=update,
                                     context=context,
                                     args=args,
                                     kwargs=kwargs)

    async def collect_members_count(self,
                                    source: str,
                                    ) -> dict[int, int]:
        """
        Collect the members count for all the groups
        :param source: source type
        :return: dictionary with group_id and members count
        """
        result = {}
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            database = Database(filepath=db_path)
            try:
                members_count = await self.bot.bot.get_chat_member_count(
                    chat_id=chat_id)
                with database.open() as connection:
                    self.update_database_schema(connection=connection)
                    connection.execute(
                        '''
                        INSERT INTO members_count (
                            chat_id,
                            total,
                            source,
                            taken_at
                        )
                        VALUES (?, ?, ?, ?)
                        ''',
                        (
                            chat_id,
                            members_count,
                            source,
                            extras.utc_now_iso(),
                        ),
                    )
                    connection.commit()
            except telegram.error.TelegramError as error:
                print({
                    'name': self.__class__.__name__,
                    'event': 'members_count_get_chat_member_count_error',
                    'chat_id': chat_id,
                    'error': str(error),
                })
                continue
            result[chat_id] = members_count
            print({
                'name': self.__class__.__name__,
                'chat_id': chat_id,
                'members_count': members_count,
                'source': source,
            })
        return result

    def get_background_tasks(self) -> tuple[Callable]:
        """
        Get background tasks

        :return: tuple of async tasks
        """
        return (self.collect_members_count_hourly(),)

    async def collect_members_count_hourly(self) -> None:
        """
        Collect the members count for all the groups every hour
        """
        await self.collect_members_count(source='startup')
        while True:
            await asyncio.sleep(60 * 60)
            await self.collect_members_count(source='hourly')

    def update_database_schema(self,
                               connection: sqlite3.Connection,
                               ) -> None:
        """
        Update database schema

        :param connection: database connection
        """
        connection.executescript(
            '''
            CREATE TABLE IF NOT EXISTS members_count (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                total INTEGER NOT NULL,
                source TEXT NOT NULL,
                taken_at TEXT NOT NULL
            );
            '''
        )
        return super().update_database_schema(connection=connection)
