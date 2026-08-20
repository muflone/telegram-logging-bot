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

import copy
import json
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pathlib
    from typing import Optional

    import telegram
    import telegram.ext

    from .command import Command

BOT_OWNERS = 'bot_owners'
BOT_ADMINS = 'bot_admins'
CHAT_ADMINS = 'chat_admins'
DENIED_USERS = 'denied_users'
ENABLED_CHATS = 'enabled_chats'
ENABLED_COMMANDS = 'enabled_commands'
EVERYONE = 'everyone'

COMMAND_ACCESS_LISTS = 'access_lists'
COMMAND_SCOPE = 'scope'
COMMAND_STATUS = 'status'

SCOPE_PRIVATE = 'private'
SCOPE_GROUP = 'group'
SCOPE_SUPERGROUP = 'supergroup'


class Settings:
    STANDARD_ACCESS_LISTS = {
        BOT_OWNERS,
        BOT_ADMINS,
        EVERYONE,
    }

    def __init__(self,
                 filepath: pathlib.Path,
                 chats_dir: pathlib.Path):
        self.filepath = filepath
        self.chats_dir = chats_dir
        self.global_data = {}
        self.chats_data = {}
        self.load()

    def load(self) -> None:
        """
        Load settings from file
        """
        if not self.filepath.exists():
            self.global_data = self._get_default_global_data()
            self.save()
        else:
            with self.filepath.open(encoding='utf-8') as handle:
                self.global_data = json.load(handle)
            for key, value in self._get_default_global_data().items():
                self.global_data.setdefault(key, value)
        # Add bot_owner from environment if not present
        if (not self.get_list_from_global_data(list_name=BOT_OWNERS) and
                os.environ.get('BOT_OWNER')):
            self.add_global_user(access_list=BOT_OWNERS,
                                 user_reference=os.environ['BOT_OWNER'])
        # Load every chat settings
        for chat_path in self.chats_dir.glob('*'):
            if chat_path.is_dir():
                self.load_chat(chat_id=chat_path.name)

    def save(self) -> None:
        """
        Save settings to file
        """
        tmp_filepath = self.filepath.with_suffix('.json.tmp')
        with tmp_filepath.open('w', encoding='utf-8') as file:
            json.dump(self.global_data, file, indent=2, ensure_ascii=False)
            file.write('\n')
        tmp_filepath.replace(self.filepath)

    def get_chat_filepath(self,
                          chat_id: str
                          ) -> pathlib.Path:
        """
        Get chat settings filepath

        :param chat_id: chat id as string
        :return: settings filepath
        """
        return self.chats_dir / chat_id / 'settings.json'

    def load_chat(self,
                  chat_id: str
                  ) -> None:
        """
        Load chat settings

        :param chat_id: chat id as string
        """
        filepath = self.get_chat_filepath(chat_id=chat_id)
        if not filepath.exists():
            result = self._get_default_chat_data()
        else:
            with filepath.open(encoding='utf-8') as handle:
                result = json.load(handle)
            result.setdefault(CHAT_ADMINS, [])
            result.setdefault(DENIED_USERS, [])
        self.chats_data[chat_id] = result

    def save_chat(self,
                  chat_id: str,
                  ) -> None:
        """
        Load chat settings

        :param chat_id: chat id as string
        :param data: chat settings
        """
        filepath = self.get_chat_filepath(chat_id=chat_id)
        tmp_filepath = filepath.with_suffix('.json.tmp')
        with tmp_filepath.open('w', encoding='utf-8') as handle:
            json.dump(self.chats_data[chat_id],
                      handle,
                      indent=2,
                      ensure_ascii=False)
            handle.write('\n')
        tmp_filepath.replace(filepath)

    def get_list_from_chat_data(self,
                                chat_id: str,
                                list_name: str
                                ) -> list[str]:
        """
        Return a list from chat data

        :param chat_id: chat id as string
        :param list_name: list name to get
        :return: list of members
        """
        return copy.copy(self.chats_data.get(chat_id, {}).get(list_name, []))

    def get_list_from_global_data(self,
                                  list_name: str
                                  ) -> list[str]:
        """
        Return a list from global data

        :param list_name: list name to get
        :return: list of members
        """
        return copy.copy(self.global_data.get(list_name, []))

    def get_enabled_commands(self) -> dict[str, Any]:
        """
        Return the enabled commands data

        :return: dictionary with commands details
        """
        return self.global_data.get(ENABLED_COMMANDS, {})

    def user_in_list(self,
                     user: Optional[telegram.User],
                     users_list: list[str]
                     ) -> bool:
        """
        Check if the user is in the users list

        :param user: user details
        :param users_list: users list
        :return: True if the user is included in the users list
        """
        # Check user id and username if available
        if not user:
            result = False
        else:
            user_refs = {str(user.id)}
            if user.username:
                user_refs.add(self._normalize_user_ref(f'@{user.username}'))
            normalized_values = {
                self._normalize_user_ref(value)
                for value in users_list
            }
            # Find matching users
            result = bool(user_refs & normalized_values)
        return result

    def is_in_chat_list(self,
                        chat_id: str,
                        user: Optional[telegram.User],
                        access_list: str
                        ) -> bool:
        """
        Check if the user is in the specified chat list

        :param chat_id: chat id as string
        :param user: user details
        :param access_list: list to check
        :return: True if the user is in the access list
        """
        if not chat_id:
            result = False
        else:
            result = self.user_in_list(
                user=user,
                users_list=self.get_list_from_chat_data(chat_id=chat_id,
                                                        list_name=access_list))
        return result

    def is_in_global_list(self,
                          user: Optional[telegram.User],
                          access_list: str
                          ) -> bool:
        """
        Check if the user is in the specified global list

        :param user: user details
        :param access_list: list to check
        :return: True if the user is in the access list
        """
        result = self.user_in_list(
            user=user,
            users_list=self.get_list_from_global_data(list_name=access_list))
        return result

    def is_bot_owner(self,
                     user: Optional[telegram.User]
                     ) -> bool:
        """
        Check if the user is in the bot_owners list

        :param user: user details
        :return: True if the user is in the bot_owners list
        """
        return self.is_in_global_list(user=user,
                                      access_list=BOT_OWNERS)

    def is_bot_admin(self,
                     user: Optional[telegram.User]
                     ) -> bool:
        """
        Check if the user is in the bot_owners or bot_admins lists

        :param user: user details
        :return: True if the user is in the bot_owners or bot_admins list
        """
        return (self.is_bot_owner(user=user) or
                self.is_in_global_list(user=user,
                                       access_list=BOT_ADMINS))

    def is_chat_enabled(self,
                        chat: Optional[telegram.Chat]
                        ) -> bool:
        """
        Check if the chat is in the enabled_chats group

        :param chat: chat details
        :return: True if the chat is included in the enabled_chats group
        """
        if not chat:
            result = False
        else:
            result = str(chat.id) in {
                chat_id
                for chat_id in self.get_list_from_global_data(
                    list_name=ENABLED_CHATS)
            }
        return result

    def is_global_denied_users(self,
                               user: Optional[telegram.User]
                               ) -> bool:
        """
        Check if the user is in the global denied_users lists

        :param user: user details
        :return: True if the user is in the denied_users list
        """
        return self.is_in_global_list(user=user,
                                      access_list=DENIED_USERS)

    def is_chat_admin(self,
                      chat_id: str,
                      user: Optional[telegram.User]
                      ) -> bool:
        """
        Check if the user is in the bot_admin or in the chat_admins chat group

        :param chat_id: chat id as string
        :param user: user details
        :return: True if the user is in the chat groups
        """
        return (self.is_bot_admin(user=user) or
                self.is_in_chat_list(chat_id=chat_id,
                                     user=user,
                                     access_list=CHAT_ADMINS))

    def is_chat_denied_users(self,
                             chat_id: str,
                             user: Optional[telegram.User]
                             ) -> bool:
        """
        Check if the user is in the denied_users chat group

        :param chat_id: chat id as string
        :param user: user details
        :return: True if the user is in the denied_users chat group
        """
        return self.is_in_chat_list(chat_id=chat_id,
                                    user=user,
                                    access_list=DENIED_USERS)

    def get_command_settings(self,
                             trigger: str
                             ) -> dict[str, Any]:
        """
        Get commands settings, with default settings if missing

        :param trigger: command trigger
        :return: command details
        """
        commands_settings = self.get_enabled_commands()
        command_settings = commands_settings.get(trigger, {})
        return {
            COMMAND_STATUS: command_settings.get(COMMAND_STATUS, True),
            COMMAND_ACCESS_LISTS: command_settings.get(COMMAND_ACCESS_LISTS,
                                                       []),
            COMMAND_SCOPE: command_settings.get(COMMAND_SCOPE,
                                                [SCOPE_PRIVATE,
                                                 SCOPE_GROUP,
                                                 SCOPE_SUPERGROUP]),
        }

    def can_run_command(self,
                        update: telegram.Update,
                        command: Command
                        ) -> bool:
        """
        Check if the user can execute the command

        :param update: update details
        :param command: command details
        :return: True if the command is valid for the user
        """
        user = update.effective_user
        chat = update.effective_chat
        command_settings = self.get_command_settings(
            trigger=command.trigger)

        if self.is_bot_owner(user=user):
            # Bot owner users can do anything
            result = True
        elif self.is_global_denied_users(user=user):
            # Globally excluded users cannot do anything
            result = False
        elif not chat:
            # Messages without chat are denied
            result = False
        elif self.is_chat_denied_users(chat_id=str(chat.id),
                                       user=user):
            # Users excluded for single chat cannot do anything
            result = False
        elif not self.is_chat_enabled(chat=chat):
            # Chats not enabled are always denied
            result = False
        elif not command_settings[COMMAND_STATUS]:
            # Commands disabled are always denied
            result = False
        elif chat.type not in command_settings[COMMAND_SCOPE]:
            # Commands for a different chat type are always denied
            result = False
        else:
            # Check command access lists
            for access in command_settings[COMMAND_ACCESS_LISTS]:
                if access == EVERYONE:
                    # Access level everyone is always allowed
                    result = True
                    break
                elif access == BOT_OWNERS:
                    # Commands requiring bot_owner access are unchecked
                    # as is_bot_owner was previously checked
                    pass
                elif (access == BOT_ADMINS and
                      self.is_bot_admin(user=user)):
                    # Commands requiring bot_admin access are allowed
                    # only if the user is in the list
                    result = True
                    break
                elif access not in self.STANDARD_ACCESS_LISTS:
                    # Check custom access lists
                    if self.is_bot_admin(user=user):
                        # Bot admins are allowed to execute the command
                        result = True
                        break
                    elif self.is_in_chat_list(chat_id=str(chat.id),
                                              user=user,
                                              access_list=access):
                        # Only users in the specified access group are
                        # allowed to execute the command
                        result = True
                        break
            else:
                # Command denied
                result = False
        return result

    async def run_command(self,
                          update: telegram.Update,
                          context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                          command: Command
                          ) -> None:
        """
        Check if the user can execute the command and process it

        :param update: update details
        :param context: context details
        :param command: command details
        """
        if not self.can_run_command(update=update,
                                    command=command):
            await update.effective_message.reply_text(
                text='Command not available or pemission denied.')
        else:
            await command.callback(update=update,
                                   context=context,
                                   command=command)

    def add_global_user(self,
                        access_list: str,
                        user_reference: str
                        ) -> None:
        """
        Add the specified user_reference to the global access_list

        :param access_list: name of the group to add the user
        :param user_reference: user id or username to add
        """
        users = self.global_data.setdefault(access_list, [])
        user_reference = self._normalize_user_ref(value=user_reference)
        if user_reference not in users:
            users.append(user_reference)
            self.save()

    def remove_global_user(self,
                           access_list: str,
                           user_reference: str
                           ) -> None:
        """
        Remove the specified user_reference from the global access_list

        :param access_list: name of the group to remove the user
        :param user_reference: user id or username to remove
        """
        users = self.global_data.setdefault(access_list, [])
        user_reference = self._normalize_user_ref(value=user_reference)
        if user_reference in users:
            users.remove(user_reference)
            self.save()

    def add_chat_user(self,
                      chat_id: str,
                      access_list: str,
                      user_reference: str
                      ) -> None:
        """
        Add the specified user_reference to the chat access_list

        :param chat_id: chat id as string
        :param access_list: name of the group to add the user
        :param user_reference: user id or username to add
        """
        users = self.chats_data.get(chat_id, {}).setdefault(access_list, [])
        user_reference = self._normalize_user_ref(value=user_reference)
        if user_reference not in users:
            users.append(user_reference)
            self.save_chat(chat_id=chat_id)

    def set_chat_enabled(self,
                         chat_id: str,
                         status: bool
                         ) -> None:
        """
        Add or remove the specified chat from the global chats list

        :param chat_id: chat id as string
        :param status: True to add, False to remove
        """
        chats = self.global_data.setdefault(ENABLED_CHATS, [])
        if status and chat_id not in chats:
            # Add chat
            chats.append(chat_id)
        elif not status and chat_id in chats:
            # Remove chat
            chats.remove(chat_id)
        self.save()

    def set_command_status(self,
                           trigger: str,
                           status: bool,
                           access_lists: list[str] = None,
                           scope: list[str] = None,
                           ) -> None:
        """
        Enable or disable the specified trigger from the global commands list

        :param trigger: command name
        :param status: True to enable, False to disable
        :param access_lists: access list
        :param scope: scope of enabled chats
        :return:
        """
        commands_settings = self.get_enabled_commands()
        command = commands_settings.setdefault(trigger, {})
        command[COMMAND_STATUS] = status
        command.setdefault(COMMAND_ACCESS_LISTS, [])
        if access_lists is not None:
            command[COMMAND_ACCESS_LISTS] = access_lists
        command.setdefault(COMMAND_SCOPE, [SCOPE_PRIVATE,
                                           SCOPE_GROUP,
                                           SCOPE_SUPERGROUP])
        if scope is not None:
            command[COMMAND_SCOPE] = scope
        self.save()

    def _get_default_global_data(self) -> dict[str, Any]:
        """
        Standard empty default global settings
        """
        return {
            BOT_OWNERS: [],
            BOT_ADMINS: [],
            DENIED_USERS: [],
            ENABLED_CHATS: [],
            ENABLED_COMMANDS: {},
        }

    def _get_default_chat_data(self) -> dict[str, Any]:
        """
        Standard empty default chat settings
        """
        return {
            CHAT_ADMINS: [],
            DENIED_USERS: [],
        }

    def _normalize_user_ref(self, value: str | int) -> str:
        """
        Clear user name or id

        :param value: user name or id
        :return: lowercase user name or id as string
        """
        value = str(value).strip()
        if value.startswith('@'):
            return f'@{value[1:].lower()}'
        return value
