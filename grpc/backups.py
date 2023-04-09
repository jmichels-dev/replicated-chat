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
def keepalive_listen(ip, port, responseStream):
    while True:
        try:
            response = next(responseStream)
            time.sleep(primary.HEARTBEAT_INTERVAL)
        except Exception as e:
            print("Error in heartbeat from primary:", e)
            return

def send_backup_heartbeats(ip, port):
    keep_alive_request = chat_pb2.KeepAlive(ip=ip, port=port)
    while True:
        yield keep_alive_request
        time.sleep(primary.HEARTBEAT_INTERVAL)

def run(server_id):
    ip = constants.IP_PORT_DICT[server_id][0]
    port = constants.IP_PORT_DICT[server_id][1]

    with grpc.insecure_channel('{}:{}'.format(ip, port)) as channel:
        stub = chat_pb2_grpc.ChatStub(channel)
        # print("Congratulations! You have connected to the chat server.\n")

        # Establish bidirectional stream to send and receive keep-alive messages from primary server.
        # requestStream and responseStream are generators of chat_pb2.KeepAlive objects.
        requestStream = send_backup_heartbeats(ip, port)
        responseStream = stub.Heartbeats(requestStream)
        start_new_thread(keepalive_listen, (responseStream))


if __name__ == '__main__':
    logging.basicConfig()
    # Checks for correct number of args
    if len(sys.argv) != 2:
        print("Correct usage: script, server_id (0 = primary, 1 = backup1, 2 = backup2)")
        exit()
    server_id = int(sys.argv[1])
    run(server_id)
