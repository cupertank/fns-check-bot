import bot
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

def main():
    TOKEN = os.getenv("MAIN_TOKEN")
    fns_bot = bot.Bot(TOKEN)
    fns_bot.run()


if __name__ == "__main__":
    main()

