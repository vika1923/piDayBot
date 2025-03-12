import asyncio
import logging
import sys
from os import getenv, listdir

from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, BaseFilter, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.formatting import Bold
from aiogram.fsm.state import State, StatesGroup

# letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'Y', 'Z']
letters = ['A', 'B', 'C']

team_names = ["Σ", "e", "∫", "∂/∂x"]
look_for_type = {"Σ":"person", "e":"person", "∫": "thing", "∂/∂x": "thing"}
file_name = {"Σ":"SIGMA", "e":"EULERS", "∫": "INTEGRAL", "∂/∂x": "DIFFERENTIATION"}


TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()



#  === FILTERS ===

class TeamSubmissions(StatesGroup):
    choosing_name = State()
    choosing_challenge = State()
    choosing_letter = State()
    submitting = State()

class NotCancelCommandFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return not message.text == "/cancel"
    
class TeamNameFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.text in team_names
    
class LetterFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.text.upper() in letters and len(message.text) == 1
    


#  === HANDLERS ===

@dp.message(StateFilter(None), CommandStart())
async def start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # If the user has already set a team name, ignore the command
    if "name" in user_data:
        await message.answer("You have already started. Continue submitting photos.")
        return
    
    await state.set_state(TeamSubmissions.choosing_name)
    await state.update_data(available_letters=letters.copy())
    builder = ReplyKeyboardBuilder()
    for n in team_names:
        builder.add(types.KeyboardButton(text=n))
    
    await message.answer("ATTENTION! \n\n1) Let only one member of the team submit the responses.\n\n2) Use /cancel to return back and submit a photo for a different letter if you misclicked.\n\n3) After the photo is submitted, it can not be changed.")
    await message.answer("What team are you?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(TeamSubmissions.choosing_name)


    
@dp.message(TeamSubmissions.choosing_name, TeamNameFilter())
async def handle_name_selection(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TeamSubmissions.choosing_challenge)
    
    # Create keyboard for challenge selection
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Alphabet Challenge"))
    builder.add(types.KeyboardButton(text="Keyboard Challenge"))
    builder.adjust(2)
    
    await message.answer(
        "Choose your challenge:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(TeamSubmissions.choosing_challenge)
async def handle_challenge_selection(message: types.Message, state: FSMContext):
    if message.text not in ["Alphabet Challenge", "Keyboard Challenge"]:
        await message.answer("Please select one of the available challenges")
        return
        
    await state.update_data(challenge=message.text)
    
    if message.text == "Alphabet Challenge":
        await state.set_state(TeamSubmissions.choosing_letter)
        # Get available letters from state
        user_data = await state.get_data()
        available_letters = user_data.get('available_letters', [])
        
        builder = ReplyKeyboardBuilder()
        for i in available_letters:
            builder.add(types.KeyboardButton(text=i))
        builder.adjust(4)
        
        await message.answer(
            "Choose a letter:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    else:  # Keyboard Challenge
        await state.set_state(TeamSubmissions.submitting)
        await message.answer(
            "Please send a photo of your keyboard:",
            reply_markup=types.ReplyKeyboardRemove()
        )

@dp.message(TeamSubmissions.choosing_name, NotCancelCommandFilter())
async def invalid_name(message: types.Message, state: FSMContext):
    await message.answer("Invalid name. \nUse the markup keyboard or copypaste a valid name: Σ, e, ∫, ∂/∂x.")


@dp.message(TeamSubmissions.choosing_letter, LetterFilter())
async def echo_handler(message: types.Message, state: FSMContext):
    letter = message.text
    await state.set_state(TeamSubmissions.submitting)
    await state.update_data(letter=letter)
    temp_data = (await state.get_data())['name']
    await message.answer(f"Send photo with a {look_for_type[temp_data]} whose name starts with *{letter}* ", parse_mode="MarkdownV2")

@dp.message(TeamSubmissions.choosing_letter, NotCancelCommandFilter())
async def invalid_name(message: types.Message, state: FSMContext):
    await message.answer("Invalid input. \nUse the markup keyboard or type in a latin letter.")



@dp.message(TeamSubmissions.submitting, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_path = file_info.file_path
    
    if data.get("challenge") == "Keyboard Challenge":
        # Save keyboard photo
        destination = f"receivedFromUser/team{file_name[data['name']]}/keyboard.jpg"
        await message.bot.download_file(file_path, destination)

        if len(listdir(f"receivedFromUser/team{file_name[data['name']]}")) > 3:
            await message.answer("Congratulations! You've completed both challenges! 🎉")
        else:
            # Transition to Alphabet Challenge
            await state.update_data(challenge="Alphabet Challenge")
            await state.set_state(TeamSubmissions.choosing_letter)
            
            # Setup letter selection keyboard
            builder = ReplyKeyboardBuilder()
            for i in data.get('available_letters', []):
                builder.add(types.KeyboardButton(text=i))
            builder.adjust(4)
            
            await message.answer(
                "Great! Now let's move on to the Alphabet Challenge. Choose a letter:",
                reply_markup=builder.as_markup(resize_keyboard=True)
            )
            return
    
    # Alphabet Challenge logic
    destination = f"receivedFromUser/team{file_name[data['name']]}/{data['letter']}.jpg"
    await message.bot.download_file(file_path, destination)
    
    available_letters = data.get('available_letters', [])
    if data["letter"] in available_letters:
        available_letters.remove(data["letter"])
    await state.update_data(available_letters=available_letters)
    
    if not available_letters:  # No more letters available
        if "keyboard.jpg" not in listdir(f"receivedFromUser/team{file_name[data['name']]}"):
            # Transition to Keyboard Challenge
            await state.update_data(challenge="Keyboard Challenge")
            await state.set_state(TeamSubmissions.submitting)
            await message.answer(
                "Excellent! You've completed the Alphabet Challenge. Now, let's do the Keyboard Challenge!\n\nPlease send a photo of your keyboard:",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            # Both challenges completed
            await message.answer(
                "Congratulations! You've completed both challenges! 🎉",
                reply_markup=types.ReplyKeyboardRemove()
            )
            await state.clear()
        return
    
    # Continue with Alphabet Challenge
    await state.set_state(TeamSubmissions.choosing_letter)
    builder = ReplyKeyboardBuilder()
    for i in available_letters:
        builder.add(types.KeyboardButton(text=i))
    builder.adjust(4)
    
    await message.answer(
        "Your photo has been received and will be evaluated by us! \nChoose next letter:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(TeamSubmissions.submitting, NotCancelCommandFilter())
async def invalid_name(message: types.Message, state: FSMContext):
    await message.answer("Invalid input. Please send a photo (photo as a file is not accepted).")



@dp.message(Command(commands=["cancel"]))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.set_state(TeamSubmissions.choosing_letter)
    await message.answer(
        text="Action cancelled. \nYou can rechoose letter"
    )


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
