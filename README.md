# SCP-079-USER

This bot is used to invite and help other bots.

## How to use

- See the [manual](https://telegra.ph/SCP-079-USER-12-04)
- See [this article](https://scp-079.org/user/) to build a bot by yourself
- [README](https://github.com/scp-079/scp-079-readme) of the SCP-079 Project
- Discuss [group](https://t.me/SCP_079_CHAT)

## To Do List

- [x] Help to delete messages or ban user
- [x] Print message function
- [x] Mark message and mention as read
- [x] Share message preview

## Requirements

- Python 3.6 or higher.
- pip: `pip install -r requirements.txt` or `pip install -U APScheduler Pillow pyAesCrypt pyrogram[fast]`

## Files

- plugins
    - functions
        - `channel.py` : Functions about channel
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `receive.py` : Receive data from exchange channel
        - `telegram.py` : Some telegram functions
        - `tests.py` : Some test functions
        - `timers.py` : Timer functions
        - `user.py` : Functions about user and channel object
    - handlers
        - `command` : Handle commands
        - `message.py`: Handle messages
    - `glovar.py` : Global variables
- `.gitignore` : Ignore
- `config.ini.example` -> `config.ini` : Configuration
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribute

Welcome to make this project even better. You can submit merge requests, or report issues.

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
