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

import pathlib

from .database import Database


class Databases(object):
    def __init__(self,
                 filepath: pathlib.Path):
        self.data_dir = filepath / 'chats'
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)

    def get_known_groups(self) -> dict[int, pathlib.Path]:
        result = {}
        for group_dir in self.data_dir.iterdir():
            if group_dir.is_dir():
                # Get only numeric directories
                try:
                    chat_id = int(group_dir.name)
                except ValueError:
                    continue
                # Get database path
                db_path = self.get_database_path(directory_name=group_dir.name)
                if db_path.exists():
                    result[chat_id] = db_path
        return result

    def get_database_path(self,
                          directory_name: str) -> pathlib.Path:
        return pathlib.Path(self.data_dir / directory_name / 'data.sqlite')

    def get_database(self,
                     directory_name: str) -> Database:
        return Database(filepath=self.get_database_path(
            directory_name=directory_name))
