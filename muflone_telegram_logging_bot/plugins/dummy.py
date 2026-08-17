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

import logging
from typing import TYPE_CHECKING

import telegram.ext

from .base import BasePlugin
from ..trigger import Trigger

if TYPE_CHECKING:
    from typing import Callable


class PluginDummy(BasePlugin):
    def get_triggers(self) -> tuple[Trigger, ...]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return (
            Trigger(trigger='dummy1',
                    description='Dummy command',
                    callback=self.do_trigger_1,
                    status=False),
            Trigger(trigger='dummy2',
                    description='Dummy command',
                    callback=self.do_trigger_2,
                    status=False),
        )

    @BasePlugin.call_trigger
    async def do_trigger_1(self,
                           update: telegram.Update,
                           context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                           trigger: Trigger,
                           ) -> None:
        await update.effective_message.reply_text(
            text='dummy1')

    @BasePlugin.call_trigger
    async def do_trigger_2(self,
                           update: telegram.Update,
                           context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                           trigger: Trigger,
                           ) -> None:
        await update.effective_message.reply_text(
            text='dummy2')

    def get_background_tasks(self) -> tuple[Callable, ...]:
        """
        Get background tasks

        :return: tuple of async tasks
        """
        return (
            self.do_background_task_dummy1,
            self.do_background_task_dummy2,
        )

    async def do_background_task_dummy1(self) -> None:
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            logging.info({
                'name': f'{self.__class__.__name__}.do_background_task_dummy1',
                'chat_id': chat_id,
            })

    async def do_background_task_dummy2(self) -> None:
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            logging.info({
                'name': f'{self.__class__.__name__}.do_background_task_dummy2',
                'chat_id': chat_id,
            })
