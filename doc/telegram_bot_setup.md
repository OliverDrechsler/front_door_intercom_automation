# 1 create bot
send massage to @botfather
```
/start
```

# create new bot
```
/newbot
```
answer botname
`olmi_auto`
answer bot name with bot at end
`olmi_auto_bot`

# create a chat group

 create a chat group in telegram
 adn add bot

 # change bot setting

 ```
 /setjoingroups
 ```
 select group from selcections menu/ insert bot name

 # change bot permissions to get group messages

```
/setprivacy
```
* select bot from choosable menu or add bot name
* new select `disable` to get and read all messages

# run python bot command to get chat group details

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

