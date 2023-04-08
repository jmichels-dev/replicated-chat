import sys
from _thread import *
import time

import grpc
import chat_pb2
import chat_pb2_grpc
import helpers_grpc
import constants

# Listens for messages from server's Listen response stream. Closes when user logs out or deletes acct.
def listen_thread(username, stub, responseStream):
    while True:
        try:
            response = next(responseStream)
            print(response.msg)
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
            start_new_thread(listen_thread, (username, stub, responseStream))
            # Wait for input from command line
            messageLoop(username, stub)


if __name__ == '__main__':
    logging.basicConfig()
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2)")
        exit()
    server_id = int(sys.argv[1])
    run(server_id)
