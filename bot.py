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


class Bot:
    def __init__(self, token, database_url):
        self.updater = Updater(token)

        if database_url is None:
            self.dao = db.Dao(None)
        else:
            conn = psycopg2.connect(database_url)
            self.dao = db.Dao(conn)

        login_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_handler), CommandHandler('login', self.start_handler)],
            states={
                States.WAITING_PHONE: [MessageHandler(Filters.text & ~Filters.command, self.phone_handler)],
                States.WAITING_CODE: [MessageHandler(Filters.text & ~Filters.command, self.code_handler)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler)],
        )

        ticket_handler = ConversationHandler(
            entry_points=[CommandHandler('new_check', self.new_check_handler)],
            states={
                States.WAITING_NAMES: [MessageHandler(Filters.text & ~Filters.command, self.guest_name_handler)],
                States.WAITING_TICKET: [MessageHandler(Filters.photo, self.picture_handler)],
                States.TICKET_PICKS: [
                    CallbackQueryHandler(self.tickets_picks_next_handler, pattern="^NEXT$"),
                    CallbackQueryHandler(self.tickets_picks_prev_handler, pattern="^PREV$"),
                    CallbackQueryHandler(self.tickets_picks_finish_handler, pattern="^FINISH$"),
                    CallbackQueryHandler(self.ticket_picks_yes_handler, pattern=".*_YES$"),
                    CallbackQueryHandler(self.ticket_picks_no_handler, pattern=".*_NO$")
                ]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler),
                       CallbackQueryHandler(self.inline_cancel_handler, pattern="CANCEL")],
        )

        self.updater.dispatcher.add_handler(login_handler)
        self.updater.dispatcher.add_handler(ticket_handler)

    def __is_correct_number(self, tel_num):
        if tel_num[0] == '+':
            if len(tel_num) != 12:
                return False
            tel_num = tel_num[1:]
        else:
            if len(tel_num) != 11:
                return False
        if tel_num[0] != '7' and tel_num[0] != '8':
            return False
        if tel_num[1] != '9':
            return False

        for c in tel_num:
            if not c.isdigit():
                return False

        return True

    def __is_correct_code(self, code, number, context):
        try:
            if len(code) != 4:
                return False
            for c in code:
                if not c.isdigit():
                    return False
            context.user_data["id"], context.user_data["refresh"] = fns_api.send_login_code(number, code)
            return True
        except InvalidSmsCodeException:
            return False

    def start_handler(self, update: Update, _: CallbackContext):
        update.effective_message.reply_text("Привет! Введите номер телефона: ")
        return States.WAITING_PHONE

    def new_check_handler(self, update: Update, context: CallbackContext):
        if "refresh" in context.user_data.keys():
            try:
                context.user_data["id"] = fns_api.refresh_session(context.user_data["refresh"])
            except InvalidSessionIdException:
                update.effective_message.reply_text('Что-то пошло не так. Введите команду /login')
                return ConversationHandler.END
            update.effective_message.reply_text \
                ("Введите имена пользователей(для каждого пользователя введите имя на новой строчке): ")
            return States.WAITING_NAMES
        else:
            update.effective_message.reply_text('Вы не авторизованы. Введите команду /login')
            return ConversationHandler.END


    def phone_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text

        if self.__is_correct_number(mess):
            update.effective_message.reply_text('Введите код из СМС:')
            if mess[0] == '7' or mess[0] == '8':
                mess = '+7' + mess[1:]
            context.user_data['phone'] = mess
            fns_api.send_login_sms(context.user_data['phone'])
            return States.WAITING_CODE

        update.effective_message.reply_text("Неверный номер телефона, если хотите прекратить работу, введите /cancel")
        return States.WAITING_PHONE

    def code_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text

        current_is_correct_code = self.__is_correct_code(mess, context.user_data['phone'], context)

        if current_is_correct_code:
            update.effective_message.reply_text\
                ('Введите команду /new_check для обработки чека:')
            return ConversationHandler.END
        elif current_is_correct_code is None:
            update.effective_message.reply_text \
                ('Какие-то проблемы с телефоном, введите его еще раз:')
            return States.WAITING_PHONE

        update.effective_message.reply_text("Неверный код, если хотите прекратить работу, введите /cancel")
        return States.WAITING_CODE

    def cancel_handler(self, update: Update, _: CallbackContext):
        update.effective_message.reply_text('Для разделения нового чека введите комманду /new_check')
        return ConversationHandler.END

    def inline_cancel_handler(self, update: Update, _: CallbackContext):
        update.effective_message.edit_text('Операция отменена.\n'
                                           'Для разделения нового чека введите комманду /new_check')
        return ConversationHandler.END

    def ticket_picks_yes_handler(self, update: Update, context: CallbackContext):
        callback_name = update.callback_query.data[:-4]
        current_pos = context.user_data["current_pos"]
        context.user_data["users_for_position"][current_pos].append(callback_name)
        new_keyboard = self.__make_keyboard_by_position(context.user_data["names"],
                                                        context.user_data["users_for_position"][current_pos],
                                                        first=current_pos == 0,
                                                        last=current_pos == len(context.user_data["check"]) - 1)
        update.effective_message.edit_reply_markup(reply_markup=new_keyboard)

    def ticket_picks_no_handler(self, update: Update, context: CallbackContext):
        callback_name = update.callback_query.data[:-3]
        current_pos = context.user_data["current_pos"]
        context.user_data["users_for_position"][current_pos].remove(callback_name)
        new_keyboard = self.__make_keyboard_by_position(context.user_data["names"],
                                                        context.user_data["users_for_position"][current_pos],
                                                        first=current_pos == 0,
                                                        last=current_pos == len(context.user_data["check"]) - 1)
        update.effective_message.edit_reply_markup(reply_markup=new_keyboard)

    def tickets_picks_prev_handler(self, update: Update, context: CallbackContext):
        context.user_data["current_pos"] -= 1
        current_pos = context.user_data["current_pos"]
        keyboard = self.__make_keyboard_by_position(context.user_data["names"],
                                                    context.user_data["users_for_position"][current_pos],
                                                    first=current_pos == 0)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(position_name + ' - ' + str(context.user_data["check"][current_pos].price) +
                                           ' руб.', reply_markup=keyboard)

    def tickets_picks_next_handler(self, update: Update, context: CallbackContext):
        context.user_data["current_pos"] += 1
        current_pos = context.user_data["current_pos"]
        keyboard = self.__make_keyboard_by_position(context.user_data["names"],
                                                    context.user_data["users_for_position"][current_pos],
                                                    last=current_pos == len(context.user_data["check"]) - 1)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(position_name + ' - ' + str(context.user_data["check"][current_pos].price) +
                                           ' руб.', reply_markup=keyboard)

    def tickets_picks_finish_handler(self, update: Update, context: CallbackContext):
        answer = ''
        for name in context.user_data['names']:
            debt = 0
            for j in range(len(context.user_data['check'])):
                if name in context.user_data['users_for_position'][j]:
                    debt += context.user_data['check'][j].price / len(context.user_data['users_for_position'][j])
            answer +=  name + ' должен заплатить ' + ("%.2f" % debt)  + ' руб.\n'

        update.effective_message.edit_text(answer)

    def guest_name_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text
        context.user_data["names"] = mess.splitlines()
        update.effective_message.reply_text('Пришлите фотографию QR-кода с чека:')
        return States.WAITING_TICKET

    def picture_handler(self, update: Update, context: CallbackContext):
        sess_id = context.user_data['id']
        photo_file = update.message.photo[-1].get_file().download_as_bytearray()
        url = update.message.photo[-1].get_file().file_path
        uniq_id = update.message.photo[-1].get_file().file_unique_id
        text, got = readerQR.twoQRreaders(url, uniq_id, photo_file)
        if got:
            try:
                check = get_receipt(text, sess_id)
                context.user_data["check"] = check.items
                context.user_data["users_for_position"] = [[] for _ in range(len(check.items))]
                context.user_data["current_pos"] = 0
                keyboard = self.__make_keyboard_by_position(context.user_data["names"],
                                                            context.user_data["users_for_position"][0],
                                                            first=True)
                update.effective_message.reply_text(f"{check.items[0].name} - {check.items[0].price} руб.",
                                                    reply_markup=keyboard)
                return States.TICKET_PICKS
            except InvalidTicketIdException:
                if "refresh" in context.user_data.keys():
                    try:
                        context.user_data["id"] = fns_api.refresh_session(context.user_data["refresh"])
                    except InvalidSessionIdException:
                        update.effective_message.reply_text('Что-то пошло не так. Введите команду /login')
                        return ConversationHandler.END
        else:
            update.effective_message.reply_text("QR-код не читаем или его нет")
            return States.WAITING_TICKET

    def __make_keyboard_by_position(self, names, users_for_position, first=False, last=False):
        buttons = []
        for name in names:
            if name in users_for_position:
                buttons.append([InlineKeyboardButton(f"✅ {name}", callback_data=f"{name}_NO")])
            else:
                buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"{name}_YES")])

        prev = InlineKeyboardButton("Prev", callback_data="PREV")
        next = InlineKeyboardButton("Next", callback_data="NEXT")
        finish = InlineKeyboardButton("Finish", callback_data="FINISH")

        if first:
            buttons.append([next])
        elif last:
            buttons.append([prev, finish])
        else:
            buttons.append([prev, next])

        buttons.append([InlineKeyboardButton("Отмена", callback_data="CANCEL")])

        return InlineKeyboardMarkup(buttons)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
