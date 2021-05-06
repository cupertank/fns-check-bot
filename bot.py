from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import Update
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
            # local without postgres
            self.dao = db.Dao(None)
        else:
            # heroku deploy
            conn = psycopg2.connect(database_url)
            self.dao = db.Dao(conn)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_handler)],
            states={
                States.WAITING_PHONE: [MessageHandler(Filters.text & ~Filters.command, self.phone_handler)],
                States.WAITING_CODE: [MessageHandler(Filters.text & ~Filters.command, self.code_handler)],
                States.WAITING_NAMES: [MessageHandler(Filters.text & ~Filters.command, self.guest_name_handler)],
                States.WAITING_TICKET: [MessageHandler(Filters.photo, self.picture_handler)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler)],
        )

        self.updater.dispatcher.add_handler(conv_handler)

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
            context.user_data["id"] = fns_api.send_login_code(number, code)[0]
            context.user_data["refresh"] = fns_api.send_login_code(number, code)[1]
            return True
        except InvalidSmsCodeException:
            return False

    def start_handler(self, update: Update, context: CallbackContext):
        if "refresh" in context.user_data:
            context.user_data["id"] = fns_api.fns_api.refresh_session(context.user_data["refresh"])
            update.effective_message.reply_text("Привет! Введите имена пользователей(для каждого пользователя введите имя на новой строчке):")
            return States.WAITING_NAMES

        update.effective_message.reply_text("Привет! Введите ваш номер телефона: ")
        return States.WAITING_PHONE

    def phone_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text

        if self.__is_correct_number(mess):
            update.effective_message.reply_text('Введите код из СМС')
            if mess[0] == '7' or mess[0] == '8':
                mess = '+7' + mess[1:]
            context.user_data['phone'] = mess
            fns_api.send_login_sms(context.user_data['phone'])
            return States.WAITING_CODE

        update.effective_message.reply_text("Неверный номер телефона, если хотите прекратить работу, введите /cancel")
        return States.WAITING_PHONE

    def code_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text

        if self.__is_correct_code(mess, context.user_data['phone'], context):
            update.effective_message.reply_text('Верный код. Введите имена пользователей(для каждого пользователя введите имя на новой строчке):')
            return States.WAITING_NAMES

        update.effective_message.reply_text("Неверный код, если хотите прекратить работу, введите /cancel")
        return States.WAITING_CODE

    def cancel_handler(self, update: Update, _: CallbackContext):
        update.effective_message.reply_text('До новых встреч')
        return ConversationHandler.END

    def guest_name_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text
        context.user_data["names"] = mess.splitlines()
        update.effective_message.reply_text('Пришлите фотографию QR-кода с чека:')
        return States.WAITING_TICKET

    def picture_handler(self, update: Update, context: CallbackContext):
        sess_id = context.user_data['id']
        photo_file = update.message.photo[-1].get_file().download_as_bytearray()
        if readerQR.readQR(photo_file)[1]:
             print(get_receipt(readerQR.readQR(photo_file)[0], sess_id))
        else:
            update.effective_message.reply_text("QR не читаем или его нет")
            return States.WAITING_TICKET

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
