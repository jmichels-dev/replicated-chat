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
def keepalive_listen(responseStream):
    while True:
        try:
            responseKeepAlive = next(responseStream)
            print("Received heartbeat from primary at", responseKeepAlive.port)
            time.sleep(primary.HEARTBEAT_INTERVAL)
        except Exception as e:
            print("Error in heartbeat from primary:", e)
            return

def send_backup_heartbeats(server_ip, server_port):
    keep_alive_request = chat_pb2.KeepAlive(ip=server_ip, port=server_port)
    while True:
        yield keep_alive_request
        time.sleep(primary.HEARTBEAT_INTERVAL)

def run(server_id, client_ip, client_port):
    # ip and port that this backup will use if it becomes primary
    server_ip = constants.IP_PORT_DICT[server_id][0]
    server_port = constants.IP_PORT_DICT[server_id][1]

    # ip and port that this backup uses as a client to communicate with current primary
    client_ip = client_ip
    client_port = client_port

    with grpc.insecure_channel('{}:{}'.format(client_ip, client_port)) as channel:
        stub = chat_pb2_grpc.ChatStub(channel)
        # print("Congratulations! You have connected to the chat server.\n")

        # Establish bidirectional stream to send and receive keep-alive messages from primary server.
        # requestStream and responseStream are generators of chat_pb2.KeepAlive objects.
        while True:
            requestStream = send_backup_heartbeats(server_ip, server_port)
            responseStream = stub.Heartbeats(requestStream)
            keepalive_listen(responseStream)
            time.sleep(10)
            


if __name__ == '__main__':
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2)")
        exit()
    server_id = int(sys.argv[1])
    run(server_id, constants.IP_PORT_DICT[0][0], constants.IP_PORT_DICT[0][1])
