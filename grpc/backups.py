import sys
from _thread import *
import time

import grpc
import chat_pb2
import chat_pb2_grpc
import helpers_grpc
import constants
import primary
import csv

# Listens for messages from primary server's KeepAlive response stream
def keepalive_listen(responseStream, this_backup_id):
    primary_id = -1
    backup_ids = []
    while True:
        try:
            responseKeepAlive = next(responseStream)
            primary_id = responseKeepAlive.primary_id
            backup_ids = responseKeepAlive.backup_ids
            print("Received heartbeat from primary at server_id", primary_id)
            time.sleep(constants.HEARTBEAT_INTERVAL)
        except Exception:
            print("Error in heartbeat from primary.")
            # Failstop by setting lower backup_id as new primary
            print("backup_ids:", backup_ids)
            if len(backup_ids) > 0:
                new_primary_id = min(backup_ids)
                if new_primary_id == this_backup_id:
                    primary.serve(new_primary_id)
                    sys.exit()
                else:
                    run(this_backup_id, new_primary_id)
            else:
                print("backup_ids empty")
            return

def send_backup_heartbeats(this_backup_id):
    keep_alive_request = chat_pb2.KeepAliveRequest(backup_id=this_backup_id)
    while True:
        yield keep_alive_request
        time.sleep(constants.HEARTBEAT_INTERVAL)

def snapshot(backupDict):
    with open('snapshot_' + str(server_id) + '.csv', 'w', newline = '') as testfile:
        rowwriter = csv.writer(testfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        for key in backupDict:
            rowwriter.writerow([key] + backupDict[key])

def loadCommitLog(filename, clientDict):
    try:
        f = open(filename)
        f.close()
    except FileNotFoundError:
        print("no commit log to load")
        return
    print("loading commit log...")
    with open(filename, newline='') as log:
        rowreader = csv.reader(log, delimiter=" ", quotechar="|")
        for row in rowreader:
            op = row[0]
            if op == "ADD":
                helpers_grpc.addUser(row[1], clientDict, {}, False)
            elif op == "LOGIN":
                helpers_grpc.signInExisting(row[1], clientDict, {}, False)
            elif op == "SEND":
                helpers_grpc.sendMsg(row[1], row[3], row[2], clientDict, {}, False)
            elif op == "LIST":
                continue
            elif op == "LOGOUT":
                clientDict[row[1]] = [False, []]
            elif op == "DELETE":
                clientDict.pop(row[1])
    print("commit log fully loaded\n")

def log_ops(opResponseStream, server_id):
    while True:
        nextOp = next(opResponseStream)
        with open('commit_log_' + str(server_id) + '.csv', 'a', newline = '') as commitlog:
            rowwriter = csv.writer(commitlog, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            rowwriter.writerow(nextOp.opLst)

def snapshotThread(backup_clientDict, server_id):
    server_time = time.time()
    while True:
        if (time.time() - server_time > constants.SNAPSHOT_INTERVAL):
            filename = 'commit_log_' + str(server_id) + '.csv'
            loadCommitLog(filename, backup_clientDict)
            helpers_grpc.resetCommitLog(filename)
            snapshot(backup_clientDict)
            server_time = time.time()
        else:
            continue

def run(server_id, client_id):
    # ip and port that this backup will use if it becomes primary
    server_ip = constants.IP_PORT_DICT[server_id][0]
    server_port = constants.IP_PORT_DICT[server_id][1]

    # ip and port that this backup uses as a client to communicate with current primary
    client_ip = constants.IP_PORT_DICT[client_id][0]
    client_port = constants.IP_PORT_DICT[client_id][1]

    with grpc.insecure_channel('{}:{}'.format(client_ip, client_port)) as channel:
        stub = chat_pb2_grpc.ChatStub(channel)
        # print("Congratulations! You have connected to the chat server.\n")

        # Establish response stream to receive operations from the primary
        opResponseStream = stub.BackupOps(chat_pb2.KeepAliveRequest(backup_id=server_id))
        # Concurrently update state in a thread
        backup_clientDict = {}
        start_new_thread(log_ops, (opResponseStream, server_id))
        start_new_thread(snapshotThread, (backup_clientDict, server_id))


        # Establish bidirectional stream to send and receive keep-alive messages from primary server.
        # requestStream and responseStream are generators of chat_pb2.KeepAlive objects.
        while True:
            requestStream = send_backup_heartbeats(server_id)
            responseStream = stub.Heartbeats(requestStream)
            keepalive_listen(responseStream, server_id)
            time.sleep(constants.HEARTBEAT_INTERVAL)
            
if __name__ == '__main__':
    # Checks for correct number of args
    if len(sys.argv) != 3:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2), client_id")
        exit()
    server_id = int(sys.argv[1])
    client_id = int(sys.argv[2])
    run(server_id, client_id)
