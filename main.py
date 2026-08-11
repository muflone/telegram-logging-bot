#!/usr/bin/env python
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

import logging
import os
import pathlib

from muflone_telegram_logging_bot.bot import Bot



def main():
    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(levelname)-7s - %(name)s - %(message)s',
        level=logging.INFO)
    # Set higher logging level for httpx to avoid all GET and POST requests
    # being logged
    logging.getLogger('httpx').setLevel(logging.WARNING)
    # Start the bot
    bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'),
              data_dir=pathlib.Path(os.environ.get('APP_DATA_DIR', 'data')))
    bot.run()


if __name__ == "__main__":
    main()
