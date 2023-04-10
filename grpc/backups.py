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
            time.sleep(primary.HEARTBEAT_INTERVAL)
        except Exception as e:
            print("Error in heartbeat from primary:", e)
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
        time.sleep(primary.HEARTBEAT_INTERVAL)

def log_ops(opResponseStream, backup_clientDict, server_id):
    while True:
        try:
            nextOp = next(opResponseStream)
            with open('commit_log_' + str(server_id) + '.csv', 'a', newline = '') as commitlog:
                rowwriter = csv.writer(commitlog, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
                rowwriter.writerow(nextOp)
        except:
            pass

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
        opResponseStream = stub.BackupOp(chat_pb2.KeepAliveRequest(backup_id=server_id))
        # Concurrently update state in a thread
        backup_clientDict = {}
        start_new_thread(log_ops, (opResponseStream, backup_clientDict, server_id))

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
