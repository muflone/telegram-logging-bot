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
                             parameters=None,
                             include_in_list=False,
                             sequence=30),
            self.new_command(trigger='user_details',
                             description='User details',
                             callback=self.do_command_user_details,
                             parameters=None,
                             include_in_list=False,
                             sequence=31),
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

    @BasePlugin.call_command
    async def do_command_user_details(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        chat = update.effective_chat
        user = update.effective_user
        user_details = await context.bot.get_chat(chat_id=user.id)
        chat_member = await context.bot.get_chat_member(chat_id=chat.id,
                                                        user_id=user.id)
        await update.effective_message.reply_text(
            text=('User details:\n'
                  '\n'
                  f'ID: {user.id}\n'
                  f'Name: {user.name or ''}\n'
                  f'Username: {user.username or ''}\n'
                  f'First name: {user.first_name or ''}\n'
                  f'Last name: {user.last_name or ''}\n'
                  f'Language: {user.language_code or ''}\n'
                  f'Link: {user.link or ''}\n'
                  f'Status: {chat_member.status}\n'
                  f'Bot: {user.is_bot}\n'
                  f'Premium: {user.is_premium}\n'
                  f'Bot Owner: {self.bot.settings.is_bot_owner(user=user)}\n'
                  f'Bot Admin: {self.bot.settings.is_bot_admin(user=user)}\n'
                  f'Bio: {user_details.bio or ''}'),
            disable_web_page_preview=True)
