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
from ..settings import (CHAT_ADMINS,
                        DENIED_USERS)


class PluginAdminChat(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='admin_chat_set_chat_admins',
                             description='Set chat admins',
                             callback=self.do_command_admin_set_chat_admins,
                             include_in_list=False,
                             sequence=910),
        )

    @BasePlugin.call_command
    async def do_command_admin_set_chat_admins(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        args = context.args
        if len(args) < 2:
            await update.effective_message.reply_text(
                text=('Invalid arguments:\n'
                      '\n'
                      f'Usage:\n'
                      f'/{command.trigger} add <@username|user_id>\n'
                      f'/{command.trigger} remove <@username|user_id>'
                      ))
        else:
            action = args[0]
            value = args[1]
            chat = update.effective_chat
            if action == 'add':
                self.bot.settings.add_chat_user(chat_id=str(chat.id),
                                                access_list=CHAT_ADMINS,
                                                user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to chat admins')
            elif action == 'remove':
                self.bot.settings.remove_chat_user(chat_id=str(chat.id),
                                                   access_list=CHAT_ADMINS,
                                                   user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from chat admins')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')
