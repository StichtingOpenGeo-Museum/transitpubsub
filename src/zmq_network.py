from consts import ZMQ_SERVER_NETWORK, ZMQ_PUBSUB_KV17
from network import network
from helpers import serialize
import zmq
import sys

# Initialize the cached network
sys.stderr.write('Caching networkgraph...')
net = network()
sys.stderr.write('Done!\n')

# Initialize a zeromq context
context = zmq.Context()

# Set up a channel to receive network requests
sys.stderr.write('Setting up a ZeroMQ REP: %s\n' % (ZMQ_SERVER_NETWORK))
client = context.socket(zmq.REP)
client.bind(ZMQ_SERVER_NETWORK)

# Set up a channel to receive KV17 requests
sys.stderr.write('Setting up a ZeroMQ SUB: %s\n' % (ZMQ_PUBSUB_KV17))
subscribe_kv17 = context.socket(zmq.SUB)
subscribe_kv17.connect(ZMQ_PUBSUB_KV17)
subscribe_kv17.setsockopt(zmq.SUBSCRIBE, '')

# Set up a poller
poller = zmq.Poller()
poller.register(client, zmq.POLLIN)
poller.register(subscribe_kv17, zmq.POLLIN)

sys.stderr.write('Ready.\n')

while True:
    socks = dict(poller.poll())

    if socks.get(client) == zmq.POLLIN:
        arguments = client.recv().split(',')
        if arguments[0] == 'j' and len(arguments) == 2:
            client.send(serialize(net.journeypatterncode(arguments[1])))
        elif arguments[0] == 'p' and len(arguments) == 7:
            client.send(serialize(net.passed(arguments[1], arguments[2], arguments[3], arguments[4], arguments[5], arguments[6])))
        else:
            client.send('')

    elif socks.get(subscribe_kv17) == zmq.POLLIN:
        pass
