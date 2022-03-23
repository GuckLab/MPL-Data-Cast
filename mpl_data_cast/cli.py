import pathlib

import click

from . import recipe as mpldc_recipe


@click.group()
def cli():
    pass


@cli.command(short_help="List available recipes")
def list_recipes():
    recipes = mpldc_recipe.get_available_recipe_names()
    col1len = max(len(r) for r in recipes) + 2
    for rec in recipes:
        cls = mpldc_recipe.map_recipe_name_to_class(rec)
        col1 = rec + (" " * (col1len - len(rec)))
        doc = cls.__doc__.split("\n")[0]
        click.secho(f"{col1} {doc}")


@cli.command(short_help="Convert and copy experimental data")
@click.argument("path_raw",
                type=click.Path(exists=True,
                                file_okay=False,
                                resolve_path=True,
                                path_type=pathlib.Path))
@click.argument("path_target",
                type=click.Path(file_okay=False,
                                writable=True,
                                resolve_path=True,
                                path_type=pathlib.Path))
@click.option("--recipe", type=str, default="CatchAll",
              help="specifies recipe to use, e.g. 'OAH'")
def cast(path_raw, path_target, recipe="guess"):
    """Cast data from a source directory to a target directory

    This will convert all data under the tree in PATH_RAW and
    copy them to PATH_TARGET.
    """
    # get the actual class
    pcls = mpldc_recipe.map_recipe_name_to_class(recipe)

    pl = pcls(path_raw, path_target)
    pl.cast()
