# chatroom

## Response

### Success

```json
{
  "_uid": <The id of the request>,
  "success": <true or false>,
  "error": <[Optional] error message>
}
```


# register

**client**

```json
{
  "_uid": <uuid>,
  "path": <client path>
}
```

# RPC

## RPC Request

```json
{
  "_uid": <uuid>,
  "path": <target path>,
  "payload": {
    "id": <RPC request id>,
    "method": <method name>,
    "parameters": <parameters>
  }
}
```

## RPC Response

```json
{
  "_uid": <uuid>,
  "path": <RPC request source path>,
  "payload": {
    "id": <RPC request id>,
    "result": <RPC result>,
    "error": <error message>
  }
}
```
