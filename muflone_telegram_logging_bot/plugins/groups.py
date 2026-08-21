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

import logging
import sqlite3
from typing import TYPE_CHECKING

import telegram

from .base import BasePlugin
from .. import extras
from ..database import Database
from ..command import Command

if TYPE_CHECKING:
    from typing import Optional

    import telegram.ext

    from ..bot import Bot


class PluginGroups(BasePlugin):
    def __init__(self,
                 bot: Bot):
        super().__init__(bot=bot)
        self._users: dict[int, dict[int, dict[str, Optional[str]]]] = {}

    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='groups',
                             description='List the managed groups',
                             callback=self.do_command,
                             parameters=None,
                             include_in_list=False,
                             sequence=300),
        )

    @BasePlugin.call_command
    async def do_command(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         command: Command,
                         ) -> None:
        result = []
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            result.append(db_path.parent.name)
        await update.effective_message.reply_text(
            text=f'List of groups managed: {result}')

    def setup(self,
              app: telegram.ext.Application) -> None:
        """
        Setup plugin logic
        """
        super().setup(app=app)
        self.load_users_cache()
        logging.info(f'Setup message handler for {self.__class__.__name__}')
        app.add_handler(
            handler=telegram.ext.MessageHandler(
                filters=telegram.ext.filters.ALL,
                callback=self.log_message),
            group=self.bot.next_handler_group)
        logging.info(f'Setup member handler for {self.__class__.__name__}')
        app.add_handler(
            handler=telegram.ext.ChatMemberHandler(
                self.log_membership,
                telegram.ext.ChatMemberHandler.ANY_CHAT_MEMBER),
            group=self.bot.next_handler_group)
        self.bot.next_handler_group += 1

    async def log_message(self,
                          update: telegram.Update,
                          context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                          ) -> None:
        logging.info(f'{self.__class__.__name__}.log_message')
        message = update.effective_message
        if message:
            chat = update.effective_chat
            user = update.effective_user
            actor = message.from_user
            logging.info({
                'chat_id': chat.id if chat else None,
                'chat_title': chat.title if chat else None,
                'user_id': user.id if user else None,
                'username': user.username if user else None,
                'text': message.text,
                'date': message.date.isoformat() if message.date else None,
            })
            # Save the results
            if chat and user:
                database = self.bot.databases.get_database(
                    directory_name=str(chat.id))
                with database.open() as connection:
                    self.update_database_schema(connection=connection)
                    self.save_chat(connection=connection,
                                   chat=chat)
                    self.save_user(connection=connection,
                                   user=user,
                                   chat=chat)
                    self.save_message(connection=connection,
                                      chat=chat,
                                      message=message,
                                      user=user)
                    if message.new_chat_members:
                        for member in message.new_chat_members:
                            self.save_event(connection=connection,
                                            source='log_message',
                                            event_type='join'
                                            if actor is not None and
                                            actor.id == member.id
                                            else 'added',
                                            user=member,
                                            actor_user=actor,
                                            message=message)
                    connection.commit()

    async def log_membership(self,
                             update: telegram.Update,
                             context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                             ) -> None:
        logging.info(f'{self.__class__.__name__}.log_membership')
        chat = update.effective_chat
        # Save the results
        if chat:
            database = self.bot.databases.get_database(
                directory_name=str(chat.id))
            with database.open() as connection:
                self.update_database_schema(connection=connection)
                if update.chat_member:
                    new_member = update.chat_member.new_chat_member
                    old_member = update.chat_member.old_chat_member
                    if user := new_member.user:
                        self.save_user(connection=connection,
                                       user=user,
                                       chat=chat)
                    if actor := update.effective_user:
                        self.save_user(connection=connection,
                                       user=actor,
                                       chat=chat)
                    event_type = self.get_chat_member_change_type(
                            member_update=(update.chat_member or
                                           update.my_chat_member),
                            bot_action=update.chat_member is None)
                    logging.info({
                        'event': 'log_membership',
                        'chat_id': chat.id if chat else None,
                        'chat_title': chat.title if chat else None,
                        'user_id': user.id if user else None,
                        'user_username': user.username if user else None,
                        'type': event_type,
                        'old_status': old_member.status,
                        'new_status': new_member.status,
                    })
                    self.save_event(
                        connection=connection,
                        source='log_membership',
                        event_type=event_type,
                        user=user,
                        actor_user=actor,
                        message=update.effective_message,
                        update_id=update.update_id,
                        old_status=old_member.status,
                        new_status=new_member.status)
                connection.commit()

    def save_chat(self,
                  connection: sqlite3.Connection,
                  chat: telegram.Chat,
                  ) -> None:
        """
        Save the chat information to database

        :param connection: database connection
        :param chat: chat details
        """
        now = extras.utc_now_iso()
        connection.execute(
            '''
            INSERT INTO chat (
                chat_id,
                type,
                title,
                username,
                first_seen_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                type = excluded.type,
                title = excluded.title,
                username = excluded.username,
                last_seen_at = excluded.last_seen_at
            ''',
            (
                chat.id,
                chat.type,
                chat.title,
                chat.username,
                now,
                now,
            )
        )

    def save_user(self,
                  connection: sqlite3.Connection,
                  user: telegram.User,
                  chat: telegram.Chat,
                  ) -> None:
        """
        Save the user information to database

        :param connection: database connection
        :param user: user details
        :param chat: chat details
        """
        now = extras.utc_now_iso()
        connection.execute(
            '''
            INSERT INTO users (
                user_id,
                is_bot,
                username,
                first_name,
                last_name,
                language_code,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                is_bot = excluded.is_bot,
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                language_code = excluded.language_code,
                last_seen_at = excluded.last_seen_at
            ''',
            (
                user.id,
                1 if user.is_bot else 0,
                user.username,
                user.first_name,
                user.last_name,
                user.language_code,
                now,
            ),
        )
        # Save user details to history
        chat_users = self._users.setdefault(chat.id, {})
        existing_user = chat_users.get(user.id, {})
        if not all((user.username == existing_user.get('username'),
                    user.first_name == existing_user.get('first_name'),
                    user.last_name == existing_user.get('last_name'))):
            # Save user details to history
            connection.execute(
                '''
                INSERT INTO users_history (
                    user_id,
                    username,
                    first_name,
                    last_name,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    now,
                ),
            )
            # Keep user details
            chat_users[user.id] = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

    def save_message(self,
                     connection: sqlite3.Connection,
                     chat: telegram.Chat,
                     message: telegram.Message,
                     user: telegram.User,
                     ) -> None:
        """
        Save the current message into database

        :param connection: database connection
        :param chat: chat details
        :param message: message details
        :param user: user details
        """
        reply_to_message_id = (message.reply_to_message.message_id
                               if message.reply_to_message
                               else None)
        edit_date = (message.edit_date.isoformat()
                     if message.edit_date
                     else None)
        if message and chat and user:
            connection.execute(
                '''
                INSERT INTO messages (
                    message_id,
                    user_id,
                    date,
                    message_type,
                    text,
                    caption,
                    reply_to_message_id,
                    edit_date,
                    is_edited
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    date = excluded.date,
                    message_type = excluded.message_type,
                    text = excluded.text,
                    caption = excluded.caption,
                    reply_to_message_id = excluded.reply_to_message_id,
                    edit_date = excluded.edit_date,
                    is_edited = excluded.is_edited
                ''',
                (
                    message.message_id,
                    user.id if user else None,
                    message.date.isoformat(),
                    self.get_message_type(message),
                    message.text,
                    message.caption,
                    reply_to_message_id,
                    edit_date,
                    1 if edit_date else 0,
                )
            )

    def save_event(self,
                   connection: sqlite3.Connection,
                   source: str,
                   event_type: str,
                   user: Optional[telegram.User],
                   actor_user: Optional[telegram.User],
                   message: Optional[telegram.Message],
                   update_id: Optional[int] = None,
                   old_status: Optional[str] = None,
                   new_status: Optional[str] = None,
                   ) -> None:
        """
        Save event

        :param connection: database connection
        :param source: source event
        :param event_type: event type
        :param user: original user details
        :param actor_user: final user details
        :param message: message details
        :param update_id: event to update
        :param old_status: old status
        :param new_status: new status
        """
        connection.execute(
            '''
            INSERT INTO events (
                message_id,
                update_id,
                source,
                event_type,
                user_id,
                actor_user_id,
                old_status,
                new_status,
                date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                message.message_id if message else None,
                update_id,
                source,
                event_type,
                user.id if user else None,
                actor_user.id if actor_user else None,
                old_status,
                new_status,
                message.date.isoformat() if message else extras.utc_now_iso(),
            ),
        )

    def update_database_schema(self,
                               connection: sqlite3.Connection,
                               ) -> None:
        """
        Update database schema

        :param connection: database connection
        """
        connection.executescript(
            '''
            CREATE TABLE IF NOT EXISTS chat (
                chat_id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_bot INTEGER NOT NULL DEFAULT 0,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                last_seen_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TEXT NOT NULL,
                message_type TEXT NOT NULL,
                text TEXT,
                caption TEXT,
                reply_to_message_id INTEGER,
                edit_date TEXT,
                is_edited INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                update_id INTEGER,
                source TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                actor_user_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                date TEXT NOT NULL
            );
            '''
        )

    def get_message_type(self,
                         message: telegram.Message,
                         ) -> str:
        """
        Get the message type by its data

        :param message: message details
        :return: message type
        """
        if message.text is not None:
            result = 'text'
        elif message.photo:
            result = 'photo'
        elif message.document is not None:
            result = 'document'
        elif message.video is not None:
            result = 'video'
        elif message.animation is not None:
            result = 'animation'
        elif message.audio is not None:
            result = 'audio'
        elif message.voice is not None:
            result = 'voice'
        elif message.sticker is not None:
            result = 'sticker'
        elif message.location is not None:
            result = 'location'
        elif message.contact is not None:
            result = 'contact'
        elif message.poll is not None:
            result = 'poll'
        elif message.new_chat_members:
            result = 'new_chat_members'
        elif message.left_chat_member is not None:
            result = 'left_chat_member'
        else:
            result = 'other'
        return result

    def get_chat_member_change_type(self,
                                    member_update: telegram.ChatMemberUpdated,
                                    bot_action: bool,
                                    ) -> str:
        """
        Get the chat member type by its data

        :param member_update: update details
        :param bot_action: the update is for a bo
        :return: member_update type
        """
        old_member = member_update.old_chat_member
        new_member = member_update.new_chat_member
        old_status = member_update.old_chat_member.status
        new_status = member_update.new_chat_member.status
        actor = member_update.from_user
        target = member_update.new_chat_member.user

        entered_statuses = {telegram.constants.ChatMemberStatus.MEMBER,
                            telegram.constants.ChatMemberStatus.ADMINISTRATOR,
                            telegram.constants.ChatMemberStatus.OWNER}
        left_statuses = {telegram.constants.ChatMemberStatus.LEFT,
                         telegram.constants.ChatMemberStatus.BANNED}

        if bot_action:
            if (old_status in left_statuses and
                    new_status in entered_statuses):
                result = 'bot_added'
            elif (old_status in entered_statuses and
                  new_status in left_statuses):
                result = 'bot_removed'
            else:
                result = 'bot_changed'
        elif (old_status in left_statuses and
              new_status in entered_statuses):
            result = ('join'
                      if actor is not None and actor.id == target.id
                      else 'added')
        elif (old_status in entered_statuses and
              new_status == telegram.constants.ChatMemberStatus.LEFT):
            result = ('leave'
                      if actor is not None and actor.id == target.id
                      else 'removed')
        elif new_status == telegram.constants.ChatMemberStatus.BANNED:
            result = 'banned'
        elif (old_status == telegram.constants.ChatMemberStatus.BANNED and
              new_status == telegram.constants.ChatMemberStatus.LEFT):
            result = 'unbanned'
        elif (old_status == telegram.constants.ChatMemberStatus.MEMBER and
              new_status == telegram.constants.ChatMemberStatus.ADMINISTRATOR):
            result = 'promoted'
        elif (old_status == telegram.constants.ChatMemberStatus.ADMINISTRATOR
              and new_status == telegram.constants.ChatMemberStatus.MEMBER):
            result = 'demoted'
        elif new_status == telegram.constants.ChatMemberStatus.RESTRICTED:
            result = 'exception_added'
        elif (old_status == telegram.constants.ChatMemberStatus.RESTRICTED and
              new_status in entered_statuses):
            result = 'exception_removed'
        elif (old_status == telegram.constants.ChatMemberStatus.RESTRICTED and
              new_status == telegram.constants.ChatMemberStatus.LEFT):
            result = 'exception_removed'
        elif (old_status == telegram.constants.ChatMemberStatus.MEMBER and
              new_status == telegram.constants.ChatMemberStatus.MEMBER):
            if (old_member.tag is None and
                    new_member.tag is not None):
                result = 'tag_added'
            elif (old_member.tag is not None and
                  new_member.tag is None):
                result = 'tag_removed'
            elif (old_member.tag is not None and
                  new_member.tag is not None):
                result = 'tag_changed'
            else:
                result = 'permission_change'
        elif (old_status in (telegram.constants.ChatMemberStatus.ADMINISTRATOR,
                             telegram.constants.ChatMemberStatus.OWNER) and
              new_status in (telegram.constants.ChatMemberStatus.ADMINISTRATOR,
                             telegram.constants.ChatMemberStatus.OWNER)):
            if (old_member.custom_title is None and
                    new_member.custom_title is not None):
                result = 'title_added'
            elif (old_member.custom_title is not None and
                    new_member.custom_title is None):
                result = 'title_removed'
            elif (old_member.custom_title is not None and
                    new_member.custom_title is not None):
                result = 'title_changed'
            else:
                result = 'permission_change'
        else:
            result = 'membership_changed'
        return result

    def load_users_cache(self) -> None:
        """
        Load users details from the databases into the memory cache
        """
        self._users.clear()
        loaded_users = 0
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            database = Database(filepath=db_path)
            try:
                with database.open() as connection:
                    self.update_database_schema(connection=connection)
                    chat_users = self._users.setdefault(chat_id, {})
                    for row in connection.execute(
                            '''
                            SELECT
                                user_id,
                                username,
                                first_name,
                                last_name
                            FROM users
                            '''):
                        chat_users[row['user_id']] = {
                            'username': row['username'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                        }
                        loaded_users += 1
            except sqlite3.Error as error:
                logging.error({
                    'name': self.__class__.__name__,
                    'event': 'load_users_cache_error',
                    'chat_id': chat_id,
                    'database': str(db_path),
                    'error': str(error),
                })
        logging.info({
            'name': self.__class__.__name__,
            'event': 'load_users_cache',
            'chats': len(self._users),
            'users': loaded_users,
        })
