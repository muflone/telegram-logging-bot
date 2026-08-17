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
import logging
from typing import TYPE_CHECKING

import telegram

from .base import BaseCommand
from ..database import Database
from ..trigger import Trigger
from .. import extras

if TYPE_CHECKING:
    import sqlite3
    from typing import Callable

    import telegram.ext


class CommandMembersCount(BaseCommand):
    def get_triggers(self) -> tuple[Trigger, ...]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return (
            Trigger(trigger='members_count',
                    description='Collect members count statistics',
                    callback=self.do_trigger,
                    status=True),
        )

    @BaseCommand.call_trigger
    async def do_trigger(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         trigger: Trigger,
                         ) -> None:
        result = await self.collect_members_count(source='trigger')
        await update.effective_message.reply_text(
            text=f'Members count statistics collected: {result}')

    async def collect_members_count(self,
                                    source: str,
                                    ) -> dict[int, int]:
        """
        Collect the members count for all the groups
        :param source: source type
        :return: dictionary with group_id and members count
        """
        logging.info(f'{self.__class__.__name__}.collect_members_count')
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
                            total,
                            source,
                            taken_at
                        )
                        VALUES (?, ?, ?)
                        ''',
                        (
                            members_count,
                            source,
                            extras.utc_now_iso(),
                        ),
                    )
                    connection.commit()
            except telegram.error.TelegramError as error:
                logging.error({
                    'name': self.__class__.__name__,
                    'event': 'members_count_get_chat_member_count_error',
                    'chat_id': chat_id,
                    'error': str(error),
                })
                continue
            result[chat_id] = members_count
            logging.info({
                'name': self.__class__.__name__,
                'chat_id': chat_id,
                'members_count': members_count,
                'source': source,
            })
        return result

    def get_background_tasks(self) -> tuple[Callable, ...]:
        """
        Get background tasks

        :return: tuple of async tasks
        """
        return (
            self.do_collect_members_count_hourly,
        )

    async def do_collect_members_count_hourly(self) -> None:
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
                total INTEGER NOT NULL,
                source TEXT NOT NULL,
                taken_at TEXT NOT NULL
            );
            '''
        )
