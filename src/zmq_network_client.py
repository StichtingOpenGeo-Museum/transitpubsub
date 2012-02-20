"""
To test:
python zmq_network_client.py p CXX_A001_0 40002590 40000010
python zmq_network_client.py j CXX_A001_7001
"""

from consts import ZMQ_SERVER_NETWORK
import zmq
import sys

# Initialize a zeromq context
context = zmq.Context()

# Set up a channel to send network requests
client = context.socket(zmq.REQ)
client.connect(ZMQ_SERVER_NETWORK)

client.send(','.join(sys.argv[1:]))
print client.recv()
