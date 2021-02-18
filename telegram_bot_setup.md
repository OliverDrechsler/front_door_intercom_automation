# Quick Guide to setup a telegram bot and privat group chat

- [Quick Guide to setup a telegram bot and privat group chat](#quick-guide-to-setup-a-telegram-bot-and-privat-group-chat)
  - [1. Open bothfather channel](#1-open-bothfather-channel)
  - [2. Create new bot](#2-create-new-bot)
  - [3. Create a chat group](#3-create-a-chat-group)
  - [4. Change bot setting](#4-change-bot-setting)
  - [4. Change bot permissions to get group messages](#4-change-bot-permissions-to-get-group-messages)
  - [5. Run python bot command to get chat group details](#5-run-python-bot-command-to-get-chat-group-details)

## 1. Open bothfather channel
send massage to @botfather
```
/start
```

## 2. Create new bot
```
/newbot
```
answer with botname
`fdia`
answer bot name with bot at end
`fdia_bot`

## 3. Create a chat group

 create a chat group in telegram and add new bot

 ## 4. Change bot setting

 ```
 /setjoingroups
 ```
 select group from selcections menu/ insert bot name

 ## 4. Change bot permissions to get group messages

```
/setprivacy
```
* select bot from choosable menu or add bot name
* new select `disable` to get and read all messages

## 5. Run python bot command to get chat group details

```python
import sys
import time
import telepot
from telepot.loop import MessageLoop

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    if content_type == 'text':
        bot.sendMessage(chat_id, msg['text'])

TOKEN = sys.argv[1]  # get token from command-line

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()
print ('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)
```

