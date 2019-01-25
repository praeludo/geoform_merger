from dataclasses import dataclass, field, asdict
from typing import List, Dict
import geojson
import json
import shapely.geometry

@dataclass
class EPCI:
    code_epci: str
    annee: str
    epci: str
    code_region: int = field(repr=False)
    code_departement: int = field(repr=False)
    region: str = field(repr=False)
    departement: str = field(repr=False)
    
    def register(self, member):
        try:
            self.members.append(member)
        except AttributeError:
            self.members = [member]
        
    @property
    def polygon(self):
        shape = lambda x: shapely.geometry.asShape(x)
        polygon = shape(self.members[0]['geometry'])
        for member in self.members[1:]:
            polygon = polygon.union(shape(member['geometry']))
        return polygon

    @property
    def feature(self):
        return geojson.Feature(geometry=self.polygon,
                               properties=asdict(self))

@dataclass
class EPCIGroup:
    epcis: Dict[str, EPCI] = field(default_factory=dict)
    
    def register(self, epci):
        self.epcis[str(epci)] = epci
    
    @property
    def feature_collection(self):
        return geojson.FeatureCollection([epci.feature for epci in self.epcis.values()])

class EPCIGroupGeoJSON(EPCIGroup):
    
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        super().__init__()

    def load(self):
        with open(self.input_file, 'r') as input_file:
            features = json.load(input_file)
        for feature in features['features']:
            epci = EPCI(**{k: v for k, v in feature['properties'].items() 
                           if k not in ('commune', 'code_commune', 'geo_point_2d')})
            
            if not self.epcis.get(str(epci)):
                self.register(epci)
            else:
                epci = self.epcis.get(str(epci))
            epci.register(feature)
    
    def save(self):
        with open(self.output_file, 'w') as output_file:
            geojson.dump(self.feature_collection, output_file)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file',
                        help='Path to GeoJSON file containing forms to merge',
                        required=True)
    parser.add_argument('-o', '--output_file',
                        help='Path to save result',
                        required=True)
    args = vars(parser.parse_args())

    geoform_merger = EPCIGroupGeoJSON(args['input_file'], args['output_file'])
    geoform_merger.load()
    geoform_merger.save()
