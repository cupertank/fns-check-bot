import bot
import os

def main():
    TOKEN = os.getenv("LOCAL_TOKEN")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    fns_bot = bot.Bot(TOKEN, DATABASE_URL)
    fns_bot.run()


if __name__ == "__main__":
    main()

