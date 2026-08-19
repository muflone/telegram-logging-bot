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

from .databases import Databases
from .plugins.base import BasePlugin

if TYPE_CHECKING:
    import pathlib


class Bot:
    def __init__(self,
                 token: str,
                 data_dir: pathlib.Path):
        self.application = None
        self.bot = None
        self.telegram_token = token
        self.plugins = None
        self.databases = Databases(filepath=data_dir)
        self.commands = {}
        self.background_tasks = []
        self.next_handler_group = 1

    def run(self) -> None:
        """
        Run the bot
        """
        self.plugins = BasePlugin.load_plugins(bot=self)
        for plugin in self.plugins.values():
            # Collect background tasks for each plugin
            if new_tasks := plugin.get_background_tasks():
                self.background_tasks.extend(new_tasks)
        self.application = (telegram.ext.Application.builder()
                            .token(token=self.telegram_token)
                            .post_init(self.post_init)
                            .build()
                            )
        self.bot = self.application.bot
        # Setup plugins
        for plugin in self.plugins.values():
            plugin.setup(app=self.application)
        # Sort the commands by sequence
        self.commands = {
            key: self.commands[key]
            for key in sorted(self.commands,
                              key=lambda i: self.commands[i].sequence)
        }
        # Run the bot
        self.application.run_polling(
            allowed_updates=telegram.Update.ALL_TYPES)

    async def post_init(self,
                        app: telegram.ext.Application):
        """
        Set all the post init tasks
        """
        # Setup commands
        await self.bot.set_my_commands([
            telegram.BotCommand(command=command.trigger,
                                description=command.description)
            for command in self.commands.values()
            if (command.trigger and
                command.description and
                command.include_in_list)
        ])
        # Start all the background tasks from each plugin
        for task in self.background_tasks:
            asyncio.create_task(task())
