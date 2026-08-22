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
import math
from typing import TYPE_CHECKING

import PIL.Image
import PIL.ImageDraw

from .base import BasePlugin
from ..image import load_font
from ..command import Command
from ..extras import timezone_offset
from ..parameter import Parameter, ParameterType

if TYPE_CHECKING:
    from typing import Optional
    import sqlite3

    import telegram
    import telegram.ext

BACKGROUND = '#23272a'
TITLE_COLOR = '#38d39f'
TEXT_COLOR = '#9aa0a6'
GRID_COLOR = '#343a40'
LINE_COLOR = '#58a6dc'


class PluginStatsHourly(BasePlugin):
    def get_commands(self) -> tuple[Command, ...]:
        """
        Get commands and callbacks

        :return: tuple of Command
        """
        return (
            self.new_command(trigger='stats_hourly',
                             description='Show messages count chart by hour',
                             callback=self.do_command,
                             parameters=(
                                 Parameter(name='timezone',
                                           description='Timezone',
                                           type=ParameterType.STRING,
                                           null=False,
                                           default='UTC'),
                             ),
                             include_in_list=True,
                             sequence=603),
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
            selected_date1, selected_date2 = self.parse_dates(context=context)
            date_start = datetime.datetime.fromordinal(
                selected_date1.toordinal())
            date_end = datetime.datetime.fromordinal(
                (selected_date2 + datetime.timedelta(days=1)).toordinal())
            if date_start and date_end:
                date_title = (f'{selected_date1.isoformat()} '
                              f'to {selected_date2.isoformat()}')
            valid_date = date_start and date_end
        else:
            # Use the latest 24 hours if no date was specified
            date_end = datetime.datetime.now()
            date_start = date_end - datetime.timedelta(hours=24)
            date_title = 'the latest 24 hours'
            valid_date = True
        if valid_date:
            timezone = self.bot.settings.get_command_parameter_value(
                chat_id=str(chat.id),
                command=command,
                parameter='timezone')
            graph_title = f'Hourly messages count for {date_title}'
            if rows := self.get_graph_data(chat=chat,
                                           date_start=date_start,
                                           date_end=date_end,
                                           tz_name=timezone):
                # Set 0 for the missing data
                hourly_values = {
                    hour: 0
                    for hour in range(0, 24)
                }
                for row in rows:
                    hourly_values[int(row['hour'])] = row['messages_count']
                # Results found
                image = await self.create_graph_image(values=hourly_values,
                                                      title=graph_title)
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=f'{graph_title} ({timezone})')
            else:
                # No results
                await update.effective_message.reply_text(
                    text=f'No results from {selected_date1.isoformat()} '
                         f'to {selected_date2.isoformat()}')
        else:
            await update.effective_message.reply_text(
                text=f'Usage: /{command.trigger} [YYYY-MM-DD] [YYYY-MM-DD]')

    def parse_dates(self,
                    context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                    ) -> tuple[Optional[datetime.date], ...]:
        """
        Parse dates from command arguments

        :param context: telegram Context object
        :return: tuple with two date or None
        """
        if context.args:
            # Get first argument
            try:
                # Try to parse the specified date
                date_1 = datetime.date.fromordinal(
                    datetime.date.strptime(context.args[0],
                                           '%Y-%m-%d').toordinal())
                try:
                    date_2 = datetime.date.fromordinal(
                        datetime.date.strptime(context.args[1],
                                               '%Y-%m-%d').toordinal())
                except IndexError:
                    date_2 = date_1
            except ValueError:
                date_1 = None
                date_2 = None
        else:
            # Use today if date is not specified
            date_1 = datetime.date.fromordinal(
                datetime.date.today().toordinal())
            date_2 = date_1
        return (date_1, date_2)

    def get_graph_data(self,
                       chat: telegram.Chat,
                       date_start: datetime.date,
                       date_end: datetime.date,
                       tz_name: str,
                       ) -> list[sqlite3.Row]:
        """
        Get messages count grouped by hour

        :param chat: chat details
        :param date_start: initial date
        :param date_end: final date
        :param tz_name: timezone name
        :return: list of Rows with data
        """
        zone_offset = timezone_offset(tz_name=tz_name,
                                      when=date_start)
        database = self.bot.databases.get_database(
            directory_name=str(chat.id))
        with database.open() as connection:
            self.update_database_schema(connection=connection)
            result = connection.execute(
                '''
                SELECT
                  STRFTIME('%H', DATETIME(messages.date, ?)) AS hour,
                  COUNT(*) AS messages_count
                FROM messages
                WHERE DATETIME(messages.date, ?) >= ?
                  AND DATETIME(messages.date, ?) < ?
                GROUP BY hour
                ORDER BY hour ASC
                ''',
                (
                    zone_offset,
                    zone_offset,
                    date_start,
                    zone_offset,
                    date_end,
                )
            ).fetchall()
        return result

    async def create_graph_image(self,
                                 values: dict[int, int],
                                 title: str,
                                 ) -> io.BytesIO:
        """
        Create an image with the most active members

        :param values: dict object with hour and count
        :param title: graph title
        :return: binary data with the graph image
        """
        width = 600
        height = 400
        padding_left = 42
        padding_right = 22
        padding_top = 50
        padding_bottom = 34
        chart_left = padding_left
        chart_top = padding_top
        chart_right = width - padding_right
        chart_bottom = height - padding_bottom
        chart_width = chart_right - chart_left

        image = PIL.Image.new(mode='RGB',
                              size=(width, height),
                              color=BACKGROUND)
        draw = PIL.ImageDraw.Draw(im=image)
        title_font = load_font(size=18, bold=True)
        label_font = load_font(size=9)
        # Draw title
        draw.text(xy=(16, 9),
                  text=title,
                  fill=TITLE_COLOR,
                  font=title_font)
        # Draw the Y axis legend
        raw_max_value = max(values.values())
        max_value = self.round_axis_max(value=raw_max_value)
        tick_step = self.get_tick_step(max_value=max_value)
        for value in range(0, max_value + 1, tick_step):
            y = self.value_to_y(value=value,
                                min_value=0,
                                max_value=max_value,
                                chart_top=chart_top,
                                chart_bottom=chart_bottom)
            draw.line(xy=(chart_left, y, chart_right, y),
                      fill=GRID_COLOR,
                      width=1)
            draw.text(xy=(12, y - 7),
                      text=str(value),
                      fill=TEXT_COLOR,
                      font=label_font)
        # Draw the points
        points = []
        for hour, value in values.items():
            x = chart_left + round(chart_width * hour / (len(values) - 1))
            y = self.value_to_y(value=value,
                                min_value=0,
                                max_value=max_value,
                                chart_top=chart_top,
                                chart_bottom=chart_bottom)
            points.append((x, y))
        draw.line(xy=points,
                  fill=LINE_COLOR,
                  width=2)
        # Draw the X axis legend
        self.draw_x_labels(draw=draw,
                           values=values,
                           chart_left=chart_left,
                           chart_right=chart_right,
                           chart_bottom=chart_bottom,
                           font=label_font)

        # Return image
        output = io.BytesIO()
        image.save(fp=output,
                   format='PNG')
        output.seek(0)
        return output

    def round_axis_max(self,
                       value: int,
                       ) -> int:
        """
        Round the maximum Y axis value to a readable number.
        """
        if value <= 0:
            return 10

        if value <= 10:
            step = 1
        elif value <= 50:
            step = 5
        elif value <= 100:
            step = 10
        elif value <= 500:
            step = 50
        elif value <= 1000:
            step = 100
        else:
            step = 200

        return math.ceil(value / step) * step

    def get_tick_step(self,
                      max_value: int,
                      ) -> int:
        """
        Get a readable grid step for the Y axis.
        """
        if max_value <= 10:
            result = 1
        elif max_value <= 50:
            result = 5
        elif max_value <= 100:
            result = 10
        elif max_value <= 500:
            result = 50
        elif max_value <= 1000:
            result = 100
        else:
            result = 200
        return result

    def value_to_y(self,
                   value: float,
                   min_value: float,
                   max_value: float,
                   chart_top: int,
                   chart_bottom: int,
                   ) -> int:
        """
        Convert a numeric value to a chart Y coordinate.
        """
        if min_value == max_value:
            result = (chart_top + chart_bottom) // 2
        else:
            ratio = (value - min_value) / (max_value - min_value)
            result = chart_bottom - round(
                (chart_bottom - chart_top) * ratio)
        return result

    def draw_x_labels(self,
                      draw: PIL.ImageDraw.ImageDraw,
                      values: dict[int, int],
                      chart_left: int,
                      chart_right: int,
                      chart_bottom: int,
                      font: PIL.ImageFont.FreeTypeFont,
                      ) -> None:
        """
        Draw hour labels on X axis.
        """
        for hour in values.keys():
            text = f'{hour:02d}'
            text_bbox = draw.textbbox(xy=(0, 0),
                                      text=text,
                                      font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x = chart_left + round((chart_right - chart_left) * hour / 23)
            draw.text(xy=(x - text_width / 2, chart_bottom + 8),
                      text=text,
                      fill=TEXT_COLOR,
                      font=font)
