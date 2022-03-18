import pathlib

import click

from .recipe import Recipe, guess_recipe


@click.group()
def cli():
    pass


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
@click.option("--recipe", type=str, default="guess",
              help="specifies recipe to use, e.g. 'OffAxisHolographyRecipe'")
def cast(path_raw, path_target, recipe="guess"):
    """Cast data from a source directory to a target directory

    This will convert all data under the tree in PATH_RAW and
    copy them to PATH_TARGET.
    """
    if recipe == "guess":
        recipe = guess_recipe(path_raw).__name__
        click.secho(f"Using recipe '{recipe}'", bold=True)

    # get the actual class
    for cls in Recipe.__subclasses__():
        if cls.__name__ == recipe:
            pcls = cls
            break
    else:
        raise ValueError(f"Could not find recipe {recipe}")

    pl = pcls(path_raw, path_target)
    pl.cast()
