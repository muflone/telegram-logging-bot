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

import datetime
import io
from typing import TYPE_CHECKING

import PIL.Image
import PIL.ImageDraw

from .base import BasePlugin
from ..image import (get_user_avatar,
                     load_font)
from ..command import Command

if TYPE_CHECKING:
    from typing import Optional
    import sqlite3

    import telegram
    import telegram.ext

BACKGROUND = '#23272a'
TITLE_COLOR = '#38d39f'
NAME_COLOR = '#ffffff'
TEXT_COLOR = '#9aa0a6'


class PluginStatsActiveUsers(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            Command(trigger='stats_active_users',
                    description='Show most active users by message numbers',
                    callback=self.do_command,
                    status=True),
        )

    @BasePlugin.call_command
    async def do_command(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         command: Command,
                         ) -> None:
        chat = update.effective_chat
        if context.args:
            # Use parsed date if specified
            if selected_date := self.parse_date(context=context):
                rows = self.get_top_members(chat=chat,
                                            date=selected_date,
                                            limit=15)
                date_title = f'{selected_date.isoformat()} (UTC)'
            valid_date = selected_date is not None
        else:
            # Use the latest 24 hours if no date was specified
            rows = self.get_top_members_24_hours(chat=chat,
                                                 limit=15)
            date_title = 'the latest 24 hours'
            valid_date = True
        if valid_date:
            graph_title = f'Most active members for {date_title}'
            if rows:
                # Results found
                image = await self.create_graph_image(
                    rows=rows,
                    title=graph_title)
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=graph_title)
            else:
                # No results
                await update.effective_message.reply_text(
                    text=f'No results for {selected_date.isoformat()}')
        else:
            await update.effective_message.reply_text(
                text=f'Usage: /{command.trigger} [YYYY-MM-DD]')

    def parse_date(self,
                   context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                   ) -> Optional[datetime.date]:
        """
        Parse date from command arguments

        :param context: telegram Context object
        :return: selected date or None
        """
        if context.args:
            try:
                # Try to parse the specified date
                result = datetime.date.strptime(context.args[0],
                                                '%Y-%m-%d')
            except ValueError:
                result = None
        else:
            # Use today if date is not specified
            result = datetime.date.today()
        return result

    def get_top_members(self,
                        chat: telegram.Chat,
                        date: datetime.date,
                        limit: int,
                        ) -> list[sqlite3.Row]:
        """
        Get the most active members by messages count

        :param chat: chat details
        :param date: selected date
        :param limit: number of results
        :return: list of Rows with data
        """
        database = self.bot.databases.get_database(
            directory_name=str(chat.id))
        with database.open() as connection:
            self.update_database_schema(connection=connection)
            result = connection.execute(
                '''
                SELECT
                  messages.user_id AS user_id,
                  users.username AS username,
                  COALESCE(users.first_name, '') AS first_name,
                  COALESCE(users.last_name, '') AS last_name,
                  COUNT(*) AS messages_count,
                  ROUND(AVG(LENGTH(messages.text)), 0) AS average_length
                FROM messages
                LEFT JOIN users
                   ON users.user_id = messages.user_id
                WHERE date(messages.date) = ?
                GROUP BY messages.user_id, users.username
                ORDER BY messages_count DESC
                LIMIT ?
                ''',
                (
                    date.isoformat(),
                    limit
                )
            ).fetchall()
        return result

    def get_top_members_24_hours(self,
                                 chat: telegram.Chat,
                                 limit: int,
                                 ) -> list[sqlite3.Row]:
        """
        Get the most active members by messages count in the latest 24 hours

        :param chat: chat details
        :param limit: number of results
        :return: list of Rows with data
        """
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(hours=24)
        database = self.bot.databases.get_database(
            directory_name=str(chat.id))
        with database.open() as connection:
            self.update_database_schema(connection=connection)
            result = connection.execute(
                '''
                SELECT
                  messages.user_id AS user_id,
                  users.username AS username,
                  COALESCE(users.first_name, '') AS first_name,
                  COALESCE(users.last_name, '') AS last_name,
                  COUNT(*) AS messages_count,
                  ROUND(AVG(LENGTH(messages.text)), 0) AS average_length
                FROM messages
                LEFT JOIN users
                   ON users.user_id = messages.user_id
                WHERE messages.date BETWEEN ? AND ?
                GROUP BY messages.user_id, users.username
                ORDER BY messages_count DESC
                LIMIT ?
                ''',
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                    limit
                )
            ).fetchall()
        return result

    async def create_graph_image(self,
                                 rows: list[sqlite3.Row],
                                 title: str,
                                 ) -> io.BytesIO:
        """
        Create an image with the most active members

        :param rows: list of Rows with data
        :param title: graph title
        :return: binary data with the graph image
        """
        width = 450
        padding_x = 18
        padding_top = 14
        title_height = 28
        row_height = 66
        avatar_size = 48

        height = padding_top + title_height + len(rows) * row_height + 12
        image = PIL.Image.new(mode='RGB',
                              size=(width, height),
                              color=BACKGROUND)
        draw = PIL.ImageDraw.Draw(im=image)
        title_font = load_font(size=18, bold=True)
        name_font = load_font(size=13, bold=True)
        stats_font = load_font(size=12)
        draw.text(xy=(padding_x, padding_top),
                  text=title,
                  fill=TITLE_COLOR,
                  font=title_font)
        y = padding_top + title_height + 6
        for row in rows:
            user_id = int(row['user_id'])
            user_name = f'{row["first_name"]} {row["last_name"]} '
            if not user_name.strip():
                user_name = '@{row["username"]}'
            messages_count = int(row['messages_count'])
            avg_length = int(row['average_length'] or 0)
            # Get user avatar image or fallback
            avatar = await get_user_avatar(bot=self.bot.bot,
                                           user_id=user_id,
                                           name=user_name,
                                           size=avatar_size)
            avatar_x = padding_x
            image.paste(im=avatar,
                        box=(avatar_x, y + 4),
                        mask=avatar)
            text_x = avatar_x + avatar_size + 12
            draw.text(xy=(text_x, y + 8),
                      text=user_name,
                      fill=NAME_COLOR,
                      font=name_font)
            draw.text(xy=(text_x, y + 30),
                      text=(f'{messages_count} messages, '
                            f'{avg_length} characters average'),
                      fill=TEXT_COLOR,
                      font=stats_font)
            y += row_height
        # Return image
        output = io.BytesIO()
        image.save(fp=output,
                   format='PNG')
        output.seek(0)
        return output
