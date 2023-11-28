import inspect

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.logs import log, logger


class Form(StatesGroup):
    percent = State()


class TelegramBot:
    def __init__(self, api_token: str, user_service):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.user_service = user_service

        self.handlers()

    @classmethod
    def keyboard(cls, commands: list[list]) -> types.ReplyKeyboardMarkup:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for row in commands:
            markup.row(*list(map(types.KeyboardButton, row)))

        return markup

    @classmethod
    def main_menu(cls, user: dict = None) -> list:
        menu = [
            [
                f"💸 {user['percent'] if user and user['percent'] else '1'}%",
                f"💡 {'ON' if user and user['notification'] else 'OFF'}",
            ],
            ["👤 ACC", "📎 HELP"],
        ]
        return menu

    @classmethod
    @property
    def admin_panel(cls) -> list:
        menu = [["⬅ MENU"]]

        return menu

    def handlers(self):
        @log(logger)
        @self.dp.message_handler(commands=["start"])
        async def commands_start(message: types.Message):
            if (
                await self.user_service.add_user(message.from_user.id, message.from_user.username)
            ) == 0:
                for admin in await self.user_service.get_admins:
                    await self.bot.send_message(
                        admin["id"],
                        f"&#128314           "
                        f"{md.hitalic('New user')}           "
                        f"&#128314\n\nStats:\n"
                        f"├{md.hbold('ID')}: {md.hcode(message.from_user.id)}\n"
                        f"├{md.hbold('Nick')}: @{message.from_user.username}\n"
                        f"├{md.hbold('Is_bot')}: {message.from_user.is_bot}\n",
                        parse_mode="html",
                    )

            user = await self.user_service.get_user(message.from_user.id)
            menu = self.main_menu(user)

            if user["is_admin"]:
                menu.append(["➡ ADMIN_PANEL"])

            markup = TelegramBot.keyboard(menu)

            await self.bot.send_message(
                message.from_user.id,
                f"Welcome back, @"
                f"{message.from_user.username if message.from_user.username else 'user'}\n",
                parse_mode="html",
                reply_markup=markup,
            )

            await message.delete()

        @log(logger)
        @self.dp.message_handler(commands=["account", "acc", "акк", "аккаунт"])
        @self.dp.message_handler(Text(equals=["👤 ACC"], ignore_case=True))
        async def commands_account(message: types.Message):
            user = await self.user_service.get_user(message.from_user.id)

            menu = self.main_menu(user)
            if user["is_admin"]:
                menu.append(["➡ ADMIN_PANEL"])
            markup = TelegramBot.keyboard(menu)

            await self.bot.send_message(
                message.from_user.id,
                f"\n&#128100My Profile:\n"
                f"├Alert % (min): "
                f"{md.hcode(str(user['percent']) + '%') if user['percent'] else md.hcode('1%')}\n"
                f"\n&#128276Alerts: {'on' if user['notification'] else 'off'}",
                parse_mode="html",
                reply_markup=markup,
            )
            await message.delete()

        @log(logger)
        @self.dp.message_handler(commands=["help", "hlp", "hp", "поддержка"])
        @self.dp.message_handler(Text(equals=["📎 HELP"], ignore_case=True))
        async def commands_help(message: types.Message):
            user = await self.user_service.get_user(message.from_user.id)
            menu = self.main_menu(user)
            if user["is_admin"]:
                menu.append(["➡ ADMIN_PANEL"])
            markup = TelegramBot.keyboard(menu)

            await self.bot.send_message(
                message.from_user.id,
                f"&#128206Details on each of the commands&#128206\n\n"
                f"/acc {md.hitalic('- get your bot account details')}\n"
                f"/sw {md.hitalic('- to resume/break connection to the parser notification')}\n"
                f"/prc {md.hitalic('- % of profit from which notifications will be sent')}"
                f" {md.hitalic('(standard: 1)')}\n",
                parse_mode="html",
                reply_markup=markup,
            )

            await message.delete()

        @log(logger)
        @self.dp.message_handler(commands=["status", "st", "switch", "sw", "change"])
        @self.dp.message_handler(Text(contains=["💡"], ignore_case=True))
        async def commands_status(message: types.Message):
            result = await self.user_service.update_notification(message.from_user.id)

            user = await self.user_service.get_user(message.from_user.id)
            menu = self.main_menu(user)
            if user["is_admin"]:
                menu.append(["➡ ADMIN_PANEL"])
            markup = TelegramBot.keyboard(menu)

            if result == 1:
                await self.bot.send_message(
                    message.from_user.id,
                    f"Alerts {md.hbold('on')}...\n\n"
                    f"As soon as I find a good deal, I'll send a notification&#9203"
                    f"To disable notifications, type &#128073 /sw",
                    parse_mode="html",
                    reply_markup=markup,
                )

            else:
                await self.bot.send_message(
                    message.from_user.id,
                    f"Alerts {md.hbold('off')}...\n\n"
                    f"To enable notifications, type &#128073 /sw",
                    parse_mode="html",
                    reply_markup=markup,
                )

            await message.delete()

        @log(logger)
        @self.dp.message_handler(commands=["percent", "%", "prc", "процент"])
        @self.dp.message_handler(Text(contains=["💸"], ignore_case=True))
        async def commands_prc(message: types.Message):
            markup = TelegramBot.keyboard([["X"]])

            await Form.percent.set()
            await self.bot.send_message(
                message.from_user.id,
                "Enter % of which you'd like to receive eth price change cases\n"
                "To cancel, type the command 👉 /cancel",
                parse_mode="html",
                reply_markup=markup,
            )

            await message.delete()

        @self.dp.message_handler(state="*", commands="cancel")
        @self.dp.message_handler(
            Text(equals=["cancel", "отмена", "❌", "X"], ignore_case=True), state="*"
        )
        async def cancel_handler(message: types.Message, state: FSMContext):
            func_name = inspect.currentframe().f_code.co_name

            try:
                await message.delete()

                current_state = await state.get_state()
                if current_state is None:
                    return

                if current_state.split(":")[1] in ["percent", "coin"]:
                    user = await self.user_service.get_user(message.from_user.id)
                    menu = self.main_menu(user)
                    if user["is_admin"]:
                        menu.append(["➡ ADMIN_PANEL"])
                    markup = TelegramBot.keyboard(menu)

                else:
                    markup = TelegramBot.keyboard(self.admin_panel)

                await self.bot.send_message(
                    message.from_user.id,
                    "Input stopped &#128219",
                    parse_mode="html",
                    reply_markup=markup,
                )

                await self.bot.delete_message(message.from_user.id, message.message_id - 1)

            except Exception as error:
                logger.error("%s/%s||%s", func_name, error.__class__, error.args[0])

            finally:
                await state.finish()
                logger.info("%s", func_name)

        @self.dp.message_handler(state=Form.percent)
        async def process_prc(message: types.Message, state: FSMContext):
            func_name = inspect.currentframe().f_code.co_name

            try:
                async with state.proxy() as data:
                    data["percent"] = message.text

                result = await self.user_service.update_percent(
                    message.from_user.id, float(data["percent"])
                )

                user = await self.user_service.get_user(message.from_user.id)
                menu = self.main_menu(user)
                if user["is_admin"]:
                    menu.append(["➡ ADMIN_PANEL"])
                markup = TelegramBot.keyboard(menu)

                if result == 0:
                    await self.bot.send_message(
                        message.from_user.id,
                        md.text(
                            md.text(
                                "Percent updated: " + md.hcode(data["percent"] + "%") + " &#128279"
                            ),
                            sep="\n",
                        ),
                        parse_mode="html",
                        reply_markup=markup,
                    )

                else:
                    await self.bot.send_message(
                        message.from_user.id,
                        "Incorrect input &#128219 \n" "Try again, type the command 👉 /prc",
                        parse_mode="html",
                        reply_markup=markup,
                    )

            except Exception as warning:
                try:
                    user = await self.user_service.get_user(message.from_user.id)["Response"]
                    menu = self.main_menu(user)
                    if user["is_admin"]:
                        menu.append(["➡ ADMIN_PANEL"])
                    markup = TelegramBot.keyboard(menu)

                    await self.bot.send_message(
                        message.from_user.id,
                        "Unexpected error &#128219 \n" "Try again, type the command 👉 /prc",
                        parse_mode="html",
                        reply_markup=markup,
                    )
                    logger.warning("%s/%s||%s", func_name, warning.__class__, warning.args[0])

                except Exception as error:
                    logger.error("%s/%s||%s", func_name, error.__class__, error.args[0])

            finally:
                await state.finish()
                logger.info("%s", func_name)

        @log(logger)
        @self.dp.message_handler(Text(equals=["⬅ MENU"], ignore_case=True))
        async def back_to_menu(message: types.Message):
            if {"id": message.from_user.id} in (await self.user_service.get_admins):
                user = await self.user_service.get_user(message.from_user.id)
                menu = self.main_menu(user)
                if user["is_admin"]:
                    menu.append(["➡ ADMIN_PANEL"])
                markup = TelegramBot.keyboard(menu)

                await self.bot.send_message(
                    message.from_user.id,
                    "Welcome back, @{}\n".format(
                        message.from_user.username if message.from_user.username else "user"
                    ),
                    parse_mode="html",
                    reply_markup=markup,
                )

                await message.delete()

        @log(logger)
        @self.dp.message_handler(Text(equals=["➡ ADMIN_PANEL"], ignore_case=True))
        async def enter_admin_panel(message: types.Message):
            if {"id": message.from_user.id} in (await self.user_service.get_admins):
                menu = self.admin_panel
                markup = TelegramBot.keyboard(menu)

                await self.bot.send_message(
                    message.from_user.id,
                    f"&#128272 Welcome to {md.hbold('TRACKER')} ADMIN PANEL, "
                    f"@{message.from_user.username if message.from_user.username else 'user'}\n",
                    parse_mode="html",
                    reply_markup=markup,
                )

                await message.delete()

    def start(self, skip_updates: bool = True):
        executor.start_polling(self.dp, skip_updates=skip_updates)
