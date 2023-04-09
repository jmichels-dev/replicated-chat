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
import constants
import backups

SNAPSHOT_INTERVAL = 5 # seconds
HEARTBEAT_INTERVAL = 5

class ChatServicer(chat_pb2_grpc.ChatServicer):

    def __init__(self, server_id, servicer_lock):
        super(ChatServicer, self).__init__()
        self.server_id = server_id
        # {username : [loggedOnBool, [messageQueue]]}
        self.clientDict = {}
        #self.clientDict = {'test1': [True, ["hello1", "hello2"]]}
        self.backup_servers = set()
        # Thread synchronization for snapshotting
        self.servicer_lock = servicer_lock

    ## Client-server RPCs
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

    ## Replication RPCs
    def Heartbeats(self, backupStream, context):
        print("Before new connection, existing backup servers:", self.backup_servers)
        this_backup_id = -1

        while True:
            try:
                # Recieve heartbeat from backup
                requestKeepAlive = next(backupStream)
                this_backup_id = requestKeepAlive.backup_id
                print("Received heartbeat from backup at server_id", this_backup_id)
                self.backup_server_ids.add(this_backup_id)

                # Send heartbeat to backup
                # with open('snapshot.csv', newline = '') as testfile:
                #     rowreader = csv.reader(testfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
                #     for row in rowreader:
                #         rowwriter.writerow([key] + self.clientDict[key])
                yield chat_pb2.KeepAliveResponse(primary_id=self.server_id, backup_ids=list(self.backup_servers))
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                print("Error in heartbeat from backup:", e)
                self.backup_servers.remove(this_backup_id)
                print("Remaining backup servers:", self.backup_servers)
                break

    ## Non-RPC server-side snapshots
    def Snapshot(self):
        with open('snapshot.csv', 'w', newline = '') as testfile:
            rowwriter = csv.writer(testfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            for key in self.clientDict:
                rowwriter.writerow([key] + self.clientDict[key])

# server_ids 0, 1, 2 signify primary, first backup, and second backup, respectively
def serve(server_id):
    ip = constants.IP_PORT_DICT[server_id][0]
    port = constants.IP_PORT_DICT[server_id][1]

    # Create a lock for thread synchronization
    servicer_lock = threading.Lock()
    servicer = ChatServicer(server_id, servicer_lock)

    loadSnapshot('snapshot.csv', servicer.clientDict)

    # Start snapshot thread for snapshotting state and pass the servicer lock
    snapshot_thread = threading.Thread(target=snapshot, args=(servicer,), daemon=True)
    snapshot_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(servicer, server)
    server.add_insecure_port(f"{ip}:{port}")
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

def loadSnapshot(filename, clientDict):
    try:
        f = open(filename)
        f.close()
    except FileNotFoundError:
        print("no snapshot to load")
        return
    print("loading snapshot...")
    with open(filename, newline='') as snapshot:
        rowreader = csv.reader(snapshot, delimiter=" ", quotechar="|")
        for row in rowreader:
            # False since if server crashes, users will be disconnected regardless of connection status at crash time
            # issues with row[2], treats each char in row[2] as separate message
            clientDict[row[0]] = [False, row[2]]
    print("snapshot loaded: \n")
    print(clientDict)
    
def snapshot(servicer_instance):
    print("inside snapshot")
    server_time = time.time()
    while True:
        if time.time() - server_time > SNAPSHOT_INTERVAL:
            servicer_instance.Snapshot()
            helpers_grpc.resetCommitLog('commit_log.csv')
            server_time = time.time()


if __name__ == '__main__':
    logging.basicConfig()
    serve(0)
    # backups.run(1, 0)
    # backups.run(2, 0)