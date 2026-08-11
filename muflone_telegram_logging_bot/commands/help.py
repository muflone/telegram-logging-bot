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

from typing import TYPE_CHECKING

from .base import BaseCommand

if TYPE_CHECKING:
    from typing import Optional

    import telegram
    import telegram.ext


class CommandHelp(BaseCommand):
    trigger: Optional[str] = 'help'
    description: Optional[str] = None

    def get_reply_text(self,
                       update: telegram.Update,
                       context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                       *args,
                       **kwargs
                       ) -> Optional[str]:
        commands_description = []
        for command in self.bot.commands.values():
            if command.trigger and command.description:
                commands_description.append(
                    f'/{command.trigger}\n'
                    f'{command.description}\n')
        return '\n'.join(commands_description)
