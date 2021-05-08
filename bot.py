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

        self.updater.dispatcher.add_handler(CommandHandler('help', self.help_handler))
        self.updater.dispatcher.add_handler(login_handler)
        self.updater.dispatcher.add_handler(ticket_handler)

    @staticmethod
    def __is_correct_number(tel_num):
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

    @staticmethod
    def __is_correct_code(code, number, context):
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

    @staticmethod
    def help_handler(update: Update, _: CallbackContext):
        update.effective_message.reply_text(
            text="Бот для разделения чеков на компанию.\n" +
                 "Алгоритм работы:\n" +
                 "1) Введите номер телефона для авторизации в системе ФНС.\n" +
                 "2) Введите код подтверждения из СМС.\n" +
                 "3) Введите имена всех людей, среди которых делится чек, включая платившего, если такой есть.\n" +
                 "4) Над появившейся клавиатурой написано название позиции. Отмечайте гостей, которым принадлежит эта позиция, нажимая на их имена.\n" +
                 "5) Для перехода к следующей позиции используйте кнопку \"Next\", к предыдущей - \"Prev\", для отмены операции - \"Cancel\".\n" +
                 "6) После распределения позиций по гостям нажмите кнопку \"Finish\"\n" +
                 "Список команд:\n" +
                 "/new_check - разделение нового чека.\n" +
                 "/login - авторизация в системе.\n" +
                 "/cancel - отмена текущей операции.\n" +
                 "/help - помощь.\n"
        )

    @staticmethod
    def start_handler(update: Update, _: CallbackContext):
        update.effective_message.reply_text(
            "Привет! Для полной информации о боте введите команду /help. Для продолжения работы введите номер телефона для авторизации на сервере ФНС: "
        )
        return States.WAITING_PHONE

    @staticmethod
    def new_check_handler(update: Update, context: CallbackContext):
        if "refresh" in context.user_data.keys():
            update.effective_message.reply_text(
                text="Введите имена пользователей. Отправьте их по одному на строчке в одном сообщении." +
                     " Обратите внимание, что недопустим ввод одного имени одного пользователя.\n\n" +
                     "Пример:\n" +
                     "Вася\nПетя\nВаня"
            )
            return States.WAITING_NAMES
        else:
            update.effective_message.reply_text('Вы не авторизованы в системе. Для авторизации введите команду /login:')
            return ConversationHandler.END

    @staticmethod
    def phone_handler(update: Update, context: CallbackContext):
        mess = update.effective_message.text

        if Bot.__is_correct_number(mess):
            if mess[0] == '7' or mess[0] == '8':
                mess = '+7' + mess[1:]
            context.user_data['phone'] = mess
            try:
                fns_api.send_login_sms(context.user_data['phone'])
                update.effective_message.reply_text('Введите код подтверждения из СМС:')
            except InvalidPhoneException:
                update.effective_message.reply_text(
                    'Слишком много запросов, повторите попытку позже. Для повторной авторизации введите команду /login:'
                )
                return ConversationHandler.END
            return States.WAITING_CODE

        update.effective_message.reply_text("Неверный номер телефона, если хотите прекратить работу, введите /cancel")
        return States.WAITING_PHONE

    @staticmethod
    def code_handler(update: Update, context: CallbackContext):
        mess = update.effective_message.text

        current_is_correct_code = Bot.__is_correct_code(mess, context.user_data['phone'], context)

        if current_is_correct_code:
            update.effective_message.reply_text('Введите команду /new_check для разделения чека:')
            return ConversationHandler.END
        elif current_is_correct_code is None:
            update.effective_message.reply_text('Возникли проблемы с номером телефона, введите его еще раз:')
            return States.WAITING_PHONE

        update.effective_message.reply_text("Неверный код, если хотите прекратить работу, введите /cancel")
        return States.WAITING_CODE

    @staticmethod
    def cancel_handler(update: Update, context: CallbackContext):
        text = 'Для авторизации введите команду /login'
        if "refresh" in context.user_data.keys():
            text = 'Для разделения нового чека введите команду /new_check'
        update.effective_message.reply_text("Операция отменена.\n" + text)
        return ConversationHandler.END

    @staticmethod
    def inline_cancel_handler(update: Update, _: CallbackContext):
        update.effective_message.edit_text('Операция отменена.\n'
                                           'Для разделения нового чека введите команду /new_check')
        return ConversationHandler.END

    @staticmethod
    def ticket_picks_yes_handler(update: Update, context: CallbackContext):
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
        context.user_data["current_pos"] -= 1
        current_pos = context.user_data["current_pos"]
        keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                   context.user_data["users_for_position"][current_pos],
                                                   first=current_pos == 0)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(position_name + ' - ' + str(context.user_data["check"][current_pos].price) +
                                           ' руб.', reply_markup=keyboard)

    @staticmethod
    def tickets_picks_next_handler(update: Update, context: CallbackContext):
        current_pos = context.user_data["current_pos"]
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        if len(current_users_for_position) == 0:
            update.callback_query.answer("Выберите пользователей", show_alert=True)
            return

        context.user_data["current_pos"] += 1
        current_pos += 1
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                   current_users_for_position,
                                                   last=current_pos == len(context.user_data["check"]) - 1)
        position_name = context.user_data["check"][current_pos].name
        update.effective_message.edit_text(position_name + ' - ' + str(context.user_data["check"][current_pos].price) +
                                           ' руб.', reply_markup=keyboard)

    @staticmethod
    def tickets_picks_finish_handler(update: Update, context: CallbackContext):
        current_pos = context.user_data["current_pos"]
        current_users_for_position = context.user_data["users_for_position"][current_pos]
        if len(current_users_for_position) == 0:
            update.callback_query.answer("Выберите пользователей", show_alert=True)
            return

        answer = ''
        for name in context.user_data['names']:
            debt = 0
            for j in range(len(context.user_data['check'])):
                if name in context.user_data['users_for_position'][j]:
                    debt += context.user_data['check'][j].price / len(context.user_data['users_for_position'][j])
            answer += name + ' должен заплатить ' + ("%.2f" % debt) + ' руб.\n'

        update.effective_message.reply_text(answer + '\nДля разделения нового чека введите команду /new_check')

    @staticmethod
    def guest_name_handler(update: Update, context: CallbackContext):
        mess = update.effective_message.text
        if len(mess.splitlines()) == 1:
            update.effective_message.reply_text(
                text='Неверный формат ввода. Обратите внимание на пример и пришлите список имен пользователей снова'
            )
            return States.WAITING_NAMES
        context.user_data["names"] = mess.splitlines()
        update.effective_message.reply_text('Пришлите фотографию QR-кода с чека:')
        return States.WAITING_TICKET

    @staticmethod
    def picture_handler(update: Update, context: CallbackContext):
        sess_id = context.user_data['id']
        file_info = update.message.photo[-1].get_file()
        url = file_info.file_path
        uniq_id = file_info.file_unique_id
        wait_message = update.effective_message.reply_text("Пожалуйста, подождите...")
        text, got = readerQR.main_qr_reader(url, uniq_id)
        if got:
            try:
                check = get_receipt(text, sess_id)
                context.user_data["check"] = check.items
                context.user_data["users_for_position"] = [[] for _ in range(len(check.items))]
                context.user_data["current_pos"] = 0
                keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                            context.user_data["users_for_position"][0],
                                                            first=True)
                wait_message.edit_text(f"{check.items[0].name} - {check.items[0].price} руб.",
                                       reply_markup=keyboard)
                return States.TICKET_PICKS
            except InvalidTicketIdException:
                if "refresh" in context.user_data.keys():
                    try:
                        context.user_data["id"] = fns_api.refresh_session(context.user_data["refresh"])
                        try:
                            check = get_receipt(text, context.user_data['id'])
                            context.user_data["check"] = check.items
                            context.user_data["users_for_position"] = [[] for _ in range(len(check.items))]
                            context.user_data["current_pos"] = 0
                            keyboard = Bot.__make_keyboard_by_position(context.user_data["names"],
                                                                        context.user_data["users_for_position"][0],
                                                                        first=True)
                            update.effective_message.reply_text(f"{check.items[0].name} - {check.items[0].price} руб.",
                                                                reply_markup=keyboard)
                        except:
                            update.effective_message.reply_text(
                                'На сервере ФНС что-то пошло не так. Авторизуйтесь, пожалуйста, заново. ' +
                                'Для этого введите команду /login'
                            )
                            return ConversationHandler.END
                    except InvalidSessionIdException:
                        update.effective_message.reply_text(
                            'На сервере ФНС что-то пошло не так. Авторизуйтесь, пожалуйста, заново. ' +
                            'Для этого введите команду /login'
                        )
                        return ConversationHandler.END
        else:
            update.effective_message.reply_text("QR-код не читаем или его нет. Пришлите новую фотографию QR-кода")
            return States.WAITING_TICKET

    @staticmethod
    def __make_keyboard_by_position(names, users_for_position, first=False, last=False):
        buttons = []
        for name in names:
            if name in users_for_position:
                buttons.append([InlineKeyboardButton(f"✅ {name}", callback_data=f"{name}_NO")])
            else:
                buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"{name}_YES")])

        prev_button = InlineKeyboardButton("Prev", callback_data="PREV")
        next_button = InlineKeyboardButton("Next", callback_data="NEXT")
        finish_button = InlineKeyboardButton("Finish", callback_data="FINISH")

        if first:
            buttons.append([next_button])
        elif last:
            buttons.append([prev_button, finish_button])
        else:
            buttons.append([prev_button, next_button])

        buttons.append([InlineKeyboardButton("Отмена", callback_data="CANCEL")])

        return InlineKeyboardMarkup(buttons)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
