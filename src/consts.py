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
