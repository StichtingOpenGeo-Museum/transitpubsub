import monetdb.sql
from datetime import date
from secret import sql_username, sql_password, sql_hostname, sql_port, sql_database

class network:
    def __init__(self):
        self.journeys = {}
        self.network = {}
        self.timingstops = {}
        self._cache_journeys()
        self._cache_network()

    def _cache_network(self):
        sql = """SELECT dataownercode, lineplanningnumber, journeypatterncode, userstopcodebegin, timinglinkorder, istimingstop FROM jopatili ORDER BY dataownercode, lineplanningnumber, journeypatterncode, userstopcodebegin;"""

        connection = monetdb.sql.connect(username=sql_username, password=sql_password, hostname=sql_hostname, port=sql_port, database=sql_database, autocommit=True)
        cursor = connection.cursor()
        cursor.execute(sql)
        
        for dataownercode, lineplanningnumber, journeypatterncode, userstopcodebegin, timinglinkorder, istimingstop in cursor.fetchall():
            index = '_'.join([str(dataownercode), str(lineplanningnumber), str(journeypatterncode), str(userstopcodebegin)])
            self.network[index] = timinglinkorder

            if istimingstop and timinglinkorder > 1:
                if index in self.timingstops:
                    self.timingstops[index].add(timinglinkorder)
                else:
                    self.timingstops[index] = set([timinglinkorder])

    def _cache_journeys(self, operatingdate=None):
        if operatingdate is None:
            operatingdate = date.today()

        sql = """SELECT pujo.dataownercode, pujo.lineplanningnumber, pujo.journeynumber, pujo.journeypatterncode FROM pujo, tive, pegrval WHERE pujo.daytype = power(2, (dayofweek(CAST(%(operatingdate)s AS date)) - 1)) AND %(operatingdate)s BETWEEN pegrval.validfrom AND pegrval.validthru AND tive.dataownercode = pegrval.dataownercode AND tive.organizationalunitcode = pegrval.organizationalunitcode AND tive.periodgroupcode = pegrval.periodgroupcode AND pujo.timetableversioncode = tive.timetableversioncode AND pujo.organizationalunitcode = tive.organizationalunitcode AND pujo.periodgroupcode = tive.periodgroupcode;"""
    
        connection = monetdb.sql.connect(username=sql_username, password=sql_password, hostname=sql_hostname, port=sql_port, database=sql_database, autocommit=True)
        cursor = connection.cursor()
        cursor.execute(sql, {'operatingdate': operatingdate})

        for dataownercode, lineplanningnumber, journeynumber, journeypatterncode in cursor.fetchall():
            index = '_'.join([str(dataownercode), str(lineplanningnumber), str(journeynumber)])
            self.journeys[index] = journeypatterncode

    def journeypatterncode(self, doc_lpn_jn):
        try:
            return self.journeys[doc_lpn_jn]
        except:
            return None

    def passed(self, doc_lpn_jpc, userstoprequest, userstopactual):
        try:
            userstoprequest_tp = self.network[doc_lpn_jpc+'_'+userstoprequest]
            userstopactual_tp = self.network[doc_lpn_jpc+'_'+userstopactual]
        except:
            return None

        result = userstoprequest_tp > userstopactual_tp
        if result:
            return True, None
        else:
            return False, self.timingstop(doc_lpn_jpc, userstoprequest_tp, userstopactual_tp)

    def timingstop(self, doc_lpn_jpc, userstoprequest_tp, userstopactual_tp):
        if doc_lpn_jpc in self.network:
            # Thanks to Floorter use this amazing oneliner :)
            return bool(set(range(userstopactual_tp,userstoprequest_tp)) & self.timingstops[doc_lpn_jpc])
        
        return False

if __name__ == "__main__":        
    import time
    import timeit
    tmp = network()
    while True:
        print tmp.passed('CXX_A001_0', '40000010', '40002690')
        t = timeit.Timer("tmp.passed('CXX_A001_0', '40000010', '40002690')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)
        t = timeit.Timer("tmp.passed('CXX_A001_0', '40002690', '40000010')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)
        t = timeit.Timer("tmp.passed('CXX_Z494_0', '77370030', '77670030')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)
        t = timeit.Timer("tmp.passed('CXX_A006_0', '40013360', '40004024')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)

        print tmp.journeypatterncode('CXX_A001_7001')
        t = timeit.Timer("tmp.journeypatterncode('CXX_A001_7001')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)
        print tmp.journeypatterncode('CXX_Z494_7006')
        t = timeit.Timer("tmp.journeypatterncode('CXX_Z494_7006')", "from __main__ import tmp")
        print "%.2f usec/pass" % (1000000 * t.timeit(number=100000)/100000)

        time.sleep(1)
