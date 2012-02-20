import monetdb.sql
from secret import sql_username, sql_password, sql_hostname, sql_port, sql_database
from consts import ZMQ_SERVER_NETWORK
import zmq

class punctuality:
    def __init__(self):
        self.punctuality = {}
        self.points = {}
        #self._cache_points()

        self.context = zmq.Context()
        self.network_client = self.context.socket(zmq.REQ)
        self.network_client.connect(ZMQ_SERVER_NETWORK)

    def _cache_points(self):
        sql = """SELECT dataownercode, pointcode, locationx_ew, locationy_ns FROM point ORDER BY dataownercode, pointcode;"""

        connection = monetdb.sql.connect(username=sql_username, password=sql_password, hostname=sql_hostname, port=sql_port, database=sql_database, autocommit=True)
        cursor = connection.cursor()
        cursor.execute(sql)
        
        for dataownercode, pointcode, locationx_ew, locationy_ns in cursor.fetchall():
            index = str(dataownercode) + '_' + str(pointcode)
            self.points[index] = (locationx_ew, locationy_ns)

    def add(self, message):
        #if message['messagetype'] in ['ARRIVAL', 'ONSTOP', 'DEPARTURE']:
        #    index = str(message['dataownercode']) + '_' + str(message['userstopcode'])
        #    message['rd_y'], message['rd_x'] = self.points[index]

        print message
        index = str(message['dataownercode']) + '_' + str(message['lineplanningnumber'])
        if index in self.punctuality:
            if message['journeynumber'] in self.punctuality[index]:
                self.punctuality[index][message['journeynumber']][message['reinforcementnumber']] = message
            else:
                self.punctuality[index][message['journeynumber']] = {message['reinforcementnumber']: message}
        else:
            self.punctuality[index] = {message['journeynumber']: {message['reinforcementnumber']: message}}

    def get(self, dataownercode, lineplanningnumber, userstopcode):
        index = dataownercode + '_' + lineplanningnumber
        results = {}
        if index in self.punctuality:
            for journeys in self.punctuality[index].values():
                for trip in journeys.values():
                    if 'userstopcode' in trip and 'punctuality' in trip:
                        msg = ','.join(['p', str(trip['dataownercode']), str(trip['lineplanningnumber']), str(trip['journeynumber']), str(trip['operatingday']), str(trip['userstopcode']), str(userstopcode)])
                        print msg
                        self.network_client.send(msg)
                        result = self.network_client.recv()
                        print result
                        if result != '':
                            passed, timingstop = result.split(',')
                            if passed == '0':
                                # TODO: we might want to send back the 'best' punctuality here
                                results[index + '_' + str(trip['journeynumber'])] = {'userstopcode': trip['userstopcode'], 'punctuality': trip['punctuality'], 'hastimingstop': bool(timingstop)}

        return results
