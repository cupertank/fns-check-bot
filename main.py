import bot
import os

def main():
    TOKEN = os.getenv("MAIN_TOKEN")
    fns_bot = bot.Bot(TOKEN)
    fns_bot.run()


if __name__ == "__main__":
    main()

