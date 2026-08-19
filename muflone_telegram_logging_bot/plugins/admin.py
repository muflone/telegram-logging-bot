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


class PluginAdmin(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='admin_reload',
                             description='Reload admin settings',
                             callback=self.do_command_admin_reload,
                             include_in_list=False,
                             sequence=800),
            self.new_command(trigger='admin_set_bot_owners',
                             description='Set bot owners',
                             callback=self.do_command_admin_set_bot_owners,
                             include_in_list=False,
                             sequence=801),
            self.new_command(trigger='admin_set_bot_admins',
                             description='Set bot admins',
                             callback=self.do_command_admin_set_bot_admins,
                             include_in_list=False,
                             sequence=802),
            self.new_command(trigger='admin_set_excluded',
                             description='Set excluded users',
                             callback=self.do_command_admin_set_excluded,
                             include_in_list=False,
                             sequence=803),
        )

    @BasePlugin.call_command
    async def do_command_admin_reload(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        self.bot.settings.load()
        await update.effective_message.reply_text(
            text='Global settings reloaded')

    @BasePlugin.call_command
    async def do_command_admin_set_bot_owners(
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
            if action == 'add':
                self.bot.settings.add_global_user(group_name='bot_owners',
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to bot owners')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name='bot_owners',
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from bot owners')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_set_bot_admins(
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
            if action == 'add':
                self.bot.settings.add_global_user(group_name='bot_admins',
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to bot admins')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name='bot_admins',
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from bot admins')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_set_excluded(
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
            if action == 'add':
                self.bot.settings.add_global_user(group_name='denied_users',
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to excluded users')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name='denied_users',
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from excluded users')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')
