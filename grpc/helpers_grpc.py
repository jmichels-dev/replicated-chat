import csv

## Used in client
def isValidUsername(username):
    usernameWords = username.split()
    # If user inputs empty string, whitespace, or multiple words as username
    if len(usernameWords) != 1:
        print("Usernames can only be one word containing letters, numbers, and special characters. " 
              "Please try again with a different username.\n")
        return False
    return True

def existingOrNew():
    print("Sign In: ")
    # Determine if user has account or needs to sign up
    existsInput = input("Do you already have an account? [Y/N] ")
    if existsInput == 'Y' or existsInput == 'y':
        return True
    elif existsInput == 'N' or existsInput == 'n':
        return False
    else:
        print("Invalid response. Please answer with 'Y' or 'N'.")
        return existingOrNew()

## Used in server
# Create new user with input username. Returns (errorFlag, errorMsg).
def addUser(username, clientDict, newOps, first, publicKey):
    # If username is already taken, notify user and request new username
    if username in clientDict:
        return (True, "This username is already taken by another account. Please " +
                      "try again with a different username.\n")
    # If username is valid, create new user in userDict
    clientDict[username] = [True, [], publicKey]
    operation = ['ADD', str(username), str(publicKey.n), str(publicKey.e)]
    if first:
        backupOp(operation, newOps)
        logOp(operation)
    return (False, "")

# Sign in to existing account. Returns (errorFlag, message).
def signInExisting(username, clientDict, newOps, first):
    try:
        # From clientDict: [loggedOnBool, messageQueue]
        userAttributes = clientDict[username]
        # If user is already logged in, return error
        if userAttributes[0] == True:
            return (True, "This user is already logged in on another device. Please " +
                          "log out in the other location and try again.\n", [], [])
        # Set user as logged in and update socket object
        else:
            userAttributes[0] = True
            operation = ["LOGIN", str(username)]
            if first:
                backupOp(operation, newOps)
                logOp(operation)
    except:
        # If account does not exist
        return (True, "No users exist with this username. Please double check that you typed correctly " +
                      "or create a new account with this username.\n", [], [])
    unreadsLst = userAttributes[1]
    senders = [msg[0] for msg in unreadsLst]
    encryptedLst = [msg[1] for msg in unreadsLst]
    unreadsNum = str(len(unreadsLst))
    unreads = "You have " + unreadsNum + " unread messages:\n\n"
    # *** TODO: ADD ENCRYPTED MESSAGES TO UNREADS BEFORE SENDING TO CLIENT ***
    # for msg in unreadsLst:
    #     unreads += msg + "\n\n"
    # Reset unreads queue
    userAttributes[1] = []
    return (False, unreads, encryptedLst, senders)
    
# Returns error message or sender confirmation & enqueues message for recipient
def sendMsg(sender, recipient, message, clientDict, newOps, first):
    # Error handling message 
    error_handle = "Error sending message to " + recipient + ": "

    # Get recipient data
    try:
        recipientAttributes = clientDict[recipient]
        loggedIn = recipientAttributes[1]
    except:
        error_handle += "User does not exist\n"
        return error_handle

    # Send message to recipient
    try:
        recipientMsg = [sender, message]
        senderNote = "Message sent.\n"
        # print("payload is: " + payload)

        # Enqueue the message
        clientDict[recipient][1].append(recipientMsg)
        operation = ["SEND", sender, message, recipient]
        if first:
            backupOp(operation, newOps)
            logOp(operation)
        return senderNote
    except:
        error_handle += "Recipient connection error"
        return error_handle
    
def sendUserlist(wildcard, clientDict, newOps, first):
    allUsers, matches = list(clientDict.keys()), list(clientDict.keys())
    operation = ["LIST", wildcard]
    if first:
        backupOp(operation, newOps)
        logOp(operation)

    # return list of qualifying users
    if "*" in wildcard:
        starIdx = wildcard.find("*")
        for u in allUsers:
            # Chars before star (if any) must match exactly
            if u[0:starIdx] != wildcard[0:starIdx]:
                matches.remove(u)
                continue
            # Any number of chars match star. 
            # Chars after star must match exactly.
            if starIdx < len(wildcard) - 1:
                afterStar = wildcard[starIdx + 1:]
                if len(u) < len(afterStar):
                    matches.remove(u)
                else:
                    uAfterStar = u[-len(afterStar):]
                    if afterStar != uAfterStar:
                        matches.remove(u)
        
    # return list of specific user
    else:
        matches = []
        for u in allUsers:
            if u == wildcard:
                matches.append(u)

    # build formatted message for client
    userListMsg = "---------------\n"
    userListMsg += "Matching users: \n"
    for user in matches:
        userListMsg += user + "\n"
    userListMsg += "---------------\n"
    return userListMsg

def logOp(op):
    if SERVERNO != -1:
        with open('commit_log_' + str(SERVERNO) + '.csv', 'a', newline = '') as commitlog:
            rowwriter = csv.writer(commitlog, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            rowwriter.writerow(op)
    else:
        print("server number not found")

def backupOp(op, newOps):
    for key in newOps:
        newOps[key].append(op)

def getServerNo(serverNo):
    global SERVERNO
    SERVERNO = serverNo

def resetCommitLog(filename):
    f = open(filename, "w+")
    f.close()