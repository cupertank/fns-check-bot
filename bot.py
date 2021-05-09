import re
from typing import Optional

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, \
    CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import psycopg2
import db
import fns_api
import readerQR
from fns_api.exceptions import *
from fns_api.fns_api import get_receipt
from states import States
from strings import Strings


class Bot:
    def __init__(self, token, database_url):
        self.updater = Updater(token)

        if database_url is None:
            self.dao = db.Dao(None)
        else:
            conn = psycopg2.connect(database_url)
            self.dao = db.Dao(conn)

        login_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_handler, run_async=True),
                          CommandHandler('login', self.start_handler, run_async=True)],
            states={
                States.WAITING_PHONE: [MessageHandler(Filters.text & ~Filters.command, self.phone_handler, run_async=True)],
                States.WAITING_CODE: [MessageHandler(Filters.text & ~Filters.command, self.code_handler, run_async=True)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler, run_async=True),
                       MessageHandler(Filters.update.message, self.wrong_handler, run_async=True)],
            run_async=True
        )

        ticket_handler = ConversationHandler(
            entry_points=[CommandHandler('new_receipt', self.new_check_handler, run_async=True)],
            states={
                States.WAITING_NAMES: [MessageHandler(Filters.text & ~Filters.command, self.guest_name_handler, run_async=True)],
                States.WAITING_TICKET: [MessageHandler(Filters.photo, self.picture_handler, run_async=True)],
                States.TICKET_PICKS: [
                    CallbackQueryHandler(self.tickets_picks_next_handler, pattern="^NEXT$"),
                    CallbackQueryHandler(self.tickets_picks_prev_handler, pattern="^PREV$"),
                    CallbackQueryHandler(self.tickets_picks_finish_handler, pattern="^FINISH$"),
                    CallbackQueryHandler(self.ticket_picks_yes_handler, pattern=".*_YES$"),
                    CallbackQueryHandler(self.ticket_picks_no_handler, pattern=".*_NO$")
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler, run_async=True),
                       CallbackQueryHandler(self.inline_cancel_handler, pattern="CANCEL"),
                       MessageHandler(Filters.update.message, self.wrong_handler, run_async=True)]
        )

        self.updater.dispatcher.add_handler(CommandHandler('help', self.help_handler, run_async=True))
        self.updater.dispatcher.add_handler(login_handler)
        self.updater.dispatcher.add_handler(ticket_handler)
        self.updater.dispatcher.add_handler(MessageHandler(Filters.update.message, self.help_handler, run_async=True))

    @staticmethod
    def __format_number(tel_num: str) -> Optional[str]:
        tel_num = tel_num.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        match = re.match(r"^(\+7|8|7)(\d{10})$", tel_num)
        if match is None:
            return None
        tel_num = f"+7{match[2]}"
        return tel_num

    @staticmethod
    def __is_correct_code(code):
        match = re.match(r"^\d{4}$", code)
        if match is None:
            return False
        return True

    @staticmethod
    def help_handler(update: Update, _: CallbackContext):
        update.effective_message.reply_text(
            text=Strings.HELP,
            parse_mode='HTML'
        )

    def start_handler(self, update: Update, _: CallbackContext):
        uid = update.effective_user.id
        refresh_id = self.dao.get_refresh_token(uid)
        if refresh_id is not None:
            update.effective_message.reply_text(Strings.AlreadyLogin, parse_mode="HTML")
            return ConversationHandler.END
        update.effective_message.reply_text(
            text=Strings.START,
            parse_mode='HTML'
        )
        return States.WAITING_PHONE

    def new_check_handler(self, update: Update, _: CallbackContext):
        uid = update.effective_user.id
        refresh_id = self.dao.get_refresh_token(uid)
        if refresh_id is not None:
            update.effective_message.reply_text(
                text=Strings.EnterNames,
                parse_mode="HTML"
            )
            return States.WAITING_NAMES
        else:
            update.effective_message.reply_text(Strings.UNAUTHORIZED_PLEASE_LOGIN, parse_mode="HTML")
            return ConversationHandler.END

    @staticmethod
    def wrong_handler(update: Update, _: CallbackContext):
        update.effective_message.reply_text(Strings.Wrong)

    @staticmethod
    def phone_handler(update: Update, context: CallbackContext):
        mess = update.effective_message.text

        # format and check correctness
        mess = Bot.__format_number(mess)

        if mess is not None:
            context.user_data['phone'] = mess
            try:
                fns_api.send_login_sms(context.user_data['phone'])
                update.effective_message.reply_text(Strings.EnterSMS, parse_mode="HTML")
            except InvalidPhoneException:
                update.effective_message.reply_text(Strings.InvalidPhone)
                return ConversationHandler.END
            except TooManyRequests:
                update.effective_message.reply_text(Strings.TooManyRequests, parse_mode="HTML")
                return ConversationHandler.END
            except FNSConnectionError:
                update.effective_message.reply_text(Strings.ConnectionToFNSLost)
                return States.END
            return States.WAITING_CODE

        update.effective_message.reply_text(Strings.InvalidPhoneTryAgain)
        return States.WAITING_PHONE

    def code_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text

        is_correct = Bot.__is_correct_code(mess)

        if is_correct:
            try:
                session_id, refresh_id = fns_api.send_login_code(context.user_data['phone'], mess)
                uid = update.effective_user.id
                self.dao.set_session_id(uid, session_id)
                self.dao.set_refresh_token(uid, refresh_id)
            except:
                update.effective_message.reply_text('Возникли проблемы с кодом, введите его еще раз:')
                return States.WAITING_CODE
            update.effective_message.reply_text(Strings.BeginInteractionQrCode)
            return ConversationHandler.END

        update.effective_message.reply_text(Strings.InvalidCode)
        return States.WAITING_CODE

    def cancel_handler(self, update: Update, _: CallbackContext):
        text = Strings.HowToAuthenticate
        uid = update.effective_user.id
        refresh_id = self.dao.get_refresh_token(uid)
        if refresh_id is not None:
            text = Strings.BeginInteractionQrCode
        update.effective_message.reply_text(f"{Strings.OperationCancelled}\n\n{text}")
        return ConversationHandler.END

    @staticmethod
    def inline_cancel_handler(update: Update, _: CallbackContext):
        update.callback_query.answer()
        update.effective_message.edit_text(f"{Strings.OperationCancelled}\n\n{Strings.BeginInteractionQrCode}")
        return ConversationHandler.END

    @staticmethod
    def ticket_picks_yes_handler(update: Update, context: CallbackContext):
        update.callback_query.answer()
        callback_name = update.callback_query.data[:-4]
        current_pos = context.user_data["current_pos"]
        context.user_data["users_for_position"][current_pos].append(callback_name)
        new_keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                       context.user_data["users_for_position"][current_pos],
                                                       first=current_pos == 0,
                                                       last=current_pos == len(context.user_data["check"]) - 1)
        update.effective_message.edit_reply_markup(reply_markup=new_keyboard)

    @staticmethod
    def ticket_picks_no_handler(update: Update, context: CallbackContext):
        update.callback_query.answer()
        callback_name = update.callback_query.data[:-3]
        current_pos = context.user_data["current_pos"]
        context.user_data["users_for_position"][current_pos].remove(callback_name)
        new_keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                       context.user_data["users_for_position"][current_pos],
                                                       first=current_pos == 0,
                                                       last=current_pos == len(context.user_data["check"]) - 1)
        update.effective_message.edit_reply_markup(reply_markup=new_keyboard)

    @staticmethod
    def tickets_picks_prev_handler(update: Update, context: CallbackContext):
        update.callback_query.answer()
        context.user_data["current_pos"] -= 1
        current_pos = context.user_data["current_pos"]
        keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                   context.user_data["users_for_position"][current_pos],
                                                   first=current_pos == 0)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(
            f"{position_name} - {context.user_data['check'][current_pos].sum} {Strings.rubles}",
            reply_markup=keyboard
        )

    @staticmethod
    def tickets_picks_next_handler(update: Update, context: CallbackContext):
        current_pos = context.user_data["current_pos"]
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        if len(current_users_for_position) == 0:
            update.callback_query.answer(Strings.SelectPeople, show_alert=True)
            return

        update.callback_query.answer()
        context.user_data["current_pos"] += 1
        current_pos += 1
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                   current_users_for_position,
                                                   last=current_pos == len(context.user_data["check"]) - 1)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(
            f"{position_name} - {context.user_data['check'][current_pos].sum} {Strings.rubles}",
            reply_markup=keyboard
        )

    @staticmethod
    def tickets_picks_finish_handler(update: Update, context: CallbackContext):
        current_pos = context.user_data["current_pos"]
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        if len(current_users_for_position) == 0:
            update.callback_query.answer(Strings.SelectPeople, show_alert=True)
            return

        update.callback_query.answer()
        answer = []
        for name in context.user_data['names']:
            debt = []
            sum = 0
            for j in range(len(context.user_data['check'])):
                if name in context.user_data['users_for_position'][j]:
                    sum += context.user_data['check'][j].sum / len(context.user_data['users_for_position'][j])
                    debt.append([context.user_data['check'][j].name, context.user_data['check'][j].sum / len(context.user_data['users_for_position'][j])])
            answer.append([f"{name[:-6]} {Strings.shallPay} {'%.2f' % sum} {Strings.rubles}\n", debt])

        update.effective_message.delete()
        update.effective_message.reply_text(f"{Strings.ResultsHeader}\n\n")
        for result in answer:
            pay_list = ''
            if len(result[1]) == 0:
                continue
            for position in result[1]:
                pay_list += f"{position[0]} - {'%.2f' % position[1]} {Strings.rubles}\n"
            update.effective_message.reply_text(f"{result[0]}\n\n"
                                               f"{Strings.PayingFor}\n"
                                               f"{pay_list}")

        update.effective_message.reply_text(f"{Strings.RepeatInteractionQrCode}\n"
                                            f"{Strings.AdvertisingFooter}")
        return ConversationHandler.END

    @staticmethod
    def guest_name_handler(update: Update, context: CallbackContext):
        mess = update.effective_message.text
        if len(mess.splitlines()) == 1 or len(mess.splitlines()) > 10:
            update.effective_message.reply_text(
                text=Strings.IncorrectFormat
            )
            return States.WAITING_NAMES
        context.user_data["names"] = [name + str(100000 + i) for i, name in enumerate(mess.splitlines())]
        update.effective_message.reply_text(Strings.EnterQR)
        return States.WAITING_TICKET

    def picture_handler(self, update: Update, context: CallbackContext):
        uid = update.effective_user.id
        sess_id = self.dao.get_session_id(uid)
        file_info = update.message.photo[-1].get_file()
        url = file_info.file_path
        uniq_id = file_info.file_unique_id
        wait_message = update.effective_message.reply_text(Strings.PleaseWait)
        text, got = readerQR.main_qr_reader(url, uniq_id)
        if got:
            try:
                check = get_receipt(text, sess_id)
                context.user_data["check"] = check.items
                context.user_data["users_for_position"] = [[] for _ in range(len(check.items))]
                context.user_data["current_pos"] = 0
                keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                           context.user_data["users_for_position"][0],
                                                           first=True,
                                                           last=len(check.items) == 1)
                wait_message.edit_text(f"{check.items[0].name} - {check.items[0].sum} {Strings.rubles}",
                                       reply_markup=keyboard)
                return States.TICKET_PICKS
            except InvalidTicketIdException:
                refresh = self.dao.get_refresh_token(uid)
                if refresh is not None:
                    try:
                        sess_id = fns_api.refresh_session(refresh)
                        self.dao.set_session_id(uid, sess_id)
                        try:
                            check = get_receipt(text, self.dao.get_session_id(uid))
                            context.user_data["check"] = check.items
                            context.user_data["users_for_position"] = [[] for _ in range(len(check.items))]
                            context.user_data["current_pos"] = 0
                            keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                                       context.user_data["users_for_position"][0],
                                                                       first=True)
                            wait_message.edit_text(
                                f"{check.items[0].name} - {check.items[0].sum} {Strings.rubles}",
                                reply_markup=keyboard)
                        except:
                            update.effective_message.reply_text(Strings.FNSLoginError)
                            return ConversationHandler.END
                    except (InvalidSessionIdException, FNSConnectionError):
                        update.effective_message.reply_text(Strings.FNSLoginError)
                        return ConversationHandler.END
            except FNSConnectionError:
                update.effective_message.reply_text(Strings.FNSLoginError)
                return ConversationHandler.END
        else:
            update.effective_message.reply_text(Strings.CouldNotReadQR)
            return States.WAITING_TICKET

    @staticmethod
    def __make_keyboard_by_position(names, users_for_position, first=False, last=False):
        buttons = []
        for name in names:
            if name in users_for_position:
                buttons.append([InlineKeyboardButton(f"✅ {name[:-6]}", callback_data=f"{name}_NO")])
            else:
                buttons.append([InlineKeyboardButton(f"❌ {name[:-6]}", callback_data=f"{name}_YES")])

        prev_button = InlineKeyboardButton(Strings.Prev, callback_data="PREV")
        next_button = InlineKeyboardButton(Strings.Next, callback_data="NEXT")
        finish_button = InlineKeyboardButton(Strings.Finish, callback_data="FINISH")

        navigation_buttons = []
        if not first:
            navigation_buttons.append(prev_button)
        if last:
            navigation_buttons.append(finish_button)
        else:
            navigation_buttons.append(next_button)
        buttons.append(navigation_buttons)

        buttons.append([InlineKeyboardButton(Strings.Cancel, callback_data="CANCEL")])

        return InlineKeyboardMarkup(buttons)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
