import bot
import os

cache_dir = ".cache"


def main():
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    token = os.environ.get("TOKEN")
    database_url = os.environ.get("DATABASE_URL")
    fns_bot = bot.Bot(token, database_url)
    fns_bot.run()


if __name__ == "__main__":
    main()
