import os
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram import Update

TOKEN = os.getenv("LOCAL_TOKEN")


def echo_handler(update: Update, _: CallbackContext):
    text = update.effective_message.text
    update.effective_message.reply_text(text)


def main():
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo_handler))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

