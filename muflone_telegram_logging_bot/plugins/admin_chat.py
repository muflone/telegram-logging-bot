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

import prettytable

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
            self.new_command(trigger='admin_chat_list_chat_admins',
                             description='List chat admins',
                             callback=self.do_command_admin_list_chat_admins,
                             parameters=None,
                             include_in_list=False,
                             sequence=910),
            self.new_command(trigger='admin_chat_set_chat_admins',
                             description='Set chat admins',
                             callback=self.do_command_admin_set_chat_admins,
                             parameters=None,
                             include_in_list=False,
                             sequence=911),
            self.new_command(trigger='admin_chat_list_denied_users',
                             description='List denied users',
                             callback=self.do_command_admin_list_denied_users,
                             parameters=None,
                             include_in_list=False,
                             sequence=920),
            self.new_command(trigger='admin_chat_set_denied_users',
                             description='Set denied users',
                             callback=self.do_command_admin_set_denied_users,
                             parameters=None,
                             include_in_list=False,
                             sequence=921),
            self.new_command(trigger='admin_chat_list_parameters',
                             description='List command parameters',
                             callback=self.do_command_admin_list_parameters,
                             parameters=None,
                             include_in_list=False,
                             sequence=930),
            self.new_command(trigger='admin_chat_set_parameters',
                             description='Set command parameters',
                             callback=self.do_command_admin_set_parameters,
                             parameters=None,
                             include_in_list=False,
                             sequence=931),
        )

    @BasePlugin.call_command
    async def do_command_admin_list_chat_admins(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        chat = update.effective_chat
        users_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_chat_data(
                chat_id=str(chat.id),
                list_name=CHAT_ADMINS)))
        await update.effective_message.reply_text(
            text=(f'Chat admins for {chat.id}:\n'
                  '\n'
                  f'{users_list or 'None'}'))

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

    @BasePlugin.call_command
    async def do_command_admin_list_denied_users(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        chat = update.effective_chat
        users_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_chat_data(
                chat_id=str(chat.id),
                list_name=DENIED_USERS)))
        await update.effective_message.reply_text(
            text=(f'Denied users for {chat.id}:\n'
                  '\n'
                  f'{users_list or 'None'}'))

    @BasePlugin.call_command
    async def do_command_admin_set_denied_users(
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
                                                access_list=DENIED_USERS,
                                                user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to denied users')
            elif action == 'remove':
                self.bot.settings.remove_chat_user(chat_id=str(chat.id),
                                                   access_list=DENIED_USERS,
                                                   user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from denied users')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_list_parameters(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        args = context.args
        if len(args) < 1:
            await update.effective_message.reply_text(
                text=('Invalid arguments:\n'
                      '\n'
                      f'Usage:\n'
                      f'/{command.trigger} <command>'
                      ))
        else:
            command_name = args[0]
            chat = update.effective_chat
            if command_name not in self.bot.commands:
                # Invalid command name
                await update.effective_message.reply_text(
                    text=(f'Invalid command {command_name}'))
            elif not self.bot.commands[command_name].parameters:
                # The command has not parameters
                await update.effective_message.reply_text(
                    text=(f'Command {command_name} has no parameters'))
            else:
                custom_parameters = self.bot.settings.get_command_parameters(
                        chat_id=str(chat.id),
                        command_name=command_name)
                # Prepare table for results
                table = prettytable.PrettyTable()
                table.field_names = ('Name',
                                     'Description',
                                     'Type',
                                     'Null',
                                     'Default',
                                     'Options',
                                     'Set',
                                     'Value')
                table.align = 'l'
                table.align['Custom'] = 'c'
                for item in sorted(
                        self.bot.commands[command_name].parameters.values(),
                        key=lambda item: item.name):
                    table.add_row(row=[
                        item.name,
                        item.description,
                        item.type,
                        item.null,
                        item.default,
                        item.options,
                        '✅' if item.name in custom_parameters else '❌',
                        item.parse_value(custom_parameters.get(item.name)),
                    ])
                await update.effective_message.reply_html(
                    text=f'<pre>{table.get_string()}</pre>')

    @BasePlugin.call_command
    async def do_command_admin_set_parameters(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        args = context.args
        if len(args) < 3:
            await update.effective_message.reply_text(
                text=('Invalid arguments:\n'
                      '\n'
                      f'Usage:\n'
                      f'/{command.trigger} set <command> <parameter> <value>\n'
                      f'/{command.trigger} unset <command> <parameter>'
                      ))
        else:
            action = args[0]
            command_name = args[1]
            parameter_name = args[2]
            parameter_value = ' '.join(args[3:]) if len(args) >= 4 else None
            chat = update.effective_chat
            if action == 'set':
                self.bot.settings.set_command_parameter(
                    chat_id=str(chat.id),
                    command_name=command_name,
                    parameter=parameter_name,
                    value=parameter_value)
                await update.effective_message.reply_text(
                    text=f'Command parameter {parameter_name} set')
            elif action == 'unset':
                self.bot.settings.unset_command_parameter(
                    chat_id=str(chat.id),
                    command_name=command_name,
                    parameter=parameter_name)
                await update.effective_message.reply_text(
                    text=f'Command parameter {parameter_name} unset')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')
