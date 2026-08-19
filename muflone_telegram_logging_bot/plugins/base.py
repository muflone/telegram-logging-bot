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

import functools
import importlib
import inspect
import logging
import pkgutil
import sqlite3
from typing import TYPE_CHECKING

import telegram.ext

from ..command import Command

if TYPE_CHECKING:
    from typing import Callable, Self

    import telegram

    from ..bot import Bot


class BasePlugin(object):
    def __init__(self,
                 bot: Bot):
        self.bot = bot

    @staticmethod
    def load_plugins(bot: 'Bot') -> dict[str, Self]:
        """
        Discover and instantiate all plugins available in this package.
        """
        plugins = {}
        plugins_package = importlib.import_module(__package__)
        for module_info in pkgutil.iter_modules(
                path=plugins_package.__path__,
                prefix=f'{plugins_package.__name__}.'):
            module = importlib.import_module(module_info.name)
            for _, plugin_class in inspect.getmembers(module,
                                                      inspect.isclass):
                if plugin_class is BasePlugin:
                    continue
                elif not issubclass(plugin_class, BasePlugin):
                    continue
                elif plugin_class.__module__ != module.__name__:
                    continue
                # Instance the plugin module
                plugin = plugin_class(bot=bot)
                plugins[plugin_class.__name__] = plugin
        return plugins

    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return ()

    @staticmethod
    def call_command(callback: Callable) -> Callable:
        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            command = args[0]
            logging.info(f'{command.__class__.__name__}.{callback.__name__}')
            return callback(*args, **kwargs)
        return wrapper

    def get_background_tasks(self) -> tuple[Callable, ...]:
        """
        Get background tasks

        :return: tuple of async tasks
        """
        return ()

    def setup(self,
              app: telegram.ext.Application) -> None:
        """
        Setup plugin logic
        """
        for command in self.get_commands():
            if command.trigger in self.bot.commands:
                raise ValueError(
                    f'Duplicate command name: {command.trigger}')
            self.bot.commands[command.trigger] = command
            logging.info(f'Setup command /{command.trigger} '
                         f'for {self.__class__.__name__}')
            app.add_handler(
                handler=telegram.ext.CommandHandler(
                    command=command.trigger,
                    callback=functools.partial(command.callback,
                                               command=command)),
                group=self.bot.next_handler_group)
        self.bot.next_handler_group += 1

    def update_database_schema(self,
                               connection: sqlite3.Connection,
                               ) -> None:
        """
        Update database schema

        :param connection: database connection
        """
        return

    def new_command(self,
                    trigger: str,
                    description: str,
                    callback: Callable,
                    include_in_list: bool,
                    sequence: int,
                    ) -> Command:
        """
        Create a new Command

        :param trigger: command trigger
        :param description: command description
        :param callback: command callback
        :param include_in_list: include in commands list
        :param sequence: ordering sequence
        :return: new Command object
        """
        return Command(plugin=self,
                       trigger=trigger,
                       description=description,
                       callback=callback,
                       include_in_list=include_in_list,
                       sequence=sequence)
