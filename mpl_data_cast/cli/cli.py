import inspect
import pathlib
import time
from typing import List

import click

from .. import recipe as mpldc_recipe


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
        doc = cls.__doc__.strip().split("\n")[0]
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
    click.secho(f"Using recipe {recipe}.", bold=True)
    with CLICallback() as path_callback:
        result = rp.cast(path_callback=path_callback, **kwargs)
    if result["success"]:
        click.secho("Success!", bold=True)
    else:
        click.secho("Errors encountered for the following files: ", bold=True)
        for path, _ in result["errors"]:
            click.echo(f" - {path}")
        if click.confirm('Should I dump the tracebacks to "mpldc-dump.txt"?'):
            text = ""
            for path, tb in result["errors"]:
                text += f"PATH {path}:\n{tb}\n\n"
            pathlib.Path("mpldc-dump.txt").write_text(text)


class CLICallback:
    def __init__(self):
        self.counter = 0
        self.size = 0
        self.prev_len = 0
        self.time_start = time.monotonic()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        rate = self.get_rate()
        self.print(f"Processed {self.counter} files (~{rate:.1f} MB/s).")
        print("")

    def __call__(self, path_list: List[pathlib.Path]) -> None:
        self.counter += 1
        name = click.format_filename(path_list[0], shorten=True)
        message = f"Processing file {self.counter}: {name}"
        rate = self.get_rate()
        if rate:
            message += f" ({rate:.1f}MB/s)"
        self.size += sum([pp.stat().st_size for pp in path_list])
        self.print(message)

    def get_rate(self) -> float:
        curtime = time.monotonic()
        if curtime > self.time_start:
            return self.size / 1024**2 / (curtime - self.time_start)
        else:
            return 0

    def print(self, message: str) -> None:
        print(" " * self.prev_len, end="\r")
        print(message, end="\r")
        self.prev_len = len(message)
