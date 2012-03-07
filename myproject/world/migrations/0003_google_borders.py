# encoding: utf-8
from south.v2 import DataMigration
from django.contrib.gis.maps.google.overlays import GPolygon

class Migration(DataMigration):
    class NewGPolygon(GPolygon):
        def latlng_from_coords(self, coords):
            "Generates a JavaScript array of GLatLng objects for the given coordinates."
            return '[%s]' % ','.join(['new google.maps.LatLng(%s,%s)' % (y, x) for x, y in coords])
    
    def forwards(self, orm):
        for worldborder in orm.WorldBorder.objects.all():
            worldborder.google_border = '[%s]' % ','.join(unicode(self.NewGPolygon(subregion).points) for subregion in worldborder.mpoly)
            worldborder.save()

    def backwards(self, orm):
        for worldborder in orm.WorldBorder.objects.all():
            worldborder.google_border = ''
            worldborder.save()

    models = {
        'world.worldborder': {
            'Meta': {'object_name': 'WorldBorder'},
            'area': ('django.db.models.fields.IntegerField', [], {}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'google_border': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso2': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'mpoly': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'pop2005': ('django.db.models.fields.IntegerField', [], {}),
            'region': ('django.db.models.fields.IntegerField', [], {}),
            'subregion': ('django.db.models.fields.IntegerField', [], {}),
            'un': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['world']
    
