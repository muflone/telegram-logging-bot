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

import dataclasses
import datetime
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class ParameterType(enum.StrEnum):
    STRING = 'string'
    INTEGER = 'integer'
    DECIMAL = 'decimal'
    DATE = 'date'
    DATETIME = 'datetime'
    OPTION = 'option'
    LIST = 'list'


@dataclasses.dataclass
class Parameter(object):
    name: str
    description: str
    type: ParameterType
    null: bool
    default: Any
    options: tuple[str, ...] = None

    def parse_value(self,
                    value: Any
                    ) -> Any:
        result = self.default if value is None else value
        if self.type in (ParameterType.STRING, ParameterType.OPTION):
            result = str(result)
        elif self.type == ParameterType.INTEGER:
            result = int(result)
        elif self.type == ParameterType.DECIMAL:
            result = float(result)
        elif self.type == ParameterType.DATE:
            result = datetime.date.strptime(result,
                                            '%Y-%m-%d')
        elif self.type == ParameterType.DATETIME:
            result = datetime.datetime.strptime(result,
                                                '%Y-%m-%d %H:%M:%S')
        elif self.type == ParameterType.LIST:
            result = result.split(',')
        return result
