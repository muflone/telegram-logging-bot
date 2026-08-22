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

import telegram.ext

from .base import BasePlugin
from ..command import Command
from ..parameter import Parameter, ParameterType


class PluginHello(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='hello',
                             description='Hello command',
                             callback=self.do_command,
                             parameters=(
                                 Parameter(name='greet',
                                           description='Greeting text',
                                           type=ParameterType.STRING,
                                           null=False,
                                           default='Hello {NAME}!'),
                             ),
                             include_in_list=False,
                             sequence=1002),
        )

    @BasePlugin.call_command
    async def do_command(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         command: Command,
                         ) -> None:
        chat = update.effective_chat
        user = update.effective_user
        await update.effective_message.reply_text(
            text=(
                self.bot.settings.get_command_parameter_value(
                    chat_id=str(chat.id),
                    command=command,
                    parameter='greet'
                ).format(NAME=user.full_name,
                         FIRST_NAME=user.first_name,
                         LAST_NAME=user.last_name,
                         USERNAME=user.username)
            )
        )
