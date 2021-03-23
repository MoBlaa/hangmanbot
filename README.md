# Hangman Discord Bot

__Requirements:__ The Bot has to be added to your Server/Group and requires to have the permission to delete messages (Edit Messages).

Create `.env` file with the following content in the root of the project:

```env
TOKEN=<your bot login token>
USERNAME=<username of the bot>
```

and start the Bot with either `python3 hangmanbot.py` or `make run`.

## Commands

- `!start_hangman ||<word>||`: Start the game with the word inside the spoiler. The word has to be __at least 3 characters long__. This message will be deleted so be sure to configure your roles right.
- `!guess <character | word>`: Guess a single character or the whole word.