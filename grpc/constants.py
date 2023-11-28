# Primary server default at IP_PORT_DICT[0], backup servers defaults at IP_PORT_DICT[1] and IP_PORT_DICT[2]
IP0 = '127.0.0.1'
IP1 = '10.250.226.222'
IP_PORT_DICT = {0 : [IP0, '8080'], 1 : [IP0, '8081'], 2 : [IP1, '8082']}

SNAPSHOT_INTERVAL = 60 # seconds
HEARTBEAT_INTERVAL = 5