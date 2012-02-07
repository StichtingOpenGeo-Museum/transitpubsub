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
                            'bus': bus(),
                          # 'drive': drive(),
                          # 'taxi': taxi(),
                          # 'tram': tram(),
                            'train': train(),
                          # 'walk': walk(),
                          # 'cycle': cycle()
                          }
 
    def _get_items(self, jid, node, data, disco):
        if node == 'passtimes':
            # return all next departures

        elif node in self.modalities.keys():
            return self.modalities[node].get_items(jid, node, data, disco)
    
        raise XMPPError(condition='item-not-found')

    def _disco_items_query(self, jid, node, data):
        return _get_items(jid, node, data, self['xep_0030'])
    
    def _pubsub_get_items(self, data, jid, node):
        return _get_items(jid, node, data, None)  

    def _pubsub_subscribe(self, iq, jid, node=None):
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

    def _pubsub_unsubscribe(self, iq, jid, node=None, subid=None):
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

    def _pubsub_retrieve_subscriptions(self, iq, jid, node=None):
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

    def _pubsub_retrieve_affiliations(self, iq, jid, node=None):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_set_items(self, iq, jid, node):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_create_node(self, iq, jid, node):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_delete_node(self, iq, jid, node):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_retract(self, iq, jid, node):
        raise XMPPError(condition='feature-not-implemented')

    def _pubsub_get_config_node(self, iq, jid, node):
        raise XMPPError(condition='feature-not-implemented')

    def cache_service_discovery(self, jid):
        self['xep_0030'].add_item(jid=jid, name='Any', node='', subnode='*')
        for subnode, modality in modalities.items():
            modality.cache_service_discovery(self['xep_0030'], jid)
            self['xep_0030'].add_item(jid=jid, name=modality.name, node='', subnode=subnode)

        for code, station in self.stations.stations.items():
            self['xep_0030'].add_item(jid=jid, name=station.name, node='stations', subnode='stations/%s'%(code))
            self['xep_0030'].add_item(jid=jid, name='Actuele Vertrektijden', node='stations/%s'%(code), subnode='stations/%s/avt'%(code))
            self['xep_0030'].add_item(jid=jid, name='Voorzieningen', node='stations/%s'%(code), subnode='stations/%s/vz'%(code))
            self['xep_0030'].add_item(jid=jid, name='Storingen en Werkzaamheden', node='stations/%s'%(code), subnode='stations/%s/storingen'%(code))
            self['xep_0030'].add_item(jid=jid, name='Actuele Storingen en Werkzaamheden', node='stations/%s/storingen'%(code), subnode='stations/%s/storingen/actueel'%(code))
            self['xep_0030'].add_item(jid=jid, name='Geplande Storingen en Werkzaamheden', node='stations/%s/storingen'%(code), subnode='stations/%s/storingen/gepland'%(code))

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
        self['xep_0030'].set_node_handler('disco_items_query', self.boundjid.bare, handler=self._get_items30)
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

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-s", "--server", dest="server",
                    help="server to connect to")
    optp.add_option("-P", "--port", dest="port",
                    help="port to connect to")

    opts, args = optp.parse_args()

    if opts.jid is None:
        opts.jid = raw_input("Component JID: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.server is None:
        opts.server = raw_input("Server: ")
    if opts.port is None:
        opts.port = int(raw_input("Port: "))

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Setup the PubsubComponent and register plugins. Note that while plugins
    # may have interdependencies, the order in which you register them does
    # not matter.
    xmpp = PubsubComponent(opts.jid, opts.password, opts.server, opts.port)
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0060') # PubSub

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        xmpp.process(threaded=False)
        print("Done")
    else:
        print("Unable to connect.")
