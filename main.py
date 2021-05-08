import bot
import os


def main():
    token = os.environ.get("TOKEN")
    database_url = os.environ.get("DATABASE_URL")
    fns_bot = bot.Bot(token, database_url)
    fns_bot.run()


if __name__ == "__main__":
    main()
