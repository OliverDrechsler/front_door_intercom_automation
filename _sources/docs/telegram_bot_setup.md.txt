# Quick Guide to setup a telegram bot and privat group chat

- [Quick Guide to setup a telegram bot and privat group chat](#quick-guide-to-setup-a-telegram-bot-and-privat-group-chat)
  - [1. Open bothfather channel](#1-open-bothfather-channel)
  - [2. Create new bot](#2-create-new-bot)
  - [3. Create a privat telegram chat group](#3-create-a-privat-telegram-chat-group)
  - [4. Change bot setting  in the BotFather Chat](#4-change-bot-setting--in-the-botfather-chat)
  - [5. Change bot permissions to get group messages in the BotFather Chat](#5-change-bot-permissions-to-get-group-messages-in-the-botfather-chat)
  - [6. Run python bot command to get chat group details for configuration config.yaml](#6-run-python-bot-command-to-get-chat-group-details-for-configuration-configyaml)

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

## 3. Create a privat telegram chat group

1. Open Telegram App:

Launch the Telegram app on your mobile device or desktop.

2. Start a New Group:

Tap the pencil icon, then select "New Group."

3. Select Members:

Choose the users you want to add to the group. You can search for their usernames or select them from your contacts.

4. Name the Group:

After selecting the members, tap the arrow (or "Next") and enter a name for your group. Optionally, you can set a group photo.

5. Select Auto-Message-Deletion

Select an auto deletion interval of your choice in the dropdown box.

6. Create the Group:

Tap the checkmark (or "Create") to finalize the creation of the group.



7. Find the Bot

Search for the bot you want to add to the group by typing its complete username in the search bar.

8. Add the Bot

Open the bot's chat, tap the bot's profile picture, and select "Add to Group.".  
Then choose the group you just created.

9. Open Group Settings

Go to the group chat, tap the group name at the top to open the group’s info page.

10. Edit Group Permissions

Tap the pencil icon (or "Edit") to access the group settings.

11. Set Privacy

In the "Group Type" section, ensure the group is set to "Private." .  
This means only invited members can join the group.

12. Enable Bot to Read Messages
For the bot to read messages, it needs the appropriate permissions

Admin Rights:
Go to the group’s info page, select "Administrators," and add the bot as an admin. When setting the bot's admin permissions, ensure it has the "Read All Group Messages" permission.

## 4. Change bot setting  in the BotFather Chat

 ```
 /setjoingroups
 ```
 select group from selcections menu/ insert bot name

 ## 5. Change bot permissions to get group messages in the BotFather Chat

```
/setprivacy
```
* select bot from choosable menu or add bot name
* new select `disable` to get and read all messages

## 6. Run python bot command to get chat group details for configuration config.yaml

Now it time to get your telegram 
- user id
- chat group id
- and if more than one user is in the group their user ids

Send from your mobile phone a message to the telegram chat group where your bot is assigned in.
Now it time to ask other telegram chat group members to also send a test message to the group so that their from id's are also visible in the below commands.  
  
Now run shell command:
```
curl -X GET "https://api.telegram.org/bot<YOUR_BOT_TOKEN code>/getUpdates" |jq -r
```
example output:
```
{
  "ok": true,
  "result": [
    {
      "update_id": 839666728,
      "message": {
        "message_id": 1994,
        "from": {
          "id": 123456789,
          "is_bot": false,
          "first_name": "MyFirstName",
          "username": "MyFullName",
          "language_code": "de"
        },
        "chat": {
          "id": -987654321,
          "title": "a_group_title",
          "type": "group",
          "all_members_are_administrators": true
        },
        "date": 1721202785,
        "text": "test text"
      }
    },
        {
      "update_id": 3456789012,
      "message": {
        "message_id": 1995,
        "from": {
          "id": 123450000,
          "is_bot": false,
          "first_name": "OtherUserFirstName",
          "username": "OtherUserFullName",
          "language_code": "de"
        },
        "chat": {
          "id": -987654321,
          "title": "a_group_title",
          "type": "group",
          "all_members_are_administrators": true
        },
        "date": 1721202785,
        "text": "other user test text"
      }
    }
  ]
}
```

or if you prefer httpie command instead shell curl run this:
```
http GET https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
example output:
```
HTTP/1.1 200 OK
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Origin: *
Access-Control-Expose-Headers: Content-Length,Content-Type,Date,Server,Connection
Connection: keep-alive
Content-Length: 998
Content-Type: application/json
Date: Wed, 17 Jul 2024 08:03:52 GMT
Server: nginx/1.18.0
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

{
  "ok": true,
  "result": [
    {
      "update_id": 839666728,
      "message": {
        "message_id": 1994,
        "from": {
          "id": 123456789,
          "is_bot": false,
          "first_name": "MyFirstName",
          "username": "MyFullName",
          "language_code": "de"
        },
        "chat": {
          "id": -987654321,
          "title": "a_group_title",
          "type": "group",
          "all_members_are_administrators": true
        },
        "date": 1721202785,
        "text": "test text"
      }
    },
        {
      "update_id": 3456789012,
      "message": {
        "message_id": 1995,
        "from": {
          "id": 123450000,
          "is_bot": false,
          "first_name": "OtherUserFirstName",
          "username": "OtherUserFullName",
          "language_code": "de"
        },
        "chat": {
          "id": -987654321,
          "title": "a_group_title",
          "type": "group",
          "all_members_are_administrators": true
        },
        "date": 1721202785,
        "text": "other user test text"
      }
    }
  ]
}
```


Now search in the output for 
- json tree `message.from.id`  which is equal to the user id stored in `config.yaml` under
  section `telegram` `allowed_user_ids` as list string values.
- json tree `message.chat.id` which is the telegram chat group id
  which you want to allow the bot to react on. A group chat id starts always with a `-`.  
  Store this chat id in  `config.yaml` under
  section `telegram` `chat_number` as string value.
