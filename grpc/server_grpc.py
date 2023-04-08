import sys
from concurrent import futures
import logging
import time
import threading
import csv

import grpc
import chat_pb2
import chat_pb2_grpc
import helpers_grpc


SNAPSHOT_INTERVAL = 5 # seconds
# Primary server is IP_PORT_DICT[0], backup servers are IP_PORT_DICT[1] and IP_PORT_DICT[2]
IP0 = '10.250.64.41'
IP1 = '10.250.226.222'
IP_PORT_DICT = {0 : [IP0, '8080'], 1 : [IP0, '8081'], 2 : [IP1, '8082']}

class ChatServicer(chat_pb2_grpc.ChatServicer):

    def __init__(self, servicer_lock):
        super(ChatServicer, self).__init__()
        # {username : [loggedOnBool, [messageQueue]]}
        self.clientDict = {}
        #self.clientDict = {'test1': [True, ["hello1", "hello2"]]}
        # Thread synchronization for snapshotting
        self.servicer_lock = servicer_lock

    def SignInExisting(self, username, context):
        eFlag, msg = helpers_grpc.signInExisting(username.name, self.clientDict)
        return chat_pb2.Unreads(errorFlag=eFlag, unreads=msg)
    
    def AddUser(self, username, context):
        eFlag, msg = helpers_grpc.addUser(username.name, self.clientDict)
        return chat_pb2.Unreads(errorFlag=eFlag, unreads=msg)

    def Send(self, sendRequest, context):
        response = helpers_grpc.sendMsg(sendRequest.sender.name, sendRequest.recipient.name, 
                                        sendRequest.sentMsg.msg, self.clientDict)
        return chat_pb2.Payload(msg=response)

    # usernameStream only comes from logged-in user
    def Listen(self, username, context):
        while True:
            # If any messages are queued
            if len(self.clientDict[username.name][1]) > 0:
                # Yield first message
                yield chat_pb2.Payload(msg=self.clientDict[username.name][1].pop(0))
            # Stop stream if user logs out
            if self.clientDict[username.name][0] == False:
                break

    def List(self, wildcard, context):
        payload = helpers_grpc.sendUserlist(wildcard.msg, self.clientDict)
        return chat_pb2.Payload(msg=payload)

    def Logout(self, username, context):
        self.clientDict[username.name][0] = False
        return chat_pb2.Payload(msg="Goodbye!\n")

    def Delete(self, username, context):
        self.clientDict.pop(username.name)
        return chat_pb2.Payload(msg="Goodbye!\n")
    
    # Non-RPC server-side snapshots
    def Snapshot(self):
        with open('test.csv', 'w', newline = '') as testfile:
            rowwriter = csv.writer(testfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            for key in self.clientDict:
                rowwriter.writerow([key] + self.clientDict[key])

# server_ids 0, 1, 2 signify primary, first backup, and second backup, respectively
def serve(server_id):
    ip = IP_PORT_DICT[server_id][0]
    port = IP_PORT_DICT[server_id][1]

    # Create a lock for thread synchronization
    servicer_lock = threading.Lock()
    servicer = ChatServicer(servicer_lock)

    # Start snapshot thread for snapshotting state and pass the servicer lock
    snapshot_thread = threading.Thread(target=snapshot, args=(servicer,), daemon=True)
    snapshot_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(servicer, server)
    server.add_insecure_port(f"{ip}:{port}")
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()
    
def snapshot(servicer_instance):
    print("inside snapshot")
    SERVER_TIME = time.time()
    while True:
        if time.time() - SERVER_TIME > SNAPSHOT_INTERVAL:
            servicer_instance.Snapshot()
            helpers_grpc.resetCommitLog()
            SERVER_TIME = time.time()


if __name__ == '__main__':
    logging.basicConfig()
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2)")
        exit()
    server_id = int(sys.argv[1])
    serve(server_id)