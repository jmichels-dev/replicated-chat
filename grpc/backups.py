import sys
from _thread import *
import time

import grpc
import chat_pb2
import chat_pb2_grpc
import helpers_grpc
import constants
import primary

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
            new_primary_id = min(backup_ids)
            if new_primary_id == this_backup_id:
                primary.serve(new_primary_id)
                sys.exit()
            return

def send_backup_heartbeats(this_backup_id):
    keep_alive_request = chat_pb2.KeepAliveRequest(backup_id=this_backup_id)
    while True:
        yield keep_alive_request
        time.sleep(primary.HEARTBEAT_INTERVAL)

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

        # Establish bidirectional stream to send and receive keep-alive messages from primary server.
        # requestStream and responseStream are generators of chat_pb2.KeepAlive objects.
        while True:
            requestStream = send_backup_heartbeats(server_id)
            responseStream = stub.Heartbeats(requestStream)
            keepalive_listen(responseStream, server_id)
            time.sleep(10)
            


if __name__ == '__main__':
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2)")
        exit()
    server_id = int(sys.argv[1])
    run(server_id, constants.IP_PORT_DICT[0][0], constants.IP_PORT_DICT[0][1])
