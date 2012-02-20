import re
import dateutil.parser
from datetime import datetime, timedelta, date
from consts import KV1_SQL, KV1_SQL_STOPPLACE, KV8_DATEDPASSTIME, KV1_NEAREST_USERSTOP_DISCO_SQL, KV1_NEAREST_USERSTOP_GET_ITEMS_SQL, KV1_NEAREST_STOPPLACE_DISCO_SQL, KV1_STOPPLACE_QUAYS_SQL, ZMQ_SERVER_PUNCTUALITY
from sleekxmpp.exceptions import XMPPError
from sleekxmpp.plugins.xep_0030 import DiscoItems
from kv1_netex_ifopt import netex_stopplace, netex_quay, modality_stopplace, modality_quay, modality_quaytype

import monetdb.sql
from secret import sql_username, sql_password, sql_hostname, sql_port, sql_database
from xml.etree import cElementTree as ET

from projections import wgs84_rd

import simplejson as serializer
import zmq

class modality:
    def __init__(self, name):
        self.name = name
        self.node = self.name.lower()

        self.data = {'town': [{'stopplace': [{'quay': [{'id': 'CBSGM001-000001', 'name': 'Iets'}], 'id': 'CBSGM001-CENTRAAL', 'name': 'Centraal'}], 'id': 'CBSGW001', 'name': 'Amsterdam'}]}
        #self.validnode = re.compile('/'+self.name+'(/postalregion(/(.+?)(/stopplace(/(.+?)(/quay(/(.+?))?)?)?)?)?)?$')
        self.validnode = re.compile('/'+self.name+'(/postalregion(/(.+?)(/stopplace(/(.+?)(/quay(/(.+?))?)?(/passtimes(/(201[2-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].+?))?)?)?)?)?)?$')
        self.validnode_latlon = re.compile('/'+self.name+'/latlon/([0-9.]+?),([0-9.]+?)/(postalregions|stopplaces|quays)$')
        self.connection = monetdb.sql.connect(username=sql_username, password=sql_password, hostname=sql_hostname, port=sql_port, database=sql_database, autocommit=True)

        # Initialize a zeromq context
        self.context = zmq.Context()

        # Set up a channel to send punctuality requests
        self.punctuality_client = self.context.socket(zmq.REQ)
        self.punctuality_client.connect(ZMQ_SERVER_PUNCTUALITY)

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
        print node
        if latlon is not None:
            lat = latlon.group(1)
            lon = latlon.group(2)
            what = latlon.group(3)
            
            x, y = wgs84_rd(lat, lon)
            x = int(x)
            y = int(y)
            if what == 'quays':
                if disco is not None:
                    return self.nearestuserstop_disco(disco, jid, node, x, y)
                elif pubsub is not None:
                    return self.nearestuserstop_get_items(pubsub, jid, node, x, y)
            elif what == 'stopplaces':
                if disco is not None:
                    return self.neareststopplace_disco(disco, jid, node, x, y)
                elif pubsub is not None:
                    return self.neareststopplace_get_items(pubsub, jid, node, x, y)

        else:
            if disco is not None:
                return disco.static.get_items(jid, node, data)
            
            elif pubsub is not None:
                print node
                match = self.validnode.match(node)
                if match is not None:
                    print 'match=>', match.group(0)
                    if match.group(9) is not None:
                        if match.group(10) is not None:
                            return self.passtimes(pubsub, match.group(3), match.group(6), match.group(9), match.group(12))
                        else:
                            return self.quay(pubsub, node, match.group(3), match.group(6), match.group(9))

                    elif match.group(6) is not None and match.group(6) != '':
                        if match.group(10) is not None:
                            return self.passtimes_stopplace(pubsub, match.group(3), match.group(6), match.group(12))
                        else:                            
                            return self.stopplace(pubsub, node, match.group(3), match.group(6))
                        

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
        cursor = self.connection.cursor()
        cursor.execute(KV1_NEAREST_USERSTOP_DISCO_SQL, {'x': x, 'y': y, 'maxitems': 10})

        result = disco.stanza.DiscoItems()
        result['node'] = node

        for town, userstopareacode, pointcode, name in cursor.fetchall():
            if userstopareacode is None:
                userstopareacode = '*'
            postalregion = '*'
            result.add_item(jid, node='/%s/postalregion/%s/stopplace/%s/quay/%s' % (self.name, postalregion, userstopareacode, pointcode), name=name)

        return result
    
    def neareststopplace_disco(self, disco, jid, node, x, y):
        cursor = self.connection.cursor()
        cursor.execute(KV1_NEAREST_STOPPLACE_DISCO_SQL, {'x': x, 'y': y, 'maxitems': 10})

        result = disco.stanza.DiscoItems()
        result['node'] = node

        for stopplaceid, stopplacename in cursor.fetchall():
            postalregion = '*'
            result.add_item(jid, node='/%s/postalregion/%s/stopplace/%s' % (self.name, postalregion, stopplaceid), name=stopplacename)

        return result

    def nearestuserstop_get_items(self, pubsub, jid, node, x, y):
        cursor = self.connection.cursor()
        cursor.execute(KV1_NEAREST_USERSTOP_GET_ITEMS_SQL, {'x': x, 'y': y, 'maxitems': 10})
            
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

    def stopplace(self, pubsub, node, town, stoparea):
        items = pubsub.stanza.Items()
        items['node'] = node

        cursor = self.connection.cursor()
        rows = cursor.execute(KV1_STOPPLACE_QUAYS_SQL, {'stoparea': stoparea})

        if rows > 0:
            quays = ''
            item = pubsub.stanza.Item()

            for sp_id, sp_name, sp_description, sp_type, sp_street, sp_town, sp_postalregion, q_dataownercode, q_publiccode, q_name, q_transportmode, q_longitude, q_latitude, q_altitude, q_x, q_y, q_description, q_boardinguse, q_aligtinguse, q_type in cursor.fetchall():
                quay_arguments = {'dataownercode': q_dataownercode, 'publiccode': q_publiccode, 'name': q_name, 'transportmode': q_transportmode, 'x': q_x, 'y': q_y, 'altitude': q_altitude, 'boardinguse': str(q_boardinguse).lower(), 'alightinguse': str(q_aligtinguse).lower(), 'quaytype': q_type, 'description': q_description}
                quays += netex_quay(quay_arguments)

            # TODO, a lot of things, like clean up but also escape for XML
            stopplace_arguments = { 'stopplaceid': sp_id, 'name': sp_name, 'town': sp_town, 'description': sp_description, 'stopplacetype': sp_type, 'street': sp_street, 'postalregion': sp_postalregion, 'quays': quays }
            item['payload'] = ET.XML(netex_stopplace(stopplace_arguments))
            items.append(item)

        return items

    def passtimes(self, pubsub, town, stoparea, quay, querydatetime=None):
        if querydatetime is not None:
            try:
                querydatetime = dateutil.parser.parse(querydatetime)
            except:
                return false
        else:
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

        cursor = self.connection.cursor()
        cursor.execute(KV1_SQL, { 'weekday': 2 ** ((querydatetime.weekday() + 1) % 7), # In SQL Monday is 1, our bitstring wants Sunday at 0.
                                  'operatingday': operatingday,
                                  'from': fromtime,
                                  'userstop': quay,
                                  'maxresults': 10 } )

        services = set([])
        allrows = cursor.fetchall()
        for dataownercode, lineplanningnumber, journeynumber, localservicelevelcode, userstopordernumber, userstopcode, linepublicnumber, linedirection, destinationcode, destinationname50, destinationdetail24, istimingstop, passtime, first, last, wheelchairaccessible in allrows:
            services.add((dataownercode, lineplanningnumber))

        actual = {}
        for service in services:
            self.punctuality_client.send(serializer.dumps([service[0], service[1], userstopcode]))
            actual.update(serializer.loads(self.punctuality_client.recv()))

        for dataownercode, lineplanningnumber, journeynumber, localservicelevelcode, userstopordernumber, userstopcode, linepublicnumber, linedirection, destinationcode, destinationname50, destinationdetail24, istimingstop, passtime, first, last, wheelchairaccessible in allrows:
            index = dataownercode + '_' + lineplanningnumber + '_' + str(journeynumber)

            if first:
                journeystoptype = 'FIRST'
            elif last:
                journeystoptype = 'LAST'
            else:
                journeystoptype = 'INTERMEDIATE'
            
            lastupdatetimestamp = datetime.today()
    
            if destinationdetail24 is None:
                destinationdetail24 = ''
            
            tripstopstatus = 'UNKNOWN'
            
            expectedarrivaltime = passtime
            expecteddeparturetime = passtime
            targetarrivaltime = passtime
            targetdeparturetime = passtime
           
            if index in actual:
                # TODO: some super duper prediction here!
                prediction = timedelta(seconds = actual[index]['punctuality'])

                if actual[index]['punctuality'] > 0 and actual[index]['hastimingstop']:
                    expecteddeparturetime = passtime
                else:
                    expecteddeparturetime += prediction

                expectedarrivaltime += prediction

                tripstopstatus = 'DRIVING'

            expectedarrivaltime = self.renderpasstime(expectedarrivaltime)
            expecteddeparturetime = self.renderpasstime(expecteddeparturetime)
            targetarrivaltime = self.renderpasstime(targetarrivaltime)
            targetdeparturetime = self.renderpasstime(targetdeparturetime)

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
                         'destinationdetail24': destinationdetail24,
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


    def passtimes_stopplace(self, pubsub, town, stoparea, querydatetime=None):
        if querydatetime is not None:
            try:
                querydatetime = dateutil.parser.parse(querydatetime)
            except:
                return false
        else:
            querydatetime = datetime.today()

        if querydatetime.hour <= 4:
            operatingday = querydatetime.date() - timedelta(days=1)
            fromtime = datetime.combine(date(1970, 1, 2), querydatetime.time())
        else:
            operatingday = querydatetime.date()
            fromtime = datetime.combine(date(1970, 1, 1), querydatetime.time())

        node_arguments = {'town': town, 'stoparea': stoparea }

        items = pubsub.stanza.Items()
        items['node'] = '/' + self.name + '/postalregion/%(town)s/stoparea/%(stoparea)s/passtimes' % node_arguments

        cursor = self.connection.cursor()
        cursor.execute(KV1_SQL_STOPPLACE, { 'weekday': 2 ** ((querydatetime.weekday() + 1) % 7), # In SQL Monday is 1, our bitstring wants Sunday at 0.
                                            'operatingday': operatingday,
                                            'from': fromtime,
                                            'stopplace': stoparea,
                                            'maxresults': 10 } )
        services = set([])
        allrows = cursor.fetchall()
        for dataownercode, lineplanningnumber, journeynumber, localservicelevelcode, userstopordernumber, userstopcode, linepublicnumber, linedirection, destinationcode, destinationname50, destinationdetail24, istimingstop, passtime, first, last, wheelchairaccessible in allrows:
            services.add((dataownercode, lineplanningnumber))

        actual = {}
        for service in services:
            self.punctuality_client.send(serializer.dumps([service[0], service[1], userstopcode]))
            actual.update(serializer.loads(self.punctuality_client.recv()))

        for dataownercode, lineplanningnumber, journeynumber, localservicelevelcode, userstopordernumber, userstopcode, linepublicnumber, linedirection, destinationcode, destinationname50, destinationdetail24, istimingstop, passtime, first, last, wheelchairaccessible  in allrows:
            index = dataownercode + '_' + lineplanningnumber + '_' + str(journeynumber)
            if first:
                journeystoptype = 'FIRST'
            elif last:
                journeystoptype = 'LAST'
            else:
                journeystoptype = 'INTERMEDIATE'
            
            lastupdatetimestamp = datetime.today()
    
            if destinationdetail24 is None:
                destinationdetail24 = ''
            tripstopstatus = 'UNKNOWN'
            
            expectedarrivaltime = passtime
            expecteddeparturetime = passtime
            targetarrivaltime = passtime
            targetdeparturetime = passtime
            
            if index in actual:
                # TODO: some super duper prediction here!
                prediction = timedelta(seconds = actual[index]['punctuality'])

                if actual[index]['punctuality'] > 0 and actual[index]['hastimingstop']:
                    expecteddeparturetime = passtime
                else:
                    expecteddeparturetime += prediction

                expectedarrivaltime += prediction

                tripstopstatus = 'DRIVING'

            expectedarrivaltime = self.renderpasstime(expectedarrivaltime)
            expecteddeparturetime = self.renderpasstime(expecteddeparturetime)
            targetarrivaltime = self.renderpasstime(targetarrivaltime)
            targetdeparturetime = self.renderpasstime(targetdeparturetime)

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
                         'destinationdetail24': destinationdetail24,
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



    def renderpasstime(self, passtime):
        if passtime.day == 2:
            return '%.2d:%.2d:%.2d' % (passtime.time().hour + 24, passtime.time().minute, passtime.time().second)
            #passtime = datetime.combine(operatingday + timedelta(days = 1), passtime.time()).isoformat()
        else:
            return passtime.time().isoformat()
            #passtime = datetime.combine(operatingday, passtime.time()).isoformat()


