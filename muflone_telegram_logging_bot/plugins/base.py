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

from ..trigger import Trigger

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

    def get_triggers(self) -> tuple[Trigger, ...]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return ()

    @staticmethod
    def call_trigger(callback: Callable) -> Callable:
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
        for trigger in self.get_triggers():
            if trigger.trigger in self.bot.triggers:
                raise ValueError(
                    f'Duplicate command name: {trigger.trigger}')
            if trigger.status:
                self.bot.triggers[trigger.trigger] = trigger
                logging.info(f'Setup trigger /{trigger.trigger} '
                             f'for {self.__class__.__name__}')
                app.add_handler(
                    handler=telegram.ext.CommandHandler(
                        command=trigger.trigger,
                        callback=functools.partial(trigger.callback,
                                                   trigger=trigger)),
                    group=self.bot.next_handler_group)
            else:
                logging.info(f'Skipped trigger /{trigger.trigger} '
                             f'for {self.__class__.__name__}')
        self.bot.next_handler_group += 1

    def update_database_schema(self,
                               connection: sqlite3.Connection,
                               ) -> None:
        """
        Update database schema

        :param connection: database connection
        """
        return
