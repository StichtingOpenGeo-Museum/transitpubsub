from consts import ZMQ_SERVER_PUNCTUALITY, ZMQ_PUBSUB_KV6
from punctuality import punctuality
import simplejson as serializer
import zmq
import sys

"""
[{'rd_y': 460337, 'rd_x': 142572, 'timestamp': '2012-02-20T01:29:14+01:00', 'dataownercode': 'CXX', 'messagetype': 'ONROUTE', 'source': 'VEHICLE', 'journeynumber': 7087, 'lineplanningnumber': 'H077', 'passagesequencenumber': 0, 'vehiclenumber': 3258, 'punctuality': -242, 'distancesincelastuserstop': 360, 'userstopcode': '50220240', 'operatingday': '2012-02-19', 'reinforcementnumber': 0}]
"""

# Initialize the storage
punct = punctuality()

# Initialize a zeromq context
context = zmq.Context()

# Set up a channel to receive punctuality requests
sys.stderr.write('Setting up a ZeroMQ REP: %s\n' % (ZMQ_SERVER_PUNCTUALITY))
client = context.socket(zmq.REP)
client.bind(ZMQ_SERVER_PUNCTUALITY)

# Set up a channel to receive KV6 requests
sys.stderr.write('Setting up a ZeroMQ SUB: %s\n' % (ZMQ_PUBSUB_KV6))
subscribe_kv6 = context.socket(zmq.SUB)
subscribe_kv6.connect(ZMQ_PUBSUB_KV6)
subscribe_kv6.setsockopt(zmq.SUBSCRIBE, '')

# Set up a poller
poller = zmq.Poller()
poller.register(client, zmq.POLLIN)
poller.register(subscribe_kv6, zmq.POLLIN)

sys.stderr.write('Ready.\n')

while True:
    socks = dict(poller.poll())

    if socks.get(client) == zmq.POLLIN:
        arguments = serializer.loads(client.recv())
        if len(arguments) == 3:
            client.send(serializer.dumps(punct.get(arguments[0], arguments[1], arguments[2])))
        else:
            client.send('')

    elif socks.get(subscribe_kv6) == zmq.POLLIN:
        results = serializer.loads(subscribe_kv6.recv())
        for result in results:
            punct.add(result)

