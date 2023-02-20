def enqueueMsg(message, recipient, clientDict):
        clientDict[recipient][2].append(message)
        return clientDict[recipient][2][-1]

# Create new user with input username. Returns (errorFlag, errorMsg).
def addUser(username, clientDict):
    # If username is already taken, notify user and request new username
    if username in clientDict:
        return (True, "This username is already taken by another account. Please " +
                      "try again with a different username.\n")
    # If username is valid, create new user in userDict
    clientDict[username] = [True, []]
    return (False, "")

# Sign in to existing account. Returns (errorFlag, message).
def signInExisting(username, clientDict):
    try:
        # From clientDict: [loggedOnBool, messageQueue]
        userAttributes = clientDict[username]
        # If user is already logged in, return error
        if userAttributes[0] == True:
            return (True, "This user is already logged in on another device. Please " +
                          "log out in the other location and try again.\n")
        # Set user as logged in and update socket object
        else:
            userAttributes[0] = True
    except:
        # If account does not exist
        return (True, "No users exist with this username. Please double check that you typed correctly " +
                      "or create a new account with this username.\n")
    unreadsLst = userAttributes[1]
    unreadsNum = str(len(unreadsLst))
    unreads = "You have " + unreadNum + " unread messages:\n\n"
    for msg in unreadsLst:
        unreads += msg + "\n\n"
    # Reset unreads queue
    userAttributes[1] = []
    return (False, unreads)
    
# Returns (errorFlag, payload)
def sendMsg(sender, recipient, message, clientDict):
    # Error handling message 
    error_handle = "Error sending message to " + recipient + ": "

    # Get recipient data
    try:
        recipientAttributes = clientDict[recipient]
        loggedIn = recipientAttributes[1]
    except:
        error_handle += "User does not exist\n"
        return True, error_handle

    # Send message to recipient
    try:
        recipientMsg = "\nFrom " + sender + ": " + message + "\n"
        senderNote = "Message sent.\n"
        # print("payload is: " + payload)
        # If recipient is logged in, send the message
        if loggedIn:
            try:
                recipientSock.sendall(payload.encode())
            except:
                pass
        # If user is logged out, add to their queue
        # NOTE Not sure if this works since no log out function yet to set 
        # bool to false
        else:
            enqueueMsg(payload, recipient, clientDict)
        try:
            clientSock.sendall(senderNote.encode())
        except:
            pass
        return 1
    except:
        recipient.close()
        error_handle += "Recipient connection error"
        try:
            clientSock.sendall(error_handle.encode())
        except:
            pass
        return -3
    
def sendUserlist(message, clientSock, clientDict):
    wildcard = message[1]
    matches, res = list(clientDict.keys()), list(clientDict.keys())

    # return list of all users
    if wildcard == "":
        pass

    # return list of qualifying users
    elif "*" in wildcard:
        starIdx = wildcard.find("*")
        for u in matches:
            if u[0:starIdx] != wildcard[0:starIdx]:
                res.remove(u)
    
    # return list of specific user
    else:
        res = []
        for u in matches:
            if u == wildcard:
                res.append(u)

    # build formatted message for client
    userListMsg = "---------------\n"
    userListMsg += "Matching users: \n"
    for user in res:
        userListMsg += user + "\n"
    userListMsg += "---------------\n"
    try:
        clientSock.sendall(userListMsg.encode())
    except:
        pass
    return res