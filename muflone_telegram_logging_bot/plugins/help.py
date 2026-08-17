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

from typing import TYPE_CHECKING

from .base import BasePlugin
from ..command import Command

if TYPE_CHECKING:
    import telegram
    import telegram.ext


class PluginHelp(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            Command(trigger='help',
                    description=None,
                    callback=self.do_command,
                    status=True),
        )

    @BasePlugin.call_command
    async def do_command(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         command: Command,
                         ) -> None:
        commands_description = []
        for command in self.bot.commands.values():
            if command.trigger and command.description:
                commands_description.append(
                    f'/{command.trigger}\n'
                    f'{command.description}\n')
        await update.effective_message.reply_text(
            text='\n'.join(commands_description) or
                 'No commands available.')
