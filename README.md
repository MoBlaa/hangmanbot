# Hangman Discord Bot

The HangmanBot is hosted by the developer himself on a raspberrypi. So no guarantees on uptimes. If you want to control it by yourself create a Bot account and follow the [Hosting it yourself](#hosting-it-yourself) section.

If you just want to invite the bot hosted by the developer to your server: [Here you go](https://discord.com/api/oauth2/authorize?client_id=827469612329074754&permissions=10240&scope=bot).

## Hosting it yourself

__Requirements:__ The Bot has to be added to your Server/Group and requires to have the permission to send and delete messages (Send + Edit Messages).

Clone the repository, follow instructions in [Environment Setup](#environment-setup) and start the Bot with either `python3 hangmanbot/__main__.py` or `make run`.

You can also build an executable with `make package` (python3 and pip required) and distribute the executable file `dist/hangmanbot` (Python3 is still required to run this file).

### Environment setup

Create `.env` file with the following content in the execution directory:

```env
TOKEN=<your bot login token>
```

or set the environment variable `TOKEN=<your bot login token>` on the machine the bot will run on.

## Commands

- `!start_hangman ||<phrase>||` or `!s ||<phrase>||`: Start the game with the phrase inside the spoiler. The phrase has to be __at least 3 characters long__. This message will be deleted so be sure to configure your roles right.
- `!guess <character | word>` or `!g <character | word>`: Guess a single character or the whole word.
- `!remove` or `!rm`: Admin of the server or author of the game can delete the current game.
- `!cooldown <command>` or `!cd <command>` (Admin): Get the cooldown for the given command. `<command>` can either be a alias or the full command name.
- `!cooldown-edit <command> <seconds>` or `!cd-e <command> <seconds>` (Admin): Set the cooldown for the given command to given seconds. `<command>` can either be a alias or the full command name.

## Features

- Play Hangman (obviously)
- Cooldowns (configurable by Administrator) for:
    - Guessing
    - Author of previous game starting a new game
    - Removing the current game after at least one player has started guessing. Removing is still possible after creation and before first player has started guessing.
