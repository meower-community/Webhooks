
# Meower Webhooks API
## Introduction

Meower Webhooks allows users to interact with Meower without connecting to the websocket.
Base URL

All API endpoints are relative to the base URL: https://webhooks.meower.org

## Posting a Message
  Allows users to post a message to a specific chat.

  Endpoint: /webhook/<id:str>/<token:str>/<chat_id>/post
  Method: POST
  Request Body:

  ```json

    {
        "name": "string",
        "message": "string"
    }

  ```
  Response: Returns the posted message.

## Retrieving Profile Picture

Retrieves the profile picture of a user.

Endpoint: /profile/<id:str>
Method: GET
Response:

```json

    {
        "error": false,
        "pfp": "string",
        "chat_id": "string",
        "perms":  0
    }
```

## Permissions

To enhance security, all actions related to creating webhooks and moderating are performed through the bot, minimizing the risk of impersonation.
## Error Handling

The API returns appropriate HTTP status codes and error messages to indicate the success or failure of a request.
