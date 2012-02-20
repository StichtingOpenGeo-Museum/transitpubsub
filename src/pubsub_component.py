#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import time
from optparse import OptionParser
import re

import sleekxmpp
from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.plugins.xep_0060.stanza.pubsub import Subscriptions
from modality import modality

from secret import component_server, component_port, component_jid, component_password

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


class PubsubComponent(ComponentXMPP):

    """
    A simple SleekXMPP component that echoes messages.
    """

    def __init__(self, jid, secret, server, port):
        ComponentXMPP.__init__(self, jid, secret, server, port)

        self.use_signals()

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can intialize
        # our roster.
        self.add_event_handler("session_start", self.start)
        
        self.add_event_handler("pubsub_subscribe", self._pubsub_subscribe)
        self.add_event_handler("pubsub_unsubscribe", self._pubsub_unsubscribe)
        self.add_event_handler("pubsub_retrieve_subscriptions", self._pubsub_retrieve_subscriptions)
        self.add_event_handler("pubsub_retrieve_affiliations", self._pubsub_retrieve_affiliations)
        self.add_event_handler("pubsub_get_items", self._pubsub_get_items)

        self.add_event_handler("pubsub_set_items", self._pubsub_set_items)
        self.add_event_handler("pubsub_create_node", self._pubsub_create_node)
        self.add_event_handler("pubsub_delete_node", self._pubsub_delete_node)
        self.add_event_handler("pubsub_retract_node", self._pubsub_retract)
        self.add_event_handler("pubsub_get_config_node", self._pubsub_get_config_node)

        self.auto_authorize = True # Automatic bidirectional subscriptions
        self.auto_subscribe = True

        self.pnick = 'openOV Transit Pubsub'
        
        self.modalities = { 
                            'bus': modality('bus'),
                          # 'drive': drive(),
                          # 'taxi': taxi(),
                          # 'tram': tram(),
                          #  'train': train(),
                          # 'walk': walk(),
                          # 'cycle': cycle()
                          }
 
    def _get_items(self, jid, node, data, disco, pubsub):
        try:
            firstpart = node.split('/', 2)[1]
        except:
            raise XMPPError(condition='item-not-found')

        if firstpart == 'passtimes':
            pass

        elif firstpart in self.modalities.keys():
            return self.modalities[firstpart].get_items(jid, node, data, disco, pubsub)
   
        raise XMPPError(condition='item-not-found')

    def _disco_items_query(self, jid, node, data):
        return self._get_items(jid, node, data, self['xep_0030'], None)
    
    def _pubsub_get_items(self, iq):
    	jid = iq['from'].bare
    	node = iq['pubsub']['items']['node']
        
        iq = self.makeIqResult(id=iq['id'], ifrom=iq['to'], ito=iq['from'])
        iq['pubsub'].append(self._get_items(jid, node, iq, None, self['xep_0060']))
        return iq.send(block=False)

    def _pubsub_subscribe(self, iq):
    	jid = iq['subscribe']['jid'].full
        node = iq['pubsub']['subscribe']['node']
        if node is not None:
            match = self._node_pattern.match(node)
            if match is not None:
                self.send_presence_subscription(pto=jid, ptype='subscribe', pnick=self.pnick)
                query = "INSERT INTO subscriptions (jid, node) VALUES (?, ?);"
                c = self.conn.cursor()
                c.execute(sql + ';', param)
                c.close()
                iq_reply = self.makeIqResult(id=iq['id'], ifrom=iq['to'], ito=iq['from'])
                return iq_reply.send(block=False)

        raise XMPPError(condition='item-not-found')

    def _pubsub_unsubscribe(self, iq):
    	jid = iq['subscribe']['jid'].full
        node = iq['pubsub']['subscribe']['node']
        subid = iq['pubsub']['subscribe']['subid']

        param = [jid]
        query = "DELETE FROM subscriptions WHERE jid = ?"

        if node is not None:
            param.append(node)
            query += " AND node = ?"

        if subid is not None:
            param.append(subid)
            query += " AND subid = ?"
        
        c = self.conn.cursor()
        # TODO; do something smart in the error case
        c.execute(sql + ';', param)
        c.close()
        
        iq_reply = self.makeIqResult(id=iq['id'], ifrom=iq['to'], ito=iq['from'])
        return iq_reply.send(block=False)

    def _pubsub_retrieve_subscriptions(self, iq):
    	jid = iq['from'].bare
        node = iq['pubsub']['subscriptions']['node']

        param = [jid + '%']
        query = "SELECT node, jid, 'subscribed', subid FROM subscriptions WHERE jid LIKE ?"

        if node is not None:
            param.append(node)
            query += " AND node = ?"

        subcriptions = Subscriptions()
        
        c = self.conn.cursor()
        c.execute(sql + ';', param)
        for row in c.fetchall():
            subscription = Subscription()
            subscription['node'] = row[0]
            subscription['jid'] = row[1]
            subscription['subscription'] = row[2]
            subscription['subid'] = row[3]
            subscriptions.append(subscription)

        c.close()

        iq_reply = self.makeIqResult(id=iq['id'], ifrom=iq['to'], ito=iq['from'])
        id_reply['pubsub'].append(subscriptions)
        return iq_reply.send(block=False)

    def _pubsub_retrieve_affiliations(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_set_items(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_create_node(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_delete_node(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_retract(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_get_config_node(self, iq):
        raise XMPPError(condition='feature-not-implemented')

    def cache_service_discovery(self, jid):
        self['xep_0030'].add_item(jid=jid, name='Any', node='', subnode='*')
        for subnode, modality in self.modalities.items():
            modality.cache_service_discovery(self['xep_0030'], jid)
            self['xep_0030'].add_item(jid=jid, name=modality.name, node='', subnode=subnode)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an intial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.cache_service_discovery(self.boundjid.bare)
        self['xep_0030'].set_node_handler('get_items', self.boundjid.bare, handler=self._disco_items_query)
        return


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Setup the PubsubComponent and register plugins. Note that while plugins
    # may have interdependencies, the order in which you register them does
    # not matter.
    xmpp = PubsubComponent(component_jid, component_password, component_server, component_port)
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0060') # PubSub

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        xmpp.process(threaded=False)
        print("Done")
    else:
        print("Unable to connect.")
