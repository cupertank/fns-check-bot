import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import Update
import fns_api


def is_correct_number(tel_num):
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


def is_correct_code(code):
    return True


class Bot:
    current_state = 0
    TOKEN = 0

    def __init__(self):
        self.TOKEN = os.getenv("LOCAL_TOKEN")
        self.current_state = 0

    def start_handler(self, update: Update, _: CallbackContext):
        self.current_state = 1
        update.effective_message.reply_text("Привет! Введите ваш номер телефона: ")
        return self.current_state

    def phone_handler(self, update: Update, _: CallbackContext):
        text = ''
        mess = update.effective_message.text

        if is_correct_number(mess):
            text = 'Введите код из СМС'
            self.current_state = 2
        else:
            text = "Неверный номер телефона, если хотите прекратить работу, введите /cancel"
        update.effective_message.reply_text(text)

        return self.current_state

    def code_handler(self, update: Update, _: CallbackContext):
        text = ''
        mess = update.effective_message.text
        if is_correct_code(mess):
            text = 'Верный код'
            self.current_state = 3
        else:
            text = "Неверный код, если хотите прекратить работу, введите /cancel"
        update.effective_message.reply_text(text)

        return self.current_state

    def cancel_handler(self, update: Update, _: CallbackContext):
        text = 'До новых встреч'
        update.effective_message.reply_text(text)
        return ConversationHandler.END

    def run(self):
        updater = Updater(self.TOKEN)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_handler)],
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.phone_handler)],
                2: [MessageHandler(Filters.text & ~Filters.command, self.code_handler)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_handler)],
        )

        updater.dispatcher.add_handler(conv_handler)
        updater.start_polling()
        updater.idle()
