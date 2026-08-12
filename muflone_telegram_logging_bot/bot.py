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

import telegram.ext

from .commands.base import BaseCommand
from .databases import Databases

if TYPE_CHECKING:
    import pathlib


class Bot:
    def __init__(self,
                 token: str,
                 data_dir: pathlib.Path):
        self.application = None
        self.bot = None
        self.telegram_token = token
        self.commands = None
        self.databases = Databases(filepath=data_dir)
        self.triggers = {}
        self.background_tasks = []

    def run(self) -> None:
        """
        Run the bot
        """
        self.commands = BaseCommand.load_commands(bot=self)
        for command in self.commands.values():
            # Collect background tasks for each command
            if new_tasks := command.get_background_tasks():
                self.background_tasks.extend(new_tasks)
        self.application = (telegram.ext.Application.builder()
                            .token(token=self.telegram_token)
                            .post_init(self.start_background_tasks)
                            .build()
                            )
        self.bot = self.application.bot
        # Setup commands
        for command in self.commands.values():
            command.setup(app=self.application)
        # Run the bot
        self.application.run_polling(
            allowed_updates=telegram.Update.ALL_TYPES)

    async def start_background_tasks(self,
                                     app: telegram.ext.Application):
        """
        Start all the background tasks from each command
        """
        for task in self.background_tasks:
            asyncio.create_task(task())
