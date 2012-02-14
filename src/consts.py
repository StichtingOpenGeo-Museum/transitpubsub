ZMQ_SERVER_NSAPI="tcp://127.0.0.1:6040"
ZMQ_PUBSUB_NSAPI="tcp://127.0.0.1:6041"

WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

KV1_SUM_TOTALTIME="""select max(total) from (select sum(totaldrivetime) as total from timdemrnt group by dataownercode, lineplanningnumber, journeypatterncode, timedemandgroupcode) as x;"""

KV1_SQL="""
select 
cache_kv1_3.dataownercode AS dataownercode,
cache_kv1_3.lineplanningnumber AS lineplanningnumber,
cache_kv1_3.journeynumber AS journeynumber,
cache_kv1_3.journeypatterncode AS localservicelevelcode,
timdemrnt.timinglinkorder AS userstopordernumber,
timdemrnt.userstopcodebegin AS userstopcode,
cache_kv1.linepublicnumber AS linepublicnumber,
cache_kv1.direction AS linedirection,
jopatili.destcode AS destinationcode,
dest.destnamefull AS destinationname50,
jopatili.istimingstop AS istimingstop,
cache_kv1_3.departuretime + cache_kv1_2.totaldrivetime AS passtime,
cache_kv1.userstopcodebegin = userstopcode as first,
cache_kv1.userstopcodeend = userstopcode as last,
cache_kv1_3.wheelchairaccessible as wheelchairaccessible
from cache_kv1_3, cache_kv1, timdemrnt AS fromhere, timdemrnt, usrstop AS usrstopbegin, jopatili, cache_kv1_2, dest where
dest.dataownercode = jopatili.dataownercode AND
dest.destcode = jopatili.destcode AND
cache_kv1_3.dataownercode = timdemrnt.dataownercode AND
cache_kv1_3.lineplanningnumber = timdemrnt.lineplanningnumber AND
cache_kv1_3.journeypatterncode = timdemrnt.journeypatterncode AND
cache_kv1_3.timedemandgroupcode = timdemrnt.timedemandgroupcode AND
jopatili.dataownercode = timdemrnt.dataownercode AND
jopatili.lineplanningnumber = timdemrnt.lineplanningnumber AND
jopatili.journeypatterncode = timdemrnt.journeypatterncode AND
jopatili.timinglinkorder = timdemrnt.timinglinkorder AND
cache_kv1_2.dataownercode = timdemrnt.dataownercode AND
cache_kv1_2.lineplanningnumber = timdemrnt.lineplanningnumber AND
cache_kv1_2.journeypatterncode = timdemrnt.journeypatterncode AND
cache_kv1_2.timedemandgroupcode = timdemrnt.timedemandgroupcode AND
cache_kv1_2.timinglinkorder = timdemrnt.timinglinkorder AND
timdemrnt.dataownercode = usrstopbegin.dataownercode AND
timdemrnt.userstopcodebegin = usrstopbegin.userstopcode AND
cache_kv1_3.dataownercode = fromhere.dataownercode AND
cache_kv1_3.lineplanningnumber = fromhere.lineplanningnumber AND
cache_kv1_3.journeypatterncode = fromhere.journeypatterncode AND
cache_kv1_3.timedemandgroupcode = fromhere.timedemandgroupcode AND
cache_kv1_3.dataownercode = cache_kv1.dataownercode AND
cache_kv1_3.lineplanningnumber = cache_kv1.lineplanningnumber AND
cache_kv1_3.timedemandgroupcode = cache_kv1.timedemandgroupcode AND
cache_kv1_3.journeypatterncode = cache_kv1.journeypatterncode AND
cache_kv1_3.daytype%(weekday)s = true and '%(operatingday)s' BETWEEN cache_kv1_3.validfrom AND cache_kv1_3.validthru AND
cache_kv1_3.departuretime BETWEEN cast('%(from)s' AS TIMESTAMP) - interval '7680' second and cast('%(from)s' AS TIMESTAMP) + interval '7680' second AND
fromhere.userstopcodebegin = '%(userstop)s' AND
timdemrnt.userstopcodebegin = '%(userstop)s' AND
(cache_kv1_3.departuretime + cache_kv1_2.totaldrivetime) >= cast('%(from)s' AS TIMESTAMP) order by passtime limit %(maxresults)d;"""

