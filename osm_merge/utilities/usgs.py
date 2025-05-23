#!/usr/bin/python3

# Copyright (c) 2021, 2022, 2023, 2024, 2025 OpenStreetMap US
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
import argparse
import logging
import sys
import os
import re
from sys import argv
from osm_merge.osmfile import OsmFile
from progress.bar import Bar, PixelBar
from osm_merge.yamlfile import YamlFile
import geojson
from geojson import Feature, FeatureCollection, load, LineString
import osm_merge as om
rootdir = om.__path__[0]

# Instantiate logger
log = logging.getLogger(__name__)

# https://wiki.openstreetmap.org/wiki/United_States_roads_tagging#Tagging_Forest_Roads

class USGS(object):
    def __init__(self,
                 dataspec: str = None,
                 yamlspec: str = "utilities/usgs.yaml",
                 ):
        """
        This class processes the dataset.

        Args:
            dataspec (str): The input data to convert
            yamlspec (str): The YAML config file for converting data

        Returns:
            (LocalRoads): An instance of this class
        """
        self.file = None
        if dataspec is not None:
            self.file = open(dataspec, "r")

        yaml = f"{rootdir}/{yamlspec}"
        if not os.path.exists(yaml):
            log.error(f"{yaml} does not exist!")
            quit()

        file = open(yaml, "r")
        self.yaml = YamlFile(f"{yaml}")

    def convert(self,
                state: str,
                filespec: str = None,
                ) -> list:
        """
        Convert the USGS topographical dataset to something that can
        be conflated. The dataset schema is pretty ugly, duplicate
        field names, abbreviations, etc... plus a shapefile truncates
        the field names.

        Args:
            filespec (str): The input dataset file
            state (str): The 2 letter state abbreviation

        """
        # FIXME: read in the whole file for now
        if filespec is not None:
            file = open(filespec, "r")
        else:
            file = self.file
        data = geojson.load(file)

        config = self.yaml.getEntries()
        highways = list()
        spin = Bar('Processing...', max=len(data['features']))
        for entry in data["features"]:
            geom = entry["geometry"]
            if geom is None or not geom["type"]:
                continue
            # We don't care about POIs for now
            if geom["type"] == "Point":
                continue
            props = dict()
            spin.next()
            operator = str()
            for key, value in entry["properties"].items():
                # Many fields have no value
                if not value:
                    continue
                # if len(props) > 0:
                #     print(f"\tFIXME2: {props}")
                if key in config["tags"]["access"]:
                    if type(config["tags"]["access"][key]) == str:
                        # breakpoint()
                        keyword = config["tags"]["access"][key]
                    elif type(config["tags"]["access"][key]) == dict:
                        if len(config["tags"]["access"][key]) == 0:
                            if value == "Y":
                                props[key] = "designated"
                    continue
                if key not in config["tags"]:
                    continue

                # print(f"FIXME: {key} = {value}")
                if key == "name":
                    # Look for USFS reference numbers
                    pat = re.compile("[0-9]+[a-z]*")
                    # Look for USGS reference numbers
                    if re.match(pat, value.lower()) is not None:
                        # Common roads like "2nd Street" all have a space
                        if value.find(' ') > 0:
                            newvalue = str()
                            for word in value.split():
                                # Fix some common abbreviations
                                abbrevs = config["abbreviations"]
                                if word in abbrevs:
                                    newvalue += abbrevs[word]
                                else:
                                    newvalue += word
                                    newvalue += ''
                            props["name"] = f"{newvalue.title()} Road"
                        else:
                            # breakpoint()
                            props["ref"] = f"{value.upper()}"
                    elif "County Road" in value:
                        props["ref"] = value.replace("County Road", "CR")
                    else:
                        props["name"] = f"{value.title()} Road"

                elif config["tags"][key] == "ref":
                    # breakpoint()
                    props["ref"] = value

                elif config["tags"][key] == "operator":
                    # breakpoint()
                    if value not in config["tags"]["operator"]:
                        break
                    if "ref" in props:
                        source = config["tags"]["source"][value]
                        prefix = config["tags"]["prefix"][value]
                        props[f"ref:{source}"] = f"{prefix} {props["ref"]}"
                        del props["ref"]
                    props["operator"] = config["tags"]["operator"][value]

                # We don't want all the non highway data
                # elif config["tags"][key] == "source":
                elif config["tags"][key] == "source":
                    breakpoint()
                    if value not in config["tags"][source]:
                        print(f"Dropping source {value}")
                        break
                    else:
                        breakpoint()
                        if "ref" in props:
                            prefix = config["tags"]["source"][key]
                            if prefix == "blm":
                                props["ref:blm"] = f"BLM {props["ref"]}"
                            elif prefix == "usgs":
                                props["ref:usgs"] = f"FR {props["ref"]}"
                            elif prefix == "nps":
                                props["ref:nps"] = f"NPS {props["ref"]}"
                            del props["ref"]

            if len(props) > 0:
                highways.append(Feature(geometry=geom, properties=props))

        return FeatureCollection(highways)

def main():
    """This main function lets this class be run standalone by a bash script"""
    parser = argparse.ArgumentParser(
        prog="usgs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This program converts USGS datasets into OSM tagging",
        epilog="""

    For Example: 
        mvum.py -v -c -i WY_RoadsMVUM.geojson
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-i", "--infile", required=True, help="Top-level input directory")
    parser.add_argument("-c", "--convert", default=True, action="store_true", help="Convert USGS feature to OSM feature")
    parser.add_argument("-s", "--state", default="CO", help="The state the dataset is in")
    parser.add_argument("-o", "--outfile", default="out.geojson", help="Output file")

    args = parser.parse_args()

    # if verbose, dump to the terminal.
    log_level = os.getenv("LOG_LEVEL", default="INFO")
    if args.verbose is not None:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format=("%(asctime)s.%(msecs)03d [%(levelname)s] " "%(name)s | %(funcName)s:%(lineno)d | %(message)s"),
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    usgs = USGS()
    if args.convert and args.convert:
        data = usgs.convert(args.state, args.infile)

        file = open(args.outfile, "w")
        geojson.dump(data, file, indent=4)
        log.info(f"Wrote {args.outfile}")
        
if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
