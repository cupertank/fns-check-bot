import bot
import os

def main():
    TOKEN = os.environ.get("TOKEN")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    fns_bot = bot.Bot(TOKEN, DATABASE_URL)
    fns_bot.run()


if __name__ == "__main__":
    main()

