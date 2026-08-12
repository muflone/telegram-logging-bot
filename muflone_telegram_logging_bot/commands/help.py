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
from ..trigger import Trigger

if TYPE_CHECKING:
    import telegram
    import telegram.ext


class CommandHelp(BaseCommand):
    def get_triggers(self) -> tuple[Trigger]:
        """
        Get triggers and callbacks

        :return: tuple of Trigger
        """
        return (
            Trigger(trigger='help',
                    description=None,
                    callback=self.do_trigger),
        )

    @BaseCommand.call_trigger
    async def do_trigger(self,
                         update: telegram.Update,
                         context: telegram.ext.ContextTypes.DEFAULT_TYPE,
                         trigger: Trigger,
                         ) -> None:
        commands_description = []
        for trigger in self.bot.triggers.values():
            if trigger.trigger and trigger.description:
                commands_description.append(
                    f'/{trigger.trigger}\n'
                    f'{trigger.description}\n')
        await update.message.reply_text('\n'.join(commands_description))
