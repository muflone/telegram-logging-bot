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


class PluginDetails(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='chat_details',
                             description='Chat details',
                             callback=self.do_command_chat_details,
                             include_in_list=False,
                             sequence=30),
        )

    @BasePlugin.call_command
    async def do_command_chat_details(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        chat = update.effective_chat
        chat_details = await context.bot.get_chat(chat.id)
        await update.effective_message.reply_text(
            text=('Chat details:\n'
                  '\n'
                  f'Type: {chat.type or ''}\n'
                  f'ID: {chat.id}\n'
                  f'Name: {chat.username or ''}\n'
                  f'Title: {chat.title or ''}\n'
                  f'Description: {chat_details.description or ''}\n'
                  f'Link: {chat.link or ''}'),
            disable_web_page_preview=True)
