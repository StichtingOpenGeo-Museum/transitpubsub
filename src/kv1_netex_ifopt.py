from osgeo import osr, ogr
from xml.sax.saxutils import escape

src_string = '+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812 +no_defs no_defs <>'
dst_string = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

src = osr.SpatialReference()
src.ImportFromProj4(src_string)

dst = osr.SpatialReference()
dst.ImportFromProj4(dst_string)

modality_stopplace = { 'bus': 'onstreetBus' }
modality_quay = { 'bus': 'bus' }
modality_quaytype = { 'bus': 'busStop' }

def netex_quay(arguments):
    xml_quay = """          <netex:Quay xmlns:netex="http://www.netex.org.uk/netex" xmlns:gml="http://www.opengis.net/gml" id="%(dataownercode)s:%(publiccode)s">
            <netex:PublicCode>%(publiccode)s</netex:PublicCode>
            <netex:Name>%(name)s</netex:Name>
            <netex:TransportMode>%(transportmode)s</netex:TransportMode>
            <netex:Centroid>
              <netex:Location>
                <netex:Longitude>%(longitude)s</netex:Longitude>
                <netex:Latitude>%(latitude)s</netex:Latitude>
                <netex:Altitude>%(altitude)s</netex:Altitude>
                <gml:pos srsName="http://www.opengis.net/def/crs/EPSG/0/28992" srsDimension="2">%(x)s %(y)s</gml:pos>
              </netex:Location>
            </netex:Centroid>
            <netex:Description>%(description)s</netex:Description>
            <netex:BoardingUse>%(boardinguse)s</netex:BoardingUse>
            <netex:AlightingUse>%(alightinguse)s</netex:AlightingUse>
            <netex:QuayType>%(quaytype)s</netex:QuayType>
          </netex:Quay>
"""

    ogr_geom = ogr.CreateGeometryFromWkt('POINT(%(x)s %(y)s)' % arguments)
    ogr_geom.AssignSpatialReference(src)
    ogr_geom.TransformTo(dst)

    arguments['longitude'] = ogr_geom.GetX()
    arguments['latitude'] = ogr_geom.GetY()

    if arguments['altitude'] is None:
        arguments['altitude'] = ''
    
    return xml_quay % arguments

def netex_stopplace(arguments):
    xml_stopplace = """      <netex:StopPlace xmlns="http://www.ifopt.org.uk/ifopt" id="openOV:%(stopplaceid)s" modification="new" status="active" version="1.0">
        <netex:Name>%(name)s</netex:Name>
        <netex:Description>%(description)s</netex:Description>
        <netex:StopPlaceType>%(stopplacetype)s</netex:StopPlaceType>
        <netex:PostalAddress created="" changed="">
          <netex:Street>%(street)s</netex:Street>
          <netex:Town>%(town)s</netex:Town>
          <netex:PostalRegion>%(postalregion)s</netex:PostalRegion>
        </netex:PostalAddress>
        <netex:Quays>
%(quays)s        </netex:Quays>
      </netex:StopPlace>
"""

    return xml_stopplace % arguments
