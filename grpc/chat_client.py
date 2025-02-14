import logging
import sys
from _thread import *
import time
import csv
import rsa
import grpc
import chat_pb2
import chat_pb2_grpc
import helpers_grpc
import constants

# Loops until a valid sign in. Returns username of signed in user.
def signinLoop(stub):
    existsBool = helpers_grpc.existingOrNew()
    # Try to sign in existing user
    if existsBool:
        print("Please log in with your username")
        username = input("Username: ")
        # Username error check
        if helpers_grpc.isValidUsername(username):
            # Remove whitespace
            username = username.strip().lower()
            unreadsOrError = stub.SignInExisting(chat_pb2.Username(name=username))
            eFlag, msg, encryptedMsgs, senders = unreadsOrError.errorFlag, unreadsOrError.unreads, unreadsOrError.encryptedMsg, unreadsOrError.senders
    # Try to sign in new user
    else:
        print("\nPlease create a new username.")
        username = input("New Username: ")
        # Username error check
        if helpers_grpc.isValidUsername(username):
            # Remove whitespace
            username = username.strip().lower()
            unreadsOrError = stub.AddUser(chat_pb2.Username(name=username))
            eFlag, msg, privkeyList, encryptedMsgs = unreadsOrError.errorFlag, unreadsOrError.unreads, unreadsOrError.privateKey, unreadsOrError.encryptedMsg
            
            # store user's private key 
            csv_file_path = f"{username}_private_key.csv"
            with open(csv_file_path, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                for element in privkeyList:
                    csv_writer.writerow([element])
            

    if eFlag:
        print(msg)
        return signinLoop(stub)
    else:
        print("\nCongratulations! You have successfully logged in to your account.\n")
        # *** TODO: DECRYPT MESSAGES BEFORE PRINTING THEM ***
        csv_file_name = f"{username}_private_key.csv"
        # # File reading and creating a new list
        new_list = []
        with open(csv_file_name, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                new_list.append(row[0])
        new_list = [int(x) for x in new_list]
        privkey = rsa.PrivateKey(new_list[0], new_list[1], new_list[2], new_list[3], new_list[4])
        for i, msg in enumerate(encryptedMsgs):
            decrypted_msg = rsa.decrypt(msg, privkey)
            print(senders[i] + ": " + decrypted_msg.decode("utf8"))
        return username

# Parse input from command line and do the correct action. Loops until logout or delete.
def messageLoop(username, stub):
    command = sys.stdin.readline().strip()
    # User wants to send a message
    if command == 'S' or command == 's':
        while True:
            send_to_user = input("Which user do you want to message? \n Recipient username: ")
            # Username error checks
            if not helpers_grpc.isValidUsername(send_to_user):
                continue
            if send_to_user == username: 
                print("Cannot send message to self.\n")
                continue
            break
        message = input("Type the message you would like to send. \n Message: ")
        # Send sender username, recipient username, and message to the server & store confirmation response
        sender = chat_pb2.Username(name=username)
        recipient = chat_pb2.Username(name=send_to_user)
        payload = chat_pb2.Payload(msg=message)
        senderResponse = stub.Send(chat_pb2.SendRequest(sender=sender, recipient=recipient, sentMsg=payload))
        print(senderResponse.msg)
        print("Command:")
    # User wants to list users
    if command == 'L' or command == 'l':
        wildcard = input("Optional text wildcard: ")
        if wildcard == "":
            wildcard = "*"
        listResponse = stub.List(chat_pb2.Payload(msg=wildcard))
        print("Fetching users... \n")
        print(listResponse.msg)
        print("Command:")
    # User wants to log out
    if command == 'O' or command == 'o':
        logoutResponse = stub.Logout(chat_pb2.Username(name=username))
        print("Logging out...")
        time.sleep(0.2)
        print(logoutResponse.msg)
        time.sleep(0.2)
        return
    # User wants to delete account
    if command == 'D' or command == 'd':
        confirm = False
        confirmInput = input("Are you sure? Deleted accounts are permanently erased, "
                            "and you will be logged off immediately. [Y/N] ")
        while True:
            if confirmInput == 'Y' or confirmInput == 'y':
                confirm = True
                break
            elif confirmInput == 'N' or confirmInput == 'n':
                confirm = False
                break
            else:
                print("Invalid response. Please answer with 'Y' or 'N'.")
        if confirm:
            deleteResponse = stub.Delete(chat_pb2.Username(name=username))
            print("Deleting account... \n")
            time.sleep(0.2)
            print(deleteResponse.msg)
            time.sleep(0.2)
            return
        else:
            print("\nCommand: ")
    messageLoop(username, stub)

# Listens for messages from server's Listen response stream. Closes when user logs out or deletes acct.
def listen_thread(username, responseStream):
    while True:
        try:
            response = next(responseStream)
            csv_file_name = f"{username}_private_key.csv"
            # # File reading and creating a new list
            new_list = []
            with open(csv_file_name, "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    new_list.append(row[0])
            new_list = [int(x) for x in new_list]
            privkey = rsa.PrivateKey(new_list[0], new_list[1], new_list[2], new_list[3], new_list[4])
            try:
                decrypted_msg = rsa.decrypt(response.encryptedMsg, privkey)
            except Exception as error:
                # handle the exception
                print("An exception occurred:", type(error).__name__, "–", error)
            message = response.sender + ": " + decrypted_msg.decode("utf8")
            print(message)
        except:
            return

def run(server_id):
    ip = constants.IP_PORT_DICT[server_id][0]
    port = constants.IP_PORT_DICT[server_id][1]

    with grpc.insecure_channel('{}:{}'.format(ip, port)) as channel:
        stub = chat_pb2_grpc.ChatStub(channel)
        print("Congratulations! You have connected to the chat server.\n")

        while True:
            username = signinLoop(stub)
            # Now, the user is logged in. Notify the user of possible functions
            print("If any messages arrive while you are logged in, they will be immediately displayed.\n")
            print("Use the following commands to interact with the chat app: \n")
            print(" -----------------------------------------------")
            print("|L: List all accounts that exist on this server.|")
            print("|S: Send a message to another user.             |")
            print("|O: Log Out.                                    |")
            print("|D: Delete account.                             |")
            print(" ----------------------------------------------- \n")
            print("Command: ")
            # Establish response stream to receive messages from server.
            # responseStream is a generator of chat_pb2.Payload objects.
            responseStream = stub.Listen(chat_pb2.Username(name=username))
            start_new_thread(listen_thread, (username, responseStream))
            # Wait for input from command line
            messageLoop(username, stub)


if __name__ == '__main__':
    logging.basicConfig()
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id")
        exit()
    server_id = int(sys.argv[1])
    run(server_id)
