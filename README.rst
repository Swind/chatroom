turing-chatroom-bus
------------------------------------------------

Response
================================================

Success
################################################

.. code-block:: json

    {
      "_uid": <The id of the request>,
      "success": <true or false>,
      "error": <[Optional] error message>
    }


Register
=================================================

client
#################################################

.. code-block:: json

    {
      "_uid": <uuid>,
      "path": <client path>
    }

RPC
=================================================

RPC Request
#################################################

.. code-block:: json

    {
      "_uid": <uuid>,
      "path": <target path>,
      "payload": {
        "id": <RPC request id>,
        "method": <method name>,
        "parameters": <parameters>
      }
    }

RPC Response
#################################################

.. code-block:: json

    {
      "_uid": <uuid>,
      "path": <RPC request source path>,
      "payload": {
        "id": <RPC request id>,
        "result": <RPC result>,
        "error": <error message>
      }
    }
