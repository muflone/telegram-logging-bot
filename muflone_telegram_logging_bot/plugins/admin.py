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
from ..settings import (BOT_ADMINS,
                        BOT_OWNERS,
                        COMMAND_ACCESS_LISTS,
                        COMMAND_SCOPE,
                        COMMAND_STATUS,
                        DENIED_USERS,
                        ENABLED_CHATS)


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
                             sequence=810),
            self.new_command(trigger='admin_list_bot_owners',
                             description='List bot owners',
                             callback=self.do_command_admin_list_bot_owners,
                             include_in_list=False,
                             sequence=820),
            self.new_command(trigger='admin_set_bot_owners',
                             description='Set bot owners',
                             callback=self.do_command_admin_set_bot_owners,
                             include_in_list=False,
                             sequence=821),
            self.new_command(trigger='admin_list_bot_admins',
                             description='List bot admins',
                             callback=self.do_command_admin_list_bot_admins,
                             include_in_list=False,
                             sequence=830),
            self.new_command(trigger='admin_set_bot_admins',
                             description='Set bot admins',
                             callback=self.do_command_admin_set_bot_admins,
                             include_in_list=False,
                             sequence=831),
            self.new_command(trigger='admin_list_denied_users',
                             description='List denied users',
                             callback=self.do_command_admin_list_denied_users,
                             include_in_list=False,
                             sequence=840),
            self.new_command(trigger='admin_set_denied_users',
                             description='Set denied users',
                             callback=self.do_command_admin_set_denied_users,
                             include_in_list=False,
                             sequence=841),
            self.new_command(trigger='admin_list_chats',
                             description='List enabled chats',
                             callback=self.do_command_admin_list_chats,
                             include_in_list=False,
                             sequence=850),
            self.new_command(trigger='admin_set_chats',
                             description='Set enabled chats',
                             callback=self.do_command_admin_set_chats,
                             include_in_list=False,
                             sequence=851),
            self.new_command(trigger='admin_list_commands',
                             description='List commands',
                             callback=self.do_command_admin_list_commands,
                             include_in_list=False,
                             sequence=860),
            self.new_command(trigger='admin_set_commands',
                             description='Set enabled commands',
                             callback=self.do_command_admin_set_commands,
                             include_in_list=False,
                             sequence=861),
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
    async def do_command_admin_list_bot_owners(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        users_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_global_data(
                list_name=BOT_OWNERS)))
        await update.effective_message.reply_text(
            text=('Bot owners:\n'
                  '\n'
                  f'{users_list or 'None'}'))

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
                self.bot.settings.add_global_user(group_name=BOT_OWNERS,
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to bot owners')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name=BOT_OWNERS,
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from bot owners')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_list_bot_admins(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        users_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_global_data(
                list_name=BOT_ADMINS)))
        await update.effective_message.reply_text(
            text=('Bot admins:\n'
                  '\n'
                  f'{users_list or 'None'}'))

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
                self.bot.settings.add_global_user(group_name=BOT_ADMINS,
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to bot admins')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name=BOT_ADMINS,
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from bot admins')
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
        users_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_global_data(
                list_name=DENIED_USERS)))
        await update.effective_message.reply_text(
            text=('Denied users:\n'
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
            if action == 'add':
                self.bot.settings.add_global_user(group_name=DENIED_USERS,
                                                  user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} added to denied users')
            elif action == 'remove':
                self.bot.settings.remove_global_user(group_name=DENIED_USERS,
                                                     user_reference=value)
                await update.effective_message.reply_text(
                    text=f'User {value} removed from denied users')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_list_chats(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        chats_list = '\n'.join(
            sorted(self.bot.settings.get_list_from_global_data(
                list_name=ENABLED_CHATS)))
        await update.effective_message.reply_text(
            text=('Enabled chats:\n'
                  '\n'
                  f'{chats_list or 'None'}'))

    @BasePlugin.call_command
    async def do_command_admin_set_chats(
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
                      f'/{command.trigger} add <chat_id|this>\n'
                      f'/{command.trigger} remove <chat_id|this>'
                      ))
        else:
            action = args[0]
            value = args[1]
            if value == 'this':
                value = str(update.effective_chat.id)
            if action == 'add':
                self.bot.settings.set_chat_enabled(chat_id=value,
                                                   status=True)
                await update.effective_message.reply_text(
                    text=f'Chat {value} has been enabled')
            elif action == 'remove':
                self.bot.settings.set_chat_enabled(chat_id=value,
                                                   status=False)
                await update.effective_message.reply_text(
                    text=f'Chat {value} has been disabled')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')

    @BasePlugin.call_command
    async def do_command_admin_list_commands(
            self,
            update: telegram.Update,
            context: telegram.ext.ContextTypes.DEFAULT_TYPE,
            command: Command,
    ) -> None:
        # Prepare table for results
        table = prettytable.PrettyTable()
        table.field_names = ('Command',
                             'Status',
                             'Access lists',
                             'Scope')
        table.align = 'l'
        table.align['Status'] = 'c'
        # Load commands settings
        commands_settings = self.bot.settings.get_enabled_commands()
        for item in sorted(self.bot.commands.values(),
                           key=lambda item: item.trigger):
            command_settings = commands_settings.get(item.trigger, {})
            table.add_row(row=[
                item.trigger,
                command_settings.get(COMMAND_STATUS, False) and '✅' or '❌',
                ','.join(command_settings.get(COMMAND_ACCESS_LISTS, [])),
                ','.join(command_settings.get(COMMAND_SCOPE, [])),
            ])
        await update.effective_message.reply_html(
            text=f'<pre>{table.get_string()}</pre>')

    @BasePlugin.call_command
    async def do_command_admin_set_commands(
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
                      f'/{command.trigger} enable <command> [access] [scope]\n'
                      f'/{command.trigger} disable <command>'
                      ))
        else:
            action = args[0]
            value = args[1]
            if action == 'enable':
                access_lists = None if len(args) < 3 else args[2].split(',')
                scope = None if len(args) < 4 else args[3].split(',')
                self.bot.settings.set_command_status(trigger=value,
                                                     status=True,
                                                     access_lists=access_lists,
                                                     scope=scope)
                await update.effective_message.reply_text(
                    text=f'Command {value} has been enabled')
            elif action == 'disable':
                self.bot.settings.set_command_status(trigger=value,
                                                     status=False)
                await update.effective_message.reply_text(
                    text=f'Command {value} has been disabled')
            else:
                await update.effective_message.reply_text(
                    text='Invalid action')
