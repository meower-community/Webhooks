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
