import  redisclient, redisparser
import os, strutils, strformat, osproc, tables, uri
import uuid, json, tables, net, strformat, asyncdispatch, asyncnet, strutils, ospaths



proc flagifyId*(id: string): string =
  result = fmt"result:{id}:flag" 

proc resultifyId*(id: string): string = 
  result = fmt"result:{id}" 

proc streamId*(id: string): string = 
  result = fmt"stream:{id}" 

proc newUUID*(): string = 
  var cmduid: Tuuid
  uuid_generate_random(cmduid)
  result = cmduid.to_hex

proc getResponseString*(id: string, con: Redis|AsyncRedis, timeout=10): Future[string] {.multisync.} = 
  let exists = $(await con.execCommand("EXISTS", @[flagifyId(id)]))
  if exists == "1":
    let reskey = resultifyId(id)
    result = $(await con.execCommand("BRPOPLPUSH", @[reskey, reskey, $timeout]))


proc zosSend*(payload: JsonNode, bash=false, host="localhost", port=4444, timeout=5, debug=false): string =
  let cmdid = payload["id"].getStr()

  if debug == true:
    echo "payload" & $payload
  
  let con = open(host, port.Port, true)
  let flag = flagifyId(cmdid)
  let reskey = resultifyId(cmdid) 

  var cmdres: RedisValue
  cmdres = con.execCommand("RPUSH", @["core:default", $payload])
  if debug:
    echo $cmdres
  cmdres = con.execCommand("BRPOPLPUSH", @[flag, flag, $timeout])
  if debug:
    echo $cmdres

  let parsed = parseJson(getResponseString(cmdid, con))
  result = parsed.pretty(2)

  let response_state = $parsed["state"].getStr()
  if response_state != "SUCCESS":
    echo fmt"FAILED TO EXECUTE with error {parsed}"
    echo result
  else:
    if bash == true:
      if parsed["code"].getInt() == 0:
        echo parsed["streams"][0].getStr() # stdout
      else:
        echo parsed["streams"][1].getStr() # stderr
    else:
      result = parsed["data"].getStr().parseJson().pretty(2)
    


proc zosBash*(command: string="hostname", host: string="localhost", port=4444, timeout:int=5, debug=false): string =
  let cmdid = newUUID()
  let payload = %*{
    "id": cmdid,
    "command": "bash",
    "queue": nil,
    "arguments": %*{"script":command, "stdin":""},
    "max_time": nil,
    "stream": false,
    "tags": nil
  }
  return zosSend(payload, true, host, port, timeout, debug)


proc zosCoreWithJsonNode*(command: string="core.ping", payloadNode:JsonNode=nil, host: string="localhost", port=4444, timeout:int=5, debug=false): string =

  let cmdid = newUUID()
  let payload = %*{
    "id": cmdid,
    "command": command,
    "arguments": nil,
    "queue": nil,
    "max_time": nil,
    "stream": false,
    "tags": nil
  }
  if payloadNode != nil:
    payload["arguments"] = payloadNode
  return zosSend(payload, false, host, port, timeout, debug)
    

proc zosCore*(command: string="core.ping", arguments="", host: string="localhost", port=4444, timeout:int=5, debug=false): string =
  var payloadNode: JsonNode = nil
  if not arguments.isNilOrEmpty():
    payloadNode = parseJson(arguments) 
  return zosCoreWithJsonNode(command, payloadNode, host, port, timeout, debug)

    