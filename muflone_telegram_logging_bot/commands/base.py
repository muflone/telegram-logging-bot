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
from typing import TYPE_CHECKING

import telegram.ext

from ..trigger import Trigger

if TYPE_CHECKING:
    from typing import Callable, Self

    import telegram

    from ..bot import Bot


class BaseCommand(object):
    def __init__(self,
                 bot: Bot):
        self.bot = bot

    @staticmethod
    def load_commands(bot: 'Bot') -> dict[str, Self]:
        """
        Discover and instantiate all commands available in this package.
        """
        commands = {}
        commands_package = importlib.import_module(__package__)
        for module_info in pkgutil.iter_modules(
                path=commands_package.__path__,
                prefix=f'{commands_package.__name__}.'):
            module = importlib.import_module(module_info.name)
            for _, command_class in inspect.getmembers(module,
                                                       inspect.isclass):
                if command_class is BaseCommand:
                    continue
                elif not issubclass(command_class, BaseCommand):
                    continue
                elif command_class.__module__ != module.__name__:
                    continue
                # Instance the plugin module
                command = command_class(bot=bot)
                commands[command_class.__name__] = command
        return commands

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
        Setup command logic
        """
        for trigger in self.get_triggers():
            if trigger.trigger in self.bot.triggers:
                raise ValueError(
                    f'Duplicate command name: {trigger.trigger}')
            self.bot.triggers[trigger.trigger] = trigger
            logging.info(f'Setup trigger /{trigger.trigger} '
                         f'for {self.__class__.__name__}')
            app.add_handler(
                handler=telegram.ext.CommandHandler(
                    command=trigger.trigger,
                    callback=functools.partial(trigger.callback,
                                               trigger=trigger)),
                group=self.bot.next_handler_group)
        self.bot.next_handler_group += 1
