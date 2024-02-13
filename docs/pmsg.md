# PMSG Command Documentation
## Basic Format

```json
{"cmd": "pmsg", "id": "Webhooks", "val": {"listener": "Any", "cmd": "str", "val": "any"}}
```

Webhooks always sends the provided listener back.

## Commands
### Create
#### Value

```json
{
    "chat": "UUID",
    "pfp": "int"
}
```
#### Response

On Error:

```json

{
    "error": true,
    "status": "int",
    "human": "str"
}
```

OK:

```json

{
    "status": 200,
    "token": "str",
    "id": "uuid",
    "chat": "str"
}
```
###  Delete
#### Value

json

"int"

#### Response
```json
{
    "status": "int",
    "error": "bool"
}
```

### Ban
#### Value

`"str"`

Response

```json

{
    "status": "int",
    "error": "bool"
}
```

## Permisions

All commands have some sort of permision locks.

### create
When creating webhooks for home or livechat you must have `MANAGE_CHATS` (`64`) or your username must be `ShowierData9978`

### Delete 
You must have `MANAGE_CHATS` (`64`) or your username must be `ShowierData9978`

### Ban
You must have `MANAGE_CHATS` (`64`) or your username must be `ShowierData9978`
