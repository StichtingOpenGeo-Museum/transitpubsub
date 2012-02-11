from osgeo import osr, ogr

rd = osr.SpatialReference()
rd.ImportFromProj4('+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812 +no_defs no_defs <>')

wgs84 = osr.SpatialReference()
wgs84.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

def wgs84_rd(lat, lon):
    ogr_geom = ogr.CreateGeometryFromWkt('POINT(%s %s)' % (lon, lat))
    ogr_geom.AssignSpatialReference(wgs84)
    ogr_geom.TransformTo(rd)
    return (ogr_geom.GetX(), ogr_geom.GetY())
