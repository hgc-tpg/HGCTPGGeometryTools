#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import shapely
import awkward as ak
import click
from shapely.geometry import Polygon, MultiPolygon
import shapely

def polygon_from_cell(cell):
    nb_corners = len(cell.corners_x/2)
    corners = [(x,y) for x,y in zip(cell.corners_x[:nb_corners], cell.corners_y[0:nb_corners])]
    return Polygon(corners)

def union_polygons(polygons, use_buffer=False):
    if use_buffer:
        ## inflate polygons to ensure the union is a single Polygon
        ## in case they are almost touching each other 
        ## Useful in order to get the exact union outer shape instead of a convex approximation 
        margin = polygons[0].length/1000.
        for polygon in polygons:
            margin = min(margin, polygon.length/1000.) 
        for i,polygon in enumerate(polygons):
            polygons[i] = polygon.buffer(margin)
    union_geom = shapely.unary_union(polygons)
    if use_buffer:
        for i,polygon in enumerate(polygons):
            polygons[i] = polygon.buffer(-margin)
    # If the union is a single polygon
    if isinstance(union_geom, Polygon):
        if use_buffer:
            return Polygon(union_geom.buffer(-margin).exterior)
        else:
            return Polygon(union_geom.exterior)
    # If the union is a MultiPolygon, take the outer hull
    elif isinstance(union_geom, MultiPolygon):
        return union_geom.convex_hull
    else:
        raise ValueError("Unexpected geometry type")



def module_shapes_and_errors(cells_by_module, array_modules):
    modules = {}
    for module in cells_by_module:
        modid = module[0].modid
        subdet = module[0].subdet
        cell_errors = {}
        polygons = []
        for cell in module:
            if cell.errorbits!=0: cell_errors[cell.id] = cell.errorbits
            polygons.append(polygon_from_cell(cell))
        mod_poly = union_polygons(polygons)
        module_data = array_modules[array_modules.id==modid][0]
        errorbits = module_data.errorbits
        disconnected = module_data.disconnected
        modules[modid] = {'type': 'ceh' if subdet==10 else 'cee', 'disconnected':disconnected,'shape':mod_poly, 'errors':errorbits, 'cellerrors':cell_errors}
    return modules

def from_parquet(input_directory):
    arrays = {}
    objects = ['cells', 'triggercells', 'modules', 'cells_by_module']
    for subdet in ['cee','ceh']:
        arrays[subdet] = {}
        if subdet=='cee': maxlayer=26
        elif subdet=='ceh': maxlayer=21
        layers = range(1,maxlayer+1)
        for layer in layers:
            arrays[subdet][layer] = {}
            for obj in objects:
                arrays[subdet][layer][obj] = ak.from_parquet(f"{input_directory}/{subdet}_layer{layer}/{obj}.parquet")
    return arrays

def to_json(modules, output_file):
    modules_list = []
    for modid,module in modules.items():
        geojson_dict = json.loads(shapely.to_geojson(module['shape']))
        modules_list.append({'modid':int(modid), 'type':module['type'], 'disconnected':int(module['disconnected']), 'shape':geojson_dict, 'errors':int(module['errors'])})
    modules_json = json.dumps(modules_list)
    with open(output_file, 'w') as f:
        f.write(modules_json)
        
def from_json(input_directory):
    modules = {}
    for subdet in ['cee','ceh']:
        modules[subdet] = {}
        if subdet=='cee': maxlayer=26
        elif subdet=='ceh': maxlayer=21
        layers = range(1,maxlayer+1)
        for layer in layers:
            with open(f'{input_directory}/{subdet}_layer{layer}.json', 'r') as f:
                modules[subdet][layer] = json.load(f)
                for module in modules[subdet][layer]:
                    module['shape'] = shapely.from_geojson(json.dumps(module['shape']))
    return modules


@click.command()
@click.option('--geometry',
              'geometry_name',
              required=True,
              help='Trigger geometry name (name of the geometry ROOT file without the .root extension)'
              )
def cli(geometry_name):
    click.echo('> Reading geometry Parquet files')
    arrays = from_parquet(f'resources/{geometry_name}')
    os.makedirs(f'resources/{geometry_name}/geojson', exist_ok=True)
    for subdet in ['cee', 'ceh']:
        if subdet=='cee': maxlayer=26
        elif subdet=='ceh': maxlayer=21
        layers = range(1,maxlayer+1)
        click.echo(f'> Building {subdet} Shapely polygons')
        with click.progressbar(layers) as bar:
            for layer in bar:
                modules = module_shapes_and_errors(arrays[subdet][layer]['cells_by_module'], arrays[subdet][layer]['modules'])
                to_json(modules, f'resources/{geometry_name}/geojson/{subdet}_layer{layer}.json')


