"""
To test:
"""

from consts import ZMQ_SERVER_PUNCTUALITY
import simplejson as serializer
import zmq
import sys

# Initialize a zeromq context
context = zmq.Context()

# Set up a channel to send punctuality requests
client = context.socket(zmq.REQ)
client.connect(ZMQ_SERVER_PUNCTUALITY)

client.send(serializer.dumps(sys.argv[1:]))
print client.recv()
