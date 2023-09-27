# The N-word Counter Bot

[![Python application](https://github.com/Vaiterius/N-Word-Counter-Bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/Vaiterius/N-Word-Counter-Bot/actions/workflows/python-app.yml)

User said the n-word? CAUGHT IN 4K 🤨📸

## Invite Link

[Here!](https://discord.com/oauth2/authorize?client_id=939483341684605018&permissions=412317244480&scope=bot)

## Commands

All commands have now been replaced with slash commands! Type `/` to see all the commands.

## Features

-   catches any mention of the n-word with a reply
-   view individual user n-word count
-   view server n-word rankings
-   view global n-word rankings
-   "verify" yourself through votes
-   (coming soon?!) give n-word passes

## Do you want to run this on your machine?

### Prerequisites:

-   Python 3.10 installed or above
-   Create a discord [bot application](https://discord.com/developers/docs/intro)
    and fetch the app's token url
-   on the discord bot developer portal, enable SERVER MEMBERS INTENT and MESSAGE CONTENT INTENT
-   Create a [MongoDB](https://www.mongodb.com/) account and initialize a database cluster,
    then retrieve its connection string

### Steps

1. Clone this repository to a place on to your computer
2. Go in the root directory with `cd <this repository's name>`
3. Install the required libraries with `pip install -r requirements.txt`
    - (Recommended) Create a [Python virtual environment](https://docs.python-guide.org/dev/virtualenvs/)
      within the root directory, activate it, _then_ run that command
4. Head into **config.json** and add in your `DISCORD_TOKEN` and `MONGO_URL` strings respectively, within the double quotes
5. `cd bot` to go inside the bot folder
6. Run the app with `python bot.py` if on Linux or `py bot.py` if on Windows

## Contact

Reach me on my [discord](https://discord.gg/Q2wjkGvXMk) server for any feedback,
contributions, or issues.

## Other Info

**STATUS**: Finished but continuously maintained

Utilizes Discord.py and MongoDB technology. Hosted on Fly.io.

![Why are you black?](https://i.ytimg.com/vi/mA5C08RWBzs/maxresdefault.jpg)
