import os
import sys
import argparse
import re

import pandas as pd

from opencmiss.zinc.context import Context
from opencmiss.zinc.field import FieldGroup
from opencmiss.utils.zinc.general import AbstractNodeDataObject
from opencmiss.utils.zinc.field import create_field_coordinates, find_or_create_field_group
from opencmiss.utils.zinc.general import create_node as create_zinc_node
from opencmiss.utils.zinc.general import ChangeManager

GROUPS = {'Epi': 'epicardium',
          'LVendo': 'endocardium of left ventricle',
          'RV_freewall': 'endocardium of right ventricle',
          'RV_septum': 'endocardium of right ventricle',
          'AV': 'root of aorta',
          'MV': 'root of mitral valve',
          'TV': 'root of triscupid valve',
          'PV': 'root of pulmonary valve'}

class CSVPoint(AbstractNodeDataObject):

    def __init__(self, x, y, z):
        super(CSVPoint, self).__init__(['coordinates'])
        self._x = x
        self._y = y
        self._z = z

    def get(self):
        return [self._x, self._y, self._z]

    def coordinates(self):
        return [self._x, self._y, self._z]

    def __repr__(self):
        return 'x="{0}" y="{1}" z="{2}"'.format(self._x, self._y, self._z)

def write_ex(file_name, data):
    context = Context("BiV Heart Data")
    region = context.getDefaultRegion()
    load(region, data)
    region.writeFile(file_name)


def load(region, data):
    field_module = region.getFieldmodule()
    create_field_coordinates(field_module)

    for surface, points in data.items():
        node_identifiers = create_nodes(field_module, points)
        create_group_nodes(field_module, surface, node_identifiers, node_set_name='datapoints')


def create_nodes(field_module, embedded_lists, node_set_name='datapoints'):
    node_identifiers = []
    for pt in embedded_lists:
        if isinstance(pt, list):
            node_ids = create_nodes(field_module, pt, node_set_name=node_set_name)
            node_identifiers.extend(node_ids)
        else:
            local_node_id = create_zinc_node(field_module, pt, node_set_name=node_set_name)
            node_identifiers.append(local_node_id)

    return node_identifiers


def create_group_nodes(field_module, group_name, node_ids, node_set_name='nodes'):
    with ChangeManager(field_module):
        group = find_or_create_field_group(field_module, name=group_name)
        group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)

        nodeset = field_module.findNodesetByName(node_set_name)
        node_group = group.getFieldNodeGroup(nodeset)
        if not node_group.isValid():
            node_group = group.createFieldNodeGroup(nodeset)

        nodeset_group = node_group.getNodesetGroup()
        for group_node_id in node_ids:
            node = nodeset.findNodeByIdentifier(group_node_id)
            nodeset_group.addNode(node)

class ProgramArguments(object):
    def __init__(self):
        self.input_csvs = None
        self.n_frames = None
        self.output_ex = None


def read_csv(files_path, n_frames):
    csv_data = {}
    if n_frames == 1:
        for file in os.listdir(files_path):
            points = []
            group_name = file.split('.')[0]
            if group_name in GROUPS.keys():
                data = pd.read_csv(os.path.join(files_path, file), sep=',')
                for pts in data.values:
                    points.append(_create_csv_point(pts))
                csv_data[GROUPS[group_name]] = points
    else:
        all_files = os.listdir(files_path)
        all_files.sort(key=lambda f: int(re.sub('\D', '', f)))
        current_frame = None
        for file in all_files:
            file_name = file.split('.')[0]
            group_name = file_name.split('_')[:-1]
            if isinstance(group_name, list) and len(group_name) > 1:
                group_name = '_'.join(group_name)
            else:
                group_name = group_name[-1]
            frame_number = file_name.split('_')[-1]
            if frame_number != current_frame:
                csv_data[frame_number] = {}
            points = []
            if group_name in GROUPS.keys():
                data = pd.read_csv(os.path.join(files_path, file), sep=',')
                for pts in data.values:
                    points.append(_create_csv_point(pts))
                csv_data[frame_number][GROUPS[group_name]] = points
            current_frame = frame_number

    return csv_data


def _create_csv_point(pts):
    return CSVPoint(float(pts[0]),
                    float(pts[1]),
                    float(pts[2]))


def main():
    args = parse_args()
    if os.path.exists(args.input_csvs):
        n_frames = int(args.n_frames)
        contents = read_csv(args.input_csvs, n_frames)
        if contents is None:
            sys.exit(-2)
        else:
            if n_frames > 1:
                for frame, data in contents.items():
                    if args.output_ex is None:
                        output_ex = os.path.join(args.input_csvs, 'combined_{}.ex'.format(frame))
                    else:
                        output_ex = args.output_ex
                    write_ex(output_ex, data)
            else:
                if args.output_ex is None:
                    output_ex = os.path.join(args.input_csvs, 'combined.ex')
                else:
                    output_ex = args.output_ex

                write_ex(output_ex, contents)

    else:
        sys.exit(-1)


def parse_args():
    parser = argparse.ArgumentParser(description="Transform CMI surface data files to ex format.")
    parser.add_argument("input_csvs", help="Location of the input csv files.")
    parser.add_argument("n_frames", help="Number of frames. "
                                         "[Defaults to 1.")
    parser.add_argument("--output-ex", help="Location of the output ex file. "
                                            "[defaults to the location of the input file if not set.]")

    program_arguments = ProgramArguments()
    parser.parse_args(namespace=program_arguments)

    return program_arguments


if __name__ == "__main__":
    main()
