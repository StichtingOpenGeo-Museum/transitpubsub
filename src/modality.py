import re
from datetime import datetime, timedelta, date
from consts import KV1_SQL, KV8_DATEDPASSTIME, WEEKDAYS, KV1_NEAREST_USERSTOP_DISCO_SQL, KV1_NEAREST_USERSTOP_GET_ITEMS_SQL
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.plugins.xep_0030 import DiscoItems
from kv1_netex_ifopt import netex_quay, modality_stopplace, modality_quay, modality_quaytype

import monetdb.sql
from secret import sql_username, sql_password, sql_hostname, sql_port, sql_database
from xml.etree import cElementTree as ET

from projections import wgs84_rd


class modality:
    def __init__(self, name):
        self.name = name
        self.node = self.name.lower()

        self.data = {'town': [{'stopplace': [{'quay': [{'id': 'CBSGM001-000001', 'name': 'Iets'}], 'id': 'CBSGM001-CENTRAAL', 'name': 'Centraal'}], 'id': 'CBSGW001', 'name': 'Amsterdam'}]}
        self.validnode = re.compile('/'+self.name+'(/postalregion(/(.+?)(/stopplace(/(.+?)(/quay(/(.+?)(/(passtimes))?)?)?)?)?)?)?$')
        self.validnode_latlon = re.compile('/'+self.name+'/latlon/([0-9.]+?),([0-9.]+?)/(postalregions|stopplaces|quays)$')
        self.connection = monetdb.sql.connect(username=sql_username, password=sql_password, hostname=sql_hostname, port=sql_port, database=sql_database, autocommit=False)

    def cache_service_discovery(self, disco, jid):
        disco.add_item(jid=jid, name=self.name, node='', subnode=self.node)

        if len(self.data['town']) > 0:
            subnode = self.node + '/postalregion'
            disco.add_item(jid=jid, name=self.name, node=self.node, subnode=subnode)
            for town in self.data['town']:
                subnode_town = subnode + '/' + town['id']
                disco.add_item(jid=jid, name=self.name, node=subnode, subnode=subnode_town)

                if len(town['stopplace']) > 0:
                    subnode_town_stopplace = subnode_town + '/stopplace'
                    disco.add_item(jid=jid, name=self.name, node=subnode_town, subnode=subnode_town_stopplace)
                    for stopplace in town['stopplace']:
                        subnode_stopplace = subnode_town_stopplace + '/' + stopplace['id']
                        disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace, subnode=subnode_stopplace)
                        
                        if len(stopplace['quay']) > 0:
                            subnode_town_stopplace_quay = subnode_town_stopplace + '/quay'
                            for quay in stopplace['quay']:
                                subnode_quay = subnode_town_stopplace_quay + '/' + quay['id']
                                disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace_quay, subnode=subnode_quay)
                                disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace_quay, subnode=subnode_quay + '/passtimes')

    def get_items(self, jid, node, data, disco=None, pubsub=None):
        latlon = self.validnode_latlon.match(node)
        if latlon is not None:
            lat = latlon.group(1)
            lon = latlon.group(2)
            what = latlon.group(3)
            if what == 'quays':
                x, y = wgs84_rd(lat, lon)
                if disco is not None:
                    return self.nearestuserstop_disco(disco, jid, node, x, y)
                elif pubsub is not None:
                    return self.nearestuserstop_get_items(pubsub, jid, node, x, y)

        else:
            if disco is not None:
                return disco.static.get_items(jid, node, data)
            
            elif pubsub is not None:
                print node
                match = self.validnode.match(node)
                if match is not None:
                    if match.group(11) is not None:
                        return self.passtimes(pubsub, match.group(3), match.group(6), match.group(9))

        raise XMPPError(condition='item-not-found') 

    def node_to_query(self, node):
        where = {}
        match = self.validnode.match(node)
        if lastindex >= 3 and match.group(3) != '*':
            where['postalregion'] = match.group(3)
             
        if lastindex >= 6 and match.group(6) != '*':
            where['stopplace'] = match.group(6)
        
        if lastindex >= 9 and match.group(9) != '*':
            where['quay'] = match.group(9)

        return ' AND '.join([arg+' = %('+arg+')s' for arg in where.keys()])

    def nearestuserstop_disco(self, disco, jid, node, x, y):
        sql = KV1_NEAREST_USERSTOP_DISCO_SQL % {'x': x, 'y': y, 'maxitems': 10}
        cursor = self.connection.cursor()
        cursor.execute(sql)

        result = disco.stanza.DiscoItems()
        result['node'] = node

        for town, userstopareacode, pointcode, name in cursor.fetchall():
            if userstopareacode is None:
                userstopareacode = '*'
            result.add_item(jid, node='/%s/postalregion/%s/stopplace/%s/quay/%s' % (self.modality, town, userstopareacode, pointcode), name=name)

        return result

    def nearestuserstop_get_items(self, pubsub, jid, node, x, y):
        sql = KV1_NEAREST_USERSTOP_GET_ITEMS_SQL % {'x': x, 'y': y, 'maxitems': 10}
        cursor = self.connection.cursor()
        cursor.execute(sql)
            
        items = pubsub.stanza.Items()
        items['node'] = node

        for dataownercode, areacode, areaname, areatown, areadescription, stopcode, stopname, stoptown, stopdescription, boardinguse, alightinguse, locationx, locationy, locationz in cursor.fetchall():
            if stopdescription is None:
                stopdescription = ''

            quay_arguments = {'dataownercode': dataownercode, 'publiccode': stopcode, 'name': stopname, 'transportmode': modality_quay[self.name], 'x': locationx, 'y': locationy, 'altitude': locationz, 'boardinguse': str(boardinguse).lower(), 'alightinguse': str(alightinguse).lower(), 'quaytype': modality_quaytype[self.name], 'description': stopdescription}

            item = pubsub.stanza.Item()
            item['id'] = '%(userstopcode)s' % {'dataownercode': dataownercode, 'userstopcode': stopcode}
            item['payload'] = ET.XML(netex_quay(quay_arguments))

            items.append(item)

        return items

    def passtimes(self, pubsub, town, stoparea, quay, querydatetime=None):
        if querydatetime is None:
            querydatetime = datetime.today()

        if querydatetime.hour <= 4:
            operatingday = querydatetime.date() - timedelta(days=1)
            fromtime = datetime.combine(date(1970, 1, 2), querydatetime.time())
        else:
            operatingday = querydatetime.date()
            fromtime = datetime.combine(date(1970, 1, 1), querydatetime.time())

        node_arguments = {'town': town, 'stoparea': stoparea, 'quay': quay }

        items = pubsub.stanza.Items()
        items['node'] = '/' + self.name + '/postalregion/%(town)s/stoparea/%(stoparea)s/quay/%(quay)s/passtimes' % node_arguments

        sql = KV1_SQL % { 'weekday': WEEKDAYS[querydatetime.weekday()],
                          'operatingday': operatingday,
                          'from': fromtime,
                          'userstop': quay,
                          'maxresults': 10 }

        cursor = self.connection.cursor()
        cursor.execute(sql)

        for dataownercode, lineplanningnumber, journeynumber, localservicelevelcode, userstopordernumber, userstopcode, linepublicnumber, linedirection, destinationcode, destinationname50, istimingstop, passtime, first, last, wheelchairaccessible  in cursor.fetchall():
            if first:
                journeystoptype = 'FIRST'
            elif last:
                journeystoptype = 'LAST'
            else:
                journeystoptype = 'INTERMEDIATE'
            
            lastupdatetimestamp = datetime.today()
    
            if passtime.day == 2:
                passtime = '%.2d:%.2d:%.2d' % (passtime.time().hour + 24, passtime.time().minute, passtime.time().second)
                #passtime = datetime.combine(operatingday + timedelta(days = 1), passtime.time()).isoformat()
            else:
                passtime = passtime.time().isoformat()
                #passtime = datetime.combine(operatingday, passtime.time()).isoformat()

            expectedarrivaltime = passtime
            expecteddeparturetime = passtime
            targetarrivaltime = passtime
            targetdeparturetime = passtime

            tripstopstatus = 'UNKNOWN'
            timingpointdataownercode = 'OPENOV'
            timingpointcode = userstopcode
            sidecode = '-'
            fortifyordernumber = 0

            arguments = {'dataownercode': dataownercode,
                         'operationdate': operatingday,
                         'lineplanningnumber': lineplanningnumber,
                         'linepublicnumber': linepublicnumber,
                         'journeynumber': journeynumber,
                         'fortifyordernumber': fortifyordernumber,
                         'userstopordernumber': userstopordernumber,
                         'userstopcode': userstopcode,
                         'localservicelevelcode': localservicelevelcode,
                         'linedirection': linedirection,
                         'lastupdatetimestamp': lastupdatetimestamp,
                         'destinationcode': destinationcode,
                         'destinationname50': destinationname50,
                         'istimingpoint': str(istimingstop).lower(),
                         'expectedarrivaltime': expectedarrivaltime,
                         'targetarrivaltime': targetarrivaltime,
                         'expecteddeparturetime': expecteddeparturetime,
                         'targetdeparturetime': targetdeparturetime,
                         'tripstopstatus': tripstopstatus,
                         'sidecode': sidecode,
                         'wheelchairaccessible': str(wheelchairaccessible).lower(),
                         'timingpointdataownercode': timingpointdataownercode,
                         'timingpointcode': timingpointcode,
                         'journeystoptype': journeystoptype}

            item = pubsub.stanza.Item()
            item['id'] = '%(dataownercode)s_%(lineplanningnumber)s_%(journeynumber)s_%(fortifyordernumber)s' % arguments
            item['payload'] = ET.XML(KV8_DATEDPASSTIME % arguments)
            items.append(item)

        return items
