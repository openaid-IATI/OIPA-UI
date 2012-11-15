import os
from django.contrib.gis.utils.layermapping import LayerMapping
from models import WorldBorder

world_mapping = {
    'fips' : 'FIPS',
    'iso2' : 'ISO2',
    'iso3' : 'ISO3',
    'un' : 'UN',
    'name' : 'NAME',
    'area' : 'AREA',
    'pop2005' : 'POP2005',
    'region' : 'REGION',
    'subregion' : 'SUBREGION',
    'lon' : 'LON',
    'lat' : 'LAT',
    'mpoly' : 'MULTIPOLYGON',
}

world_shp_simple = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data/worldborders_simple/TM_WORLD_BORDERS_SIMPL-0.3.shp'))

def run(verbose=True):
    WorldBorder.objects.all().delete()
    lm = LayerMapping(WorldBorder, world_shp_simple, world_mapping,
                      transform=False, encoding='iso-8859-1', unique='name')

    lm.save(strict=True, verbose=verbose)
