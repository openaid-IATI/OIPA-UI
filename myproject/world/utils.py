from django.contrib.gis.maps.google.overlays import GPolygon

class NewGPolygon(GPolygon):
    def latlng_from_coords(self, coords):
        "Generates a JavaScript array of GLatLng objects for the given coordinates."
        return '[%s]' % ','.join(['new google.maps.LatLng(%s,%s)' % (y, x) for x, y in coords])