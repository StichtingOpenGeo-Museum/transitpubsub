ZMQ_SERVER_NSAPI="tcp://127.0.0.1:6040"
ZMQ_PUBSUB_NSAPI="tcp://127.0.0.1:6041"

KV1_SQL="""SELECT
pujo.dataownercode AS doc,
pujo.lineplanningnumber AS lpn,
pujo.journeynumber AS jn,
pujo.journeypatterncode AS jpn,
timdemrnt.userstopcodebegin AS us_from,
timdemrnt.userstopcodeend AS us_to,
timdemrnt.timinglinkorder AS tlo,
cast((select sum(summation.totaldrivetime) FROM timdemrnt AS summation where
            summation.dataownercode = timdemrnt.dataownercode AND
            summation.lineplanningnumber = timdemrnt.lineplanningnumber AND
            summation.journeypatterncode = timdemrnt.journeypatterncode AND
            summation.timedemandgroupcode = timdemrnt.timedemandgroupcode AND
            summation.timinglinkorder < timdemrnt.timinglinkorder) AS interval second) + pujo.departuretime,
(usrstopend.userstoptype = 'PASSENGER') AS passengerstop
from
pujo, timdemrnt, pegrval, usrstop AS usrstopbegin, usrstop AS usrstopend, timdemrnt AS fromhere, tive
where
pujo.dataownercode = timdemrnt.dataownercode AND
pujo.lineplanningnumber = timdemrnt.lineplanningnumber AND
pujo.journeypatterncode = timdemrnt.journeypatterncode AND
pujo.timedemandgroupcode = timdemrnt.timedemandgroupcode AND
pujo.dataownercode = fromhere.dataownercode AND
pujo.lineplanningnumber = fromhere.lineplanningnumber AND
pujo.journeypatterncode = fromhere.journeypatterncode AND
pujo.timedemandgroupcode = fromhere.timedemandgroupcode AND
pujo.dataownercode = tive.dataownercode AND
pujo.timetableversioncode = tive.timetableversioncode AND
pujo.organizationalunitcode = tive.organizationalunitcode AND
pujo.periodgroupcode = tive.periodgroupcode AND
tive.dataownercode = pegrval.dataownercode AND
tive.organizationalunitcode = pegrval.organizationalunitcode AND
tive.periodgroupcode = pegrval.periodgroupcode AND
timdemrnt.dataownercode = usrstopbegin.dataownercode AND
timdemrnt.dataownercode = usrstopend.dataownercode AND
timdemrnt.userstopcodebegin = usrstopbegin.userstopcode AND
timdemrnt.userstopcodeend = usrstopend.userstopcode AND
pujo.daytype%(weekday)s = True AND
'%(operatingday)s' BETWEEN pegrval.validfrom AND pegrval.validthru AND
pujo.departuretime BETWEEN '%(betweenfrom)s' AND '%(betweento)s' AND
fromhere.userstopcodebegin = '%(userstop)s' AND
timdemrnt.userstopcodebegin = '%(userstop)s'
ORDER BY
pujo.dataownercode, pujo.lineplanningnumber, pujo.departuretime,
pujo.timetableversioncode, pujo.journeypatterncode,
pujo.timedemandgroupcode, timdemrnt.timinglinkorder LIMIT 40;"""

KV8_DATEDPASSTIME="""<tmi8:DATEDPASSTIME xmlns:tmi8="http://bison.connekt.nl/tmi8/kv7kv8/msg">
    <tmi8:dataownercode>%(dataownercode)s</tmi8:dataownercode>
    <tmi8:operationdate>%(operationdate)s</tmi8:operationdate>
    <tmi8:lineplanningnumber>%(lineplanningnumber)s</tmi8:lineplanningnumber>
    <tmi8:journeynumber>%(journeynumber)s</tmi8:journeynumber>
    <tmi8:fortifyordernumber>%(fortifyordernumber)s</tmi8:fortifyordernumber>
    <tmi8:userstopordernumber>%(userstopordernumber)s</tmi8:userstopordernumber>
    <tmi8:userstopcode>%(userstopcode)s</tmi8:userstopcode>
    <tmi8:localservicelevelcode>%(localservicelevelcode)s</tmi8:localservicelevelcode>
    <tmi8:linedirection>%(linedirection)s</tmi8:linedirection>
    <tmi8:lastupdatetimestamp>%(lastupdatetimetamp)s</tmi8:lastupdatetimestamp>
    <tmi8:destinationcode>%(destinationcode)s</tmi8:destinationcode>
    <tmi8:istimingstop>%(istimingpoint)s</tmi8:istimingstop>
    <tmi8:expectedarrivaltime>%(destinationarrivaltime)s</tmi8:expectedarrivaltime>
    <tmi8:targetarrivaltime>%(targetarrivaltime)s</tmi8:targetarrivaltime>
    <tmi8:expecteddeparturetime>%(expecteddeparturetime)</tmi8:expecteddeparturetime>
    <tmi8:targetdeparturetime>%(targetdeparturetime)</tmi8:targetdeparturetime>
    <tmi8:tripstopstatus>%(tripstopstatus)s</tmi8:tripstopstatus>
    <tmi8:sidecode>%(sidecode)s</tmi8:sidecode>
    <tmi8:wheelchairaccessible>%(wheelchairaccessible)s</tmi8:wheelchairaccessible>
    <tmi8:timingpointdataownercode>%(timingpointdataownercode)s</tmi8:timingpointdataownercode>
    <tmi8:timingpointcode>%(timingpointcode)s</tmi8:timingpointcode>
    <tmi8:journeystoptype>%(journeystoptype)s</tmi8:journeystoptype>
</tmi8:DATEDPASSTIME>"""

{'dataownercode': dataownercode,
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
