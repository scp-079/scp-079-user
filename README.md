# SCP-079-USER

This bot is used to invite and help other bots.

## How to use

- See the [manual](https://telegra.ph/SCP-079-USER-12-04)
- See [this article](https://scp-079.org/user/) to build a bot by yourself
- [README](https://scp-079.org/readme/) of the SCP-079 Project
- Discuss [group](https://t.me/SCP_079_CHAT)

## Requirements

- Python 3.6 or higher.
- pip: `pip install -r requirements.txt` 
- or pip: `pip install -U APScheduler Pillow pyAesCrypt pyrogram pyyaml tgcrypto`

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
