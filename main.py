import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardBuilder, InlineKeyboardButton
from aiogram.utils.formatting import Bold
from aiogram.fsm.state import State, StatesGroup

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'Y', 'Z']
team_names = ["Σ", "e"]


# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")
print(TOKEN)

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


class TeamSubmissions(StatesGroup):
    name = State()
    letter = State()
    submission = State()


@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.set_state(TeamSubmissions.name)
    print(state)
    builder = ReplyKeyboardBuilder()
    for n in team_names:
        builder.add(types.KeyboardButton(text=n))
    await message.answer("Welcome! Submit photos with people you find here")
    await message.answer("What team are you?", reply_markup=builder.as_markup(resize_keyboard=True))




class TeamNameFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.text in team_names and len(message.text) == 1
@dp.message(TeamNameFilter())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TeamSubmissions.letter)
    print(state)
    builder = ReplyKeyboardBuilder()
    for i in letters:
        builder.add(types.KeyboardButton(text=i))
    builder.adjust(4)
    await message.answer(
        "Choose Letter",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )


class LetterFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.text in letters and len(message.text) == 1
@dp.message(LetterFilter())
async def echo_handler(message: types.Message, state: FSMContext):
    await state.set_state(TeamSubmissions.submission)
    await state.update_data(letter=message.text)

    letter = message.text
    await message.answer(f"Send photo with a person whose name starts with *{letter}*\ ", parse_mode="MarkdownV2")

@dp.message(F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    print("User sent a photo!") 

    data = await state.get_data()
    print(data["name"], data["letter"])
    await state.clear()
    


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
