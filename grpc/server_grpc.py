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

class ChatServicer(chat_pb2_grpc.ChatServicer):

    def __init__(self, servicer_lock):
        super(ChatServicer, self).__init__()
        # {username : [loggedOnBool, [messageQueue]]}
        #self.clientDict = {}
        self.clientDict = {'test1': [True, ["hello1", "hello2"]]}
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


def serve():
    ip = '10.148.151.210'
    port = '8080'

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
            SERVER_TIME = time.time()


if __name__ == '__main__':
    logging.basicConfig()
    serve()