KV8_DATEDPASSTIME="""<tmi8:DATEDPASSTIME xmlns:tmi8="http://bison.connekt.nl/tmi8/kv7kv8/msg">
    <tmi8:dataownercode>%(dataownercode)s</tmi8:dataownercode>
    <tmi8:operationdate>%(operationdate)s</tmi8:operationdate>
    <tmi8:lineplanningnumber>%(lineplanningnumber)s</tmi8:lineplanningnumber>
    <tmi8:linepublicnumber>%(linepublicnumber)s</tmi8:linepublicnumber>
    <tmi8:journeynumber>%(journeynumber)s</tmi8:journeynumber>
    <tmi8:fortifyordernumber>%(fortifyordernumber)s</tmi8:fortifyordernumber>
    <tmi8:userstopordernumber>%(userstopordernumber)s</tmi8:userstopordernumber>
    <tmi8:userstopcode>%(userstopcode)s</tmi8:userstopcode>
    <tmi8:localservicelevelcode>%(localservicelevelcode)s</tmi8:localservicelevelcode>
    <tmi8:linedirection>%(linedirection)s</tmi8:linedirection>
    <tmi8:lastupdatetimestamp>%(lastupdatetimestamp)s</tmi8:lastupdatetimestamp>
    <tmi8:destinationcode>%(destinationcode)s</tmi8:destinationcode>
    <tmi8:destinationname50>%(destinationname50)s</tmi8:destinationname50>
    <tmi8:istimingstop>%(istimingpoint)s</tmi8:istimingstop>
    <tmi8:expectedarrivaltime>%(expectedarrivaltime)s</tmi8:expectedarrivaltime>
    <tmi8:targetarrivaltime>%(targetarrivaltime)s</tmi8:targetarrivaltime>
    <tmi8:expecteddeparturetime>%(expecteddeparturetime)s</tmi8:expecteddeparturetime>
    <tmi8:targetdeparturetime>%(targetdeparturetime)s</tmi8:targetdeparturetime>
    <tmi8:tripstopstatus>%(tripstopstatus)s</tmi8:tripstopstatus>
    <tmi8:sidecode>%(sidecode)s</tmi8:sidecode>
    <tmi8:wheelchairaccessible>%(wheelchairaccessible)s</tmi8:wheelchairaccessible>
    <tmi8:timingpointdataownercode>%(timingpointdataownercode)s</tmi8:timingpointdataownercode>
    <tmi8:timingpointcode>%(timingpointcode)s</tmi8:timingpointcode>
    <tmi8:journeystoptype>%(journeystoptype)s</tmi8:journeystoptype>
</tmi8:DATEDPASSTIME>"""

KV1_NEAREST_STOPPLACE_DISCO_SQL="""SELECT stopplaces.id, stopplaces.name FROM quays, stopplaces WHERE stopplaces.id = stopplace ORDER BY (((x - (%(x)d))*(x - (%(x)d)))+((y - (%(y)d))*(y - (%(y)d)))) LIMIT %(maxitems)d;"""

KV1_NEAREST_USERSTOP_DISCO_SQL="""SELECT town, userstopareacode, pointcode, name FROM point, usrstop WHERE point.pointcode = usrstop.userstopcode AND point.pointtype = 'SP' AND usrstop.userstoptype = 'PASSENGER' ORDER BY (((locationx_ew - (%(x)d))*(locationx_ew - (%(x)d)))+((locationy_ns - (%(y)d))*(locationy_ns - (%(y)d)))) LIMIT %(maxitems)d;"""

KV1_NEAREST_USERSTOP_GET_ITEMS_SQL="""SELECT usrstop.dataownercode, usrstop.userstopareacode, usrstar.name, usrstar.town, usrstar.description, usrstop.userstopcode, usrstop.name, usrstop.town, usrstop.description, usrstop.getin, usrstop.getout, point.locationx_ew, point.locationy_ns, point.locationz FROM point, usrstop LEFT JOIN usrstar ON usrstop.dataownercode = usrstar.dataownercode AND usrstop.userstopareacode = usrstar.userstopareacode WHERE usrstop.dataownercode = point.dataownercode AND usrstop.userstopcode = point.pointcode AND point.pointtype = 'SP' AND usrstop.userstoptype = 'PASSENGER' ORDER BY (((locationx_ew - (%(x)d))*(locationx_ew - (%(x)d)))+((locationy_ns - (%(y)d))*(locationy_ns - (%(y)d)))), usrstop.userstopareacode DESC, usrstop.town, usrstop.name, usrstop.userstopcode LIMIT %(maxitems)d;"""

KV1_STOPPLACE_QUAYS_SQL="""SELECT sp.id, sp.name, sp.description, sp.stopplacetype, sp.street, sp.town, sp.postalregion, q.dataownercode, q.publiccode, q.name, q.transportmode, q.longitude, q.latitude, q.altitude, q.x, q.y, q.description, q.boardinguse, q.aligtinguse, q.quaytype FROM stopplaces AS sp, quays AS q WHERE sp.id = %(stoparea)s AND sp.id = q.stopplace;"""
