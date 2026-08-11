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

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib


class Database(object):
    def __init__(self,
                 filepath: pathlib.Path):
        self.filepath = filepath
        # Open database connection and create the needed tables
        self.update_schema()

    def open(self) -> sqlite3.Connection:
        """
        Open database connection (used as context manager)
        """
        connection = sqlite3.connect(self.filepath)
        connection.row_factory = sqlite3.Row
        return connection

    def update_schema(self) -> None:
        """
        Create the needed tables
        """
        with self.open() as connection:
            connection.execute('PRAGMA journal_mode=WAL;')
            connection.execute('PRAGMA foreign_keys=ON;')
            connection.commit()
