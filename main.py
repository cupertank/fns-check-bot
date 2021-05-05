import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update

import fns_api

TOKEN = os.getenv("TOKEN")


def start_handler(update: Update, _: CallbackContext):
    update.effective_message.reply_text("Привет!")


def echo_handler(update: Update, _: CallbackContext):
    text = update.effective_message.text
    update.effective_message.reply_text(text)


def main():
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo_handler))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

