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
import zoneinfo


def utc_now_iso() -> str:
    """
    Get the current datetime in ISO format

    :return: current date in ISO as string
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def timezone_offset(tz_name: str,
                    when: datetime.datetime
                    ) -> str:
    """
    Return the time offset as HH:MM for a timezone

    :param tz_name: timezone name as zoneinfo.available_timezones()
    :param when: reference datime
    :return: string with {+/-}HH:MM
    """
    tz = zoneinfo.ZoneInfo(tz_name)

    if when.tzinfo is None:
        # Naive datetime to timezone
        dt = when.replace(tzinfo=tz)
    else:
        # Change timezone
        dt = when.astimezone(tz)
    # Get offset and calculate difference in seconds
    offset = dt.utcoffset()
    if offset is None:
        raise ValueError(f'Cannot determine UTC offset for {tz_name}')
    # Format result
    total_minutes = int(offset.total_seconds() // 60)
    sign = '+' if total_minutes >= 0 else '-'
    hours, minutes = divmod(abs(total_minutes), 60)
    return f'{sign}{hours:02d}:{minutes:02d}'
