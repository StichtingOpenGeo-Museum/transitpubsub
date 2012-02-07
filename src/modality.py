import re
from consts import KV1_SQL

class modality:
    def __init__(self):
        self.name = 'modality'
        self.node = self.name.lower()

        self.data = {'town': [{'stopplace': [{'quay': [{'id': 'CBSGM001-000001', 'name': 'Iets'}], 'id': 'CBSGM001-CENTRAAL', 'name': 'Centraal'}], 'id': 'CBSGW001', 'name': 'Amsterdam'}]}
        self.validnode = re.compile(self.modality+'(/town(/(.+?)(/stopplace(/(.+?)(/quay(/(.+?)(/(passtimes))?)?)?)?)?)?)?$')

    def cache_service_discovery(self, disco, jid):
        disco.add_item(jid=jid, name=self.name, node='', subnode=self.node)

        if len(self.data['town']) > 0:
            subnode = self.node + '/town'
            disco.add_item(jid=jid, name=self.name, node=self.node, subnode=subnode)
            for town in self.data['town']:
                subnode_town = subnode + '/' + town
                disco.add_item(jid=jid, name=self.name, node=subnode, subnode=subnode_town)

                if len(town['stopplace']) > 0:
                    subnode_town_stopplace = subnode_town + '/stopplace'
                    disco.add_item(jid=jid, name=self.name, node=subnode_town, subnode=subnode_town_stopplace)
                    for stopplace in town['stopplace']:
                        subnode_stopplace = subnode_town_stopplace + '/' + stopplace
                        disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace, subnode=subnode_stopplace)
                        
                        if len(stopplace['quay']) > 0:
                            subnode_town_stopplace_quay = subnode_town_stopplace + '/quay'
                            for quay in stopplace['quay']:
                                subnode_quay = subnode_town_stopplace_quay + '/' + quay
                                disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace_quay, subnode=subnode_quay)
                                disco.add_item(jid=jid, name=self.name, node=subnode_town_stopplace_quay, subnode=subnode_quay + '/passtimes')

    def get_items(self, jid, node, data, disco=None, pubsub=None):
        if disco is not None:
            return disco.static.get_items(jid, node, data)
        
        elif pubsub is not None:
            match = self.validnode.match(node)
            if match is not None:
                if match.group(11) is not None:
                    return self.passtimes(pubsub, match.group(3), match.group(6), match.group(9))

        raise XMPPError(condition='item-not-found') 

    def node_to_query(self, node):
        where = {}
        match = self.validnode.match(node)
        if lastindex >= 3 and match.group(3) != '*':
            where['town'] = match.group(3)
             
        if lastindex >= 6 and match.group(6) != '*'::
            where['stopplace'] = match.group(6)
        
        if lastindex >= 9 and match.group(9) != '*':
            where['quay'] = match.group(9)

        return ' AND '.join([arg+' = %('+arg+')s' for arg in where.keys()])

    def passtimes(self, pubsub, town, stoparea, quay):
        node_arguments = {'town': town, 'stoparea': stoparea, 'quay': quay }

        items = pubsub.stanza.Items()
        items['node'] = self.modality + '/town/%(town)s/stoparea/%(stoparea)s/quay/%(quay)s/passtimes' % node_arguments

        # TODO some voodoo
        sql = KV1_SQL % 
        for row in cursor.execute(sql):
            arguments = {'dataownercode': dataownercode, 
                         'operationdate': operationdate,
                         'lineplanningnumber': lineplanningnumber,
                         'journeynumber': journeynumber,
                         'fortifyordernumber': fortifyordernumber,
                         'userstopordernumber': userstopordernumber,
                         'userstopcode': userstopcode,
                         'localservicelevelcode': localservicelevelcode,
                         'linedirection': linedirection,
                         'lastupdatetimetamp': lastupdatetimetamp,
                         'destinationcode': destinationcode,
                         'istimingpoint': istimingpoint,
                         'destinationarrivaltime': destinationarrivaltime,
                         'targetarrivaltime': targetarrivaltime,
                         'expecteddeparturetime': expecteddeparturetime,
                         'targetdeparturetime': targetdeparturetime,
                         'tripstopstatus': tripstopstatus,
                         'sidecode': sidecode,
                         'wheelchairaccessible': wheelchairaccessible,
                         'timingpointdataownercode': timingpointdataownercode,
                         'timingpointcode': timingpointcode,
                         'journeystoptype': journeystoptype}

            item = pubsub.stanza.Item()
            item['id'] = '%(dataownercode)s_%(lineplanningnumber)s_%(journeynumber)s_%(fortifyordersumber)s' % arguments
            item['payload'] = KV8_DATEDPASSTIME % arguments
            items.append(item)

        return items
