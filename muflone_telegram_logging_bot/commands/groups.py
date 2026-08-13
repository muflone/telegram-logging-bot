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

from .base import BaseCommand
from .. import extras
from ..trigger import Trigger

if TYPE_CHECKING:
    import telegram.ext


class CommandGroups(BaseCommand):
    def get_triggers(self) -> tuple[Trigger]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return (
            Trigger(trigger='groups',
                    description='List the managed groups',
                    callback=self.do_trigger),
        )

    @BaseCommand.call_trigger
    async def do_trigger(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         trigger: Trigger,
                         ) -> None:
        result = []
        for chat_id, db_path in self.bot.databases.get_known_groups().items():
            result.append(db_path)
        await update.message.reply_text(f'List of groups managed: {result}')

    def setup(self,
              app: telegram.ext.Application) -> None:
        """
        Setup command logic
        """
        super().setup(app=app)
        logging.info(f'Setup message handler for {self.__class__.__name__}')
        app.add_handler(
            handler=telegram.ext.MessageHandler(
                filters=telegram.ext.filters.ALL,
                callback=self.log_message),
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
            logging.info({
                "chat_id": chat.id if chat else None,
                "chat_title": chat.title if chat else None,
                "user_id": user.id if user else None,
                "username": user.username if user else None,
                "text": message.text,
                "date": message.date.isoformat() if message.date else None,
            })
            # Save the results
            if chat := update.effective_chat:
                message = update.effective_message
                user = update.effective_user
                database = self.bot.databases.get_database(
                    filename=str(chat.id))
                with database.open() as connection:
                    self.update_database_schema(connection=connection)
                    self.save_chat(connection=connection,
                                   chat=chat)
                    self.save_message(connection=connection,
                                      chat=chat,
                                      message=message,
                                      user=user)
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
                    chat_id,
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, message_id) DO UPDATE SET
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
                    chat.id,
                    message.message_id,
                    user.id if user else None,
                    message.date.isoformat(),
                    self._classify_message_type(message),
                    message.text,
                    message.caption,
                    reply_to_message_id,
                    edit_date,
                    1 if edit_date else 0,
                )
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

            CREATE TABLE IF NOT EXISTS messages (
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER,
                date TEXT NOT NULL,
                message_type TEXT NOT NULL,
                text TEXT,
                caption TEXT,
                reply_to_message_id INTEGER,
                edit_date TEXT,
                is_edited INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, message_id)
            );
            '''
        )

    def _classify_message_type(self,
                               message: telegram.Message,
                               ) -> str:
        """
        Classify the message type by its data

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
