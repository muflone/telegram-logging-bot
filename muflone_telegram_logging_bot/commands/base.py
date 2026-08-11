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

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3
    from typing import Callable, Optional, Self

    import telegram
    import telegram.ext

    from ..bot import Bot


class BaseCommand(object):
    trigger: Optional[str] = None
    description: Optional[str] = None

    def __init__(self,
                 bot: Bot):
        self.bot = bot

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
        return None

    async def execute(self,
                      update: telegram.Update,
                      context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                      *args,
                      **kwargs
                      ) -> None:
        """
        Get reply text and send response
        """
        print(f'{self.__class__.__name__}.execute')
        reply_text = self.get_reply_text(update=update,
                                         context=context,
                                         args=args,
                                         kwargs=kwargs)
        if reply_text is not None:
            await update.message.reply_text(reply_text)

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
                if command.trigger in commands:
                    raise ValueError(
                        f'Duplicate command name: {command.trigger}')
                commands[command_class.__name__] = command
        return commands

    def update_database_schema(self,
                               connection: sqlite3.Connection,
                               ) -> None:
        """
        Update database schema

        :param connection: database connection
        """
        return None

    def get_background_tasks(self) -> tuple[Callable]:
        """
        Get tuple of background tasks

        :return: tuple of async tasks
        """
        return ()
