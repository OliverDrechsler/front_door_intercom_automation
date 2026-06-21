# Quick Guide: Set Up a Telegram Bot and Private Group

This guide explains how to create a Telegram bot, add it to a private group, and collect the IDs required for `config.yaml`.

## 1. Open the BotFather Chat

Send this command to `@BotFather`:

```text
/start
```

## 2. Create a New Bot

Use:

```text
/newbot
```

Then provide:

- a display name, for example `fdia`
- a bot username ending in `bot`, for example `fdia_bot`

## 3. Create a Private Telegram Group

1. Open the Telegram app.
2. Create a new group.
3. Select the users you want to add.
4. Enter a group name and, optionally, set a group image.
5. Choose an auto-delete interval if desired.
6. Create the group.

## 4. Add the Bot to the Group

1. Search for your bot by its full username.
2. Open the bot profile.
3. Add the bot to the group you created.

## 5. Make Sure the Group Is Private

1. Open the group settings.
2. Open the group type or privacy settings.
3. Confirm that the group is set to `Private`.

## 6. Allow the Bot to Read Group Messages

In the group settings:

1. Open `Administrators`.
2. Add the bot as an administrator if required.
3. Make sure the bot is allowed to read all group messages.

## 7. Enable Group Access in BotFather

In the BotFather chat, run:

```text
/setjoingroups
```

Then select your bot from the list.

## 8. Disable Privacy Mode for the Bot

To allow the bot to receive group messages, run in BotFather:

```text
/setprivacy
```

Then:

1. Select your bot.
2. Choose `Disable`.

## 9. Collect the Telegram IDs for `config.yaml`

You need:

- your user ID
- the group chat ID
- the user IDs of any additional allowed users

### Generate Message Activity

1. Send a message to the Telegram group from your own account.
2. Ask every other authorized user to send a test message as well.

### Query Telegram Updates with `curl`

```bash
curl -X GET "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" | jq -r
```

Example output:

```json
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

### Alternative: Use `httpie`

```bash
http GET https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Use the response to extract:

- `chat.id` for `telegram.chat_number`
- each `from.id` for `telegram.allowed_user_ids`

## 10. Update `config.yaml`

Copy the extracted values into the Telegram section of `config.yaml`.
