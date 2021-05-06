from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import Update
import fns_api


class Bot:
    def __init__(self, token):
        self.updater = Updater(token)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_handler)],
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.phone_handler)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.code_handler)],
                3: [MessageHandler(Filters.text & ~Filters.command, self.guest_name_handler)]
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

    def __is_correct_code(self, code):
        return True

    def start_handler(self, update: Update, _: CallbackContext):
        update.effective_message.reply_text("Привет! Введите ваш номер телефона: ")
        return 1

    def phone_handler(self, update: Update, _: CallbackContext):
        mess = update.effective_message.text

        if self.__is_correct_number(mess):
            update.effective_message.reply_text('Введите код из СМС')
            return 2

        update.effective_message.reply_text("Неверный номер телефона, если хотите прекратить работу, введите /cancel")

        return 1

    def code_handler(self, update: Update, _: CallbackContext):
        mess = update.effective_message.text

        if self.__is_correct_code(mess):
            update.effective_message.reply_text('Верный код. Введите имена пользователей(для каждого пользователя введите имя на новой строчке):')
            return 3

        update.effective_message.reply_text("Неверный код, если хотите прекратить работу, введите /cancel")
        return 2

    def cancel_handler(self, update: Update, _: CallbackContext):
        update.effective_message.reply_text('До новых встреч')
        return ConversationHandler.END

    def guest_name_handler(self, update: Update, context: CallbackContext):
        mess = update.effective_message.text
        context.user_data["names"] = mess.splitlines()
        update.effective_message.reply_text('Пришлите фотографию QR-кода с чека:')
        return 4

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
