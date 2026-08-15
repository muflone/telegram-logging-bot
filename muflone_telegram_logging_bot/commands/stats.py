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

from .base import BaseCommand
from ..image import (get_user_avatar,
                     load_font)
from ..trigger import Trigger

if TYPE_CHECKING:
    import telegram
    import telegram.ext

BACKGROUND = '#23272a'
TITLE_COLOR = '#38d39f'
NAME_COLOR = '#ffffff'
TEXT_COLOR = '#9aa0a6'


class CommandStart(BaseCommand):
    def get_triggers(self) -> tuple[Trigger, ...]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return (
            Trigger(trigger='stats',
                    description=None,
                    callback=self.do_trigger),
        )

    @BaseCommand.call_trigger
    async def do_trigger(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         trigger: Trigger,
                         ) -> None:
        chat = update.effective_chat
        database = self.bot.databases.get_database(
            directory_name=str(chat.id))
        with database.open() as connection:
            self.update_database_schema(connection=connection)
            rows = connection.execute(
                '''
                SELECT
                  date(messages.date) AS date,
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
                GROUP BY date(messages.date), messages.user_id, users.username
                ORDER BY date DESC, messages_count DESC
                LIMIT ?
                ''',
                (datetime.date.today().isoformat(), 20)
            ).fetchall()
        image = await create_top_members_image(bot=context.bot,
                                               rows=rows)
        await update.effective_message.reply_photo(photo=image,
                                                   caption='Top members')


async def create_top_members_image(bot, rows: list[dict]) -> io.BytesIO:
    """
    Create an image with the most active members
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
              text='Top members',
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
        avatar = await get_user_avatar(bot=bot,
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
