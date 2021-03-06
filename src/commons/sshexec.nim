import osproc, strformat, ospaths, os

proc sshExec*(cmd:string): int =
  let p = startProcess("/usr/bin/ssh", args=[cmd], options={poInteractive, poParentStreams})
  result = p.waitForExit()


# proc rsyncUploadFile*(src: string, sshDest:string): int =
#   let cmd = fmt"""rsync -avz ssh --progress {src} {sshDest} """ 
#   echo cmd

# proc rsyncDownloadFile*(sshSrc:string , dest:string) = 
#   let cmd = fmt"""rsync -avzhe ssh --progress {sshSrc} {dest}""" 
#   echo cmd

proc getAgentPublicKeys*(): string = 
  ## Extract Public keys loaded in Agent
  let (output, rc) = execCmdEx("ssh-add -L")
  if rc == 0:
    return $output

proc getPublicSshKeyByName*(keyname="id_rsa"): string =
  ## Get public key content by key name `keyname`
  let path = getHomeDir() / ".ssh" / fmt"{keyname}.pub"
  if fileExists(path):
    result = readFile(path)

proc getPublicSshkeyFromKeyPath*(keypath=getHomeDir()/".ssh"/"id_rsa"):string = 
  ## Get public key content from full path
  if fileExists(keypath):
    result = readFile(keypath & ".pub")

proc rsyncUpload*(src: string, sshDest:string, isDir=false,extraflags=""):string =
  ## Format SCP command to upload `src` to `sshDest`
  ## isDir is false by default (set to true in case of uploading directories)
  var rflag = ""
  if isDir:
    rflag = "-r"

  result = fmt"""scp {extraflags} {rflag} {src} {sshDest} """ 
  echo result 

proc rsyncDownload*(sshSrc:string , dest:string, isDir=false, extraflags=""):string = 
  ## Format SCP command to download `src` to `dest`
  ## isDir is false by default (set to true in case of uploading directories)
  var rflag = ""
  if isDir:
    rflag = "-r"

  result = fmt"""scp {extraflags} {rflag} {sshSrc} {dest}""" 
  echo result

