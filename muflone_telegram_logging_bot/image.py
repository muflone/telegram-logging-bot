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

import io
import pathlib
import random

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import telegram

COLOR_WHITE = '#FFFFFF'
COLOR_BLACK = '#000000'
COLOR_BLACK_RGBA = (0, 0, 0, 0)


def load_font(size: int,
              bold: bool = False
              ) -> PIL.ImageFont.FreeTypeFont:
    """
    Load a TrueType font if available
    """
    candidates = [
        '/usr/share/fonts/noto/NotoSansCJK-Regular.ttc' if bold else
        '/usr/share/fonts/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Medium.ttc' if bold else
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf' if bold else
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf' if bold else
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]

    for candidate in candidates:
        if pathlib.Path(candidate).exists():
            result = PIL.ImageFont.truetype(font=candidate,
                                            size=size)
            break
    else:
        result = PIL.ImageFont.load_default()
    return result


def circle_crop(image: PIL.Image.Image,
                size: int
                ) -> PIL.Image.Image:
    """
    Crop a circular image
    """
    image = image.convert(mode='RGBA').resize(size=(size, size))
    mask = PIL.Image.new(mode='L',
                         size=(size, size),
                         color=COLOR_BLACK)
    draw = PIL.ImageDraw.Draw(im=mask)
    draw.ellipse(xy=(0, 0, size - 1, size - 1),
                 fill=255)
    result = PIL.Image.new(mode='RGBA',
                           size=(size, size),
                           color=COLOR_BLACK_RGBA)
    result.paste(im=image,
                 box=(0, 0),
                 mask=mask)
    return result


def make_default_avatar(name: str,
                        size: int
                        ) -> PIL.Image.Image:
    """
    Create a fallback avatar image
    """
    random_colors = ('#5865f2', '#ed7192', '#61c14d', '#43adda', '#fa9c47')
    avatar = PIL.Image.new(mode='RGBA',
                           size=(size, size),
                           color=random.choice(random_colors))
    draw = PIL.ImageDraw.Draw(avatar)
    letter = name[:1].upper() if name else '?'
    font = load_font(size=24,
                     bold=True)
    bbox = draw.textbbox(xy=(0, 0),
                         text=letter,
                         font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(xy=((size - text_width) / 2 - 1, text_height / 2 - 2),
              text=letter,
              fill=COLOR_WHITE,
              font=font)
    return circle_crop(image=avatar,
                       size=size)


async def get_user_avatar(bot: telegram.Bot,
                          user_id: int,
                          name: str,
                          size: int
                          ) -> PIL.Image.Image:
    """
    Get Telegram user profile photo.
    If a photo is not available a new fallback avatar is generated
    """
    try:
        photos = await bot.get_user_profile_photos(user_id=user_id,
                                                   limit=1)
        if photos.photos:
            # Get latest photo
            photo = photos.photos[0][-1]
            file = await bot.get_file(photo.file_id)
            # Save the image to a temporary buffer
            buffer = io.BytesIO()
            await file.download_to_memory(out=buffer)
            buffer.seek(0)
            # Apply circular crop to the image
            image = PIL.Image.open(buffer)
            result = circle_crop(image=image,
                                 size=size)
        else:
            result = make_default_avatar(name=name,
                                         size=size)
    except telegram.error.TelegramError:
        result = make_default_avatar(name=name,
                                     size=size)
    return result
