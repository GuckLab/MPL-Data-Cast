import inspect
import pathlib

import click

from . import recipe as mpldc_recipe


@click.group()
def cli():
    pass


@cli.command(short_help="List available recipes that can be used in the "
                        + "``mpldc cast`` subcommand")
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
@click.option("-r", "--recipe", type=str, default="CatchAll",
              help="specifies recipe to use, defaults to 'CatchAll'; see the "
                   + "``mpldc list-recipes`` subcommand for more options")
@click.option("-o", "--options", type=str, default=None,
              help="comma-separated keyword arguments passed to the recipe's "
                   + "`convert_dataset` method, e.g. "
                   + "wavelength=984e-9,pixel_size=1.2e-6")
def cast(path_raw, path_target, recipe="CatchAll", options=None):
    """Cast data from a source directory to a target directory

    This will convert all data under the tree in PATH_RAW and
    copy them to PATH_TARGET.
    """
    # get the actual class
    rcls = mpldc_recipe.map_recipe_name_to_class(recipe)
    # instantiate the class
    rp = rcls(path_raw, path_target)

    # get types of the recipes
    kwarg_dtypes = {}
    sig = inspect.signature(rp.convert_dataset)
    for p in sig.parameters:
        if p in ["path_list", "temp_path"]:
            continue
        kwarg_dtypes[p] = sig.parameters[p].annotation

    # parse custom parameters from `options`
    kwargs = {}
    if options:
        entries = options.split(",")
        for entr in entries:
            if "=" not in entr:
                raise ValueError(f"Invalid option string: '{entr}'!")
            key, valuestr = [en.strip() for en in entr.split("=", 1)]
            if key not in kwarg_dtypes:
                raise ValueError("Recipe `recipe` does not implement option "
                                 + f"'{key}'; available options: "
                                 + f"{sorted(kwarg_dtypes.keys())}")
            kwargs[key] = kwarg_dtypes[key](valuestr)
    rp.cast(**kwargs)
