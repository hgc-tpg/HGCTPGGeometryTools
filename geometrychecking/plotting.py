#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click

import os
import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
from geometrychecking import data, geometry

def plot_invalid_tcs(modules, arrays, output_file):
    with click.progressbar(modules.items()) as bar:
        fig = plt.figure(dpi=150)
        for layer,mods in bar:
            tcs = arrays[layer]['triggercells']
            error_tcs = tcs[tcs.errorbits>0]
            ax = fig.add_subplot()
            for module in mods:
                modid = module['modid']
                mod_poly = module['shape']
                errorbits = module['errors']
                color = 'red' if data.check_error(errorbits, data.errortypes.InvalidTCInModule) else 'green'
                plot_polygon(mod_poly, ax=ax, color=color, add_points=False)
                ax.scatter(error_tcs.x, error_tcs.y, s=2, color='darkred')
    plt.plot()
    plt.savefig(output_file)

@click.command()
@click.option('--geometry', 'geometry_name', required=True, help='Trigger geometry name (name of the geometry ROOT file without the .root extension)')
def cli(geometry_name):
    click.echo('> Reading geometry files')
    arrays = geometry.from_parquet(f'resources/{geometry_name}')
    modules = geometry.from_json(f'resources/{geometry_name}/geojson')
    click.echo('> Plotting invalid TCs')
    os.makedirs(f'results/{geometry_name}/figs', exist_ok=True)
    plot_invalid_tcs(modules, arrays, f"results/{geometry_name}/figs/invalid_tcs.png")
    #  with click.progressbar(length=len(modules)) as bar:
        #  for layer,mods in modules.items():
            #  plot_invalid_tcs(mods, arrays[layer]['triggercells'], f"results/{geometry_name}/figs/invalid_tcs_layer{layer}.png")
            #  bar.update(1)

