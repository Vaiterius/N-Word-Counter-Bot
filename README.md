# The N-word Counter Bot

User said the n-word? GET CAUGHT IN 4K.

User not verified black? MY N**** GET CAUGHT IN 8K.

## Invite Link
https://discord.com/oauth2/authorize?client_id=939483341684605018&permissions=412317244480&scope=bot

## Commands
`n!help` for all command info

## Features
- see individual user n-word count
- a ranked list of server members by n-word count
- "verify" yourself through votes that you are black
- (coming soon?!) give n-word passes (must be black)

## Run this on your machine
### Prerequisites:
- Python 3.10 installed or above
- Create a discord [bot application](https://discord.com/developers/docs/intro)
and fetch the app's token url
- Create a [MongoDB](https://www.mongodb.com/) account and initialize a database cluster,
then retrieve its connection string
### Steps
1. Clone this repository to a place on to your computer
2. Go in the root directory with `cd <this repository's name>`
3. Install the required libraries with `pip install -r requirements.txt`
    - (Recommended) Create a [Python virtual environment](https://docs.python-guide.org/dev/virtualenvs/)
    within the root directory, activate it, _then_ run that command
4. Head into **config.json** and add in your `DISCORD_TOKEN` and `MONGO_URL` strings respectively
5. `cd bot` to go inside the bot folder
6. Run the app with `python bot.py` if on Linux or `py bot.py` if on Windows

## Contact
Reach me on my [discord](https://discord.gg/Q2wjkGvXMk) server for any feedback,
contributions, or issues.

## Other Info
**STATUS**: Finished

Utilizes Discord.py and MongoDB technology.

![Why are you black?](https://i.ytimg.com/vi/mA5C08RWBzs/maxresdefault.jpg)
