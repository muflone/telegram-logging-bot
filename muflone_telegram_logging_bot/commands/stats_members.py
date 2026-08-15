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

import dateutil

import PIL.Image
import PIL.ImageDraw

from .base import BaseCommand
from ..image import load_font
from ..trigger import Trigger

if TYPE_CHECKING:
    import sqlite3
    from typing import Optional

    import telegram
    import telegram.ext


BACKGROUND = '#23272a'
TITLE_COLOR = '#38d39f'
SUBTITLE_COLOR = '#9aa0a6'
GRID_COLOR = '#343a40'
LINE_COLOR = '#2877d5'
TEXT_COLOR = '#9aa0a6'


class CommandGrowth(BaseCommand):
    def get_triggers(self) -> tuple[Trigger, ...]:
        """
        Get triggers and callbacks
        """
        return (
            Trigger(trigger='stats_members',
                    description='Show members growth chart',
                    callback=self.do_trigger),
        )

    @BaseCommand.call_trigger
    async def do_trigger(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         trigger: Trigger,
                         ) -> None:
        chat = update.effective_chat
        if dates := self.parse_dates(context=context):
            start_date, end_date = dates
            if rows := self.get_members_growth(chat=chat,
                                               start_date=start_date,
                                               end_date=end_date):
                # Results found
                values = self.interpolate_daily_values(rows=rows,
                                                       start_date=start_date,
                                                       end_date=end_date)

                image = self.create_graph_image(values=values,
                                                start_date=start_date,
                                                end_date=end_date)
                await update.effective_message.reply_photo(
                    photo=image,
                    caption='Members growth')
            else:
                # No results
                await update.effective_message.reply_text(
                    text=(f'No members count data between '
                          f'{start_date.isoformat()} and '
                          f'{end_date.isoformat()}'))
        else:
            await update.effective_message.reply_text(
                text=f'Usage: /{trigger.trigger} [YYYY-MM-DD] [YYYY-MM-DD]')

    def parse_dates(self,
                    context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                    ) -> Optional[tuple[datetime.date, datetime.date]]:
        """
        Parse dates from command arguments

        :param context: telegram Context object
        :return: tuple with start date and end date or None
        """
        try:
            if len(context.args) == 0:
                # Get the range from 1 month ago and today
                end_date = datetime.date.today()
                start_date = (end_date -
                              dateutil.relativedelta.relativedelta(months=1))
            elif len(context.args) == 1:
                # Get the range from date to today
                end_date = datetime.date.today()
                start_date = datetime.date.fromisoformat(context.args[0])
            elif len(context.args) >= 2:
                # Get the range from date to date
                start_date = datetime.date.fromisoformat(context.args[0])
                end_date = datetime.date.fromisoformat(context.args[1])
            # Make sure the start date if not higher than end date
            if start_date > end_date:
                result = None
            else:
                result = start_date, end_date
        except ValueError:
            result = None
        return result

    def get_members_growth(self,
                           chat: telegram.Chat,
                           start_date: datetime.date,
                           end_date: datetime.date,
                           ) -> list[sqlite3.Row]:
        """
        Get members count grouped by day

        :param chat: chat details
        :param start_date: starting date
        :param end_date: ending date
        :return: list of Rows with data
        """
        database = self.bot.databases.get_database(
            directory_name=str(chat.id))
        with database.open() as connection:
            self.update_database_schema(connection=connection)
            result = connection.execute(
                '''
                WITH last_dates AS (
                  SELECT
                    members_count.id,
                    MAX(members_count.taken_at)
                  FROM members_count
                  GROUP BY date(members_count.taken_at)
                )
                SELECT
                  members_count.id,
                  date(members_count.taken_at) AS date,
                  members_count.total AS users_count
                FROM members_count
                INNER JOIN last_dates
                   ON last_dates.id = members_count.id
                WHERE TRUE
                  AND date(members_count.taken_at) BETWEEN ? AND ?
                ORDER BY date ASC
                ''',
                (
                    start_date.isoformat(),
                    end_date.isoformat(),
                ),
            ).fetchall()
        return result

    def interpolate_daily_values(self,
                                 rows: list[sqlite3.Row],
                                 start_date: datetime.date,
                                 end_date: datetime.date,
                                 ) -> list[tuple[datetime.date, float]]:
        """
        Fill missing days with linear interpolation.

        If data is missing between two known points, the value is distributed
        progressively between the two dates.

        If missing days are before the first known point or after the last one,
        the nearest known value is reused.

        :param rows: list of Rows with data
        :param start_date: initial date
        :param end_date: ending date
        :return: list with tuple with date and users count
        """
        known_values = {
            datetime.date.fromisoformat(row['date']): float(row['users_count'])
            for row in rows
        }
        known_dates = sorted(known_values)

        result = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in known_values:
                # Use the known value
                value = known_values[current_date]
            else:
                # Calculate values for the missing dates
                previous_date = next(reversed([date
                                               for date in known_dates
                                               if date < current_date]),
                                     None)
                next_date = next((date
                                  for date in known_dates
                                  if date > current_date),
                                 None)
                if previous_date and next_date:
                    # Create an interpolated medium value
                    previous_value = known_values[previous_date]
                    next_value = known_values[next_date]
                    total_days = (next_date - previous_date).days
                    current_days = (current_date - previous_date).days
                    value = (previous_value +
                             (next_value - previous_value) *
                             current_days / total_days)
                elif previous_date:
                    # Use the previous available data
                    value = known_values[previous_date]
                elif next_date:
                    # Use the next available data
                    value = known_values[next_date]
                else:
                    # No data
                    value = 0
            result.append((current_date, value))
            current_date += datetime.timedelta(days=1)
        return result

    def create_graph_image(self,
                           values: list[tuple[datetime.date, float]],
                           start_date: datetime.date,
                           end_date: datetime.date,
                           ) -> io.BytesIO:
        """
        Create the growth chart image.

        :param values: list with tuple with date and users count
        :param start_date: initial date
        :param end_date: ending date
        :return: binary data with the graph image
        """
        width = 600
        height = 400
        padding_left = 42
        padding_right = 22
        padding_top = 62
        padding_bottom = 32

        chart_left = padding_left
        chart_top = padding_top
        chart_right = width - padding_right
        chart_bottom = height - padding_bottom
        chart_width = chart_right - chart_left

        image = PIL.Image.new(mode='RGB',
                              size=(width, height),
                              color=BACKGROUND)
        draw = PIL.ImageDraw.Draw(im=image)

        title_font = load_font(size=15, bold=True)
        subtitle_font = load_font(size=10)
        label_font = load_font(size=9)

        draw.text(xy=(16, 9),
                  text='Members growth',
                  fill=TITLE_COLOR,
                  font=title_font)

        draw.text(xy=(16, 32),
                  text=f'From {start_date.isoformat()} '
                       f'to {end_date.isoformat()}',
                  fill=SUBTITLE_COLOR,
                  font=subtitle_font)

        numeric_values = [value for _, value in values]
        raw_min_value = min(numeric_values)
        raw_max_value = max(numeric_values)
        raw_range = raw_max_value - raw_min_value
        if raw_range <= 10:
            tick_step = 1
        elif raw_range <= 50:
            tick_step = 5
        elif raw_range <= 100:
            tick_step = 10
        elif raw_range <= 500:
            tick_step = 50
        elif raw_range <= 1000:
            tick_step = 100
        else:
            tick_step = 200

        min_value = math.floor(raw_min_value / tick_step) * tick_step
        max_value = math.ceil(raw_max_value / tick_step) * tick_step

        if min_value == max_value:
            min_value -= tick_step
            max_value += tick_step

        for value in range(int(min_value), int(max_value) + 1, tick_step):
            y = self.value_to_y(
                value=value,
                min_value=min_value,
                max_value=max_value,
                chart_top=chart_top,
                chart_bottom=chart_bottom,
            )
            draw.line(xy=(chart_left, y, chart_right, y),
                      fill=GRID_COLOR,
                      width=1)
            draw.text(xy=(12, y - 7),
                      text=str(value),
                      fill=TEXT_COLOR,
                      font=label_font)

        points = []

        if len(values) == 1:
            date, value = values[0]
            x = chart_left
            y = self.value_to_y(value=value,
                                min_value=min_value,
                                max_value=max_value,
                                chart_top=chart_top,
                                chart_bottom=chart_bottom)
            points.append((x, y))
        else:
            for index, (_, value) in enumerate(values):
                x = (chart_left +
                     int(chart_width * index / (len(values) - 1)))
                y = self.value_to_y(value=value,
                                    min_value=min_value,
                                    max_value=max_value,
                                    chart_top=chart_top,
                                    chart_bottom=chart_bottom)
                points.append((x, y))

        if len(points) == 1:
            x, y = points[0]
            draw.ellipse(xy=(x - 2, y - 2, x + 2, y + 2),
                         fill=LINE_COLOR)
        else:
            draw.line(xy=points,
                      fill=LINE_COLOR,
                      width=1)

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
            result = chart_bottom - round((chart_bottom - chart_top) * ratio)
        return result

    def draw_x_labels(self,
                      draw: PIL.ImageDraw.ImageDraw,
                      values: list[tuple[datetime.date, float]],
                      chart_left: int,
                      chart_right: int,
                      chart_bottom: int,
                      font: PIL.ImageFont.FreeTypeFont,
                      ) -> None:
        """
        Draw a few dates on X axis.
        """
        if values:
            labels_count = min(4, len(values))
            if labels_count == 1:
                indexes = [0]
            else:
                indexes = [
                    round(index * (len(values) - 1) / (labels_count - 1))
                    for index in range(labels_count)
                ]

            for index in indexes:
                date = values[index][0]
                text = date.strftime('%d %b')

                if len(values) == 1:
                    x = chart_left
                else:
                    x = chart_left + int(
                        (chart_right - chart_left) * index / (len(values) - 1)
                    )

                text_bbox = draw.textbbox(xy=(0, 0),
                                          text=text,
                                          font=font)
                text_width = text_bbox[2] - text_bbox[0]
                draw.text(xy=(x - text_width / 2, chart_bottom + 8),
                          text=text,
                          fill=TEXT_COLOR,
                          font=font)
