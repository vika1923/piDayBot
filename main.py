import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardBuilder, InlineKeyboardButton
from aiogram.utils.formatting import Bold


# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for i in "ABCDEFGHIJKLMNOPQRSTUVYZ":
        builder.add(types.KeyboardButton(text=i))
    builder.adjust(4)
    await message.answer(
        "Choose Number",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


@dp.message()
async def echo_handler(message: types.Message):
    letter = message.text
    if letter in "ABCDEFGHIJKLMNOPQRSTUVYZ":
        await message.answer(f"Send photo with a person whose name starts with *{letter}*\ ", parse_mode="MarkdownV2")
    else:
        await message.answer("start over and choose the right letter")
    

async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
