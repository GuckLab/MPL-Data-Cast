.. _sec_cli:

Command-line interface (CLI)
============================

The ``mpldc`` CLI gives you full access to the MPL-Data-Cast core functionalities.
This section documents the output of the different commands
(e.g. ``mpldc --help`` or ``mpldc cast --help``).


.. click:: mpl_data_cast.cli.cli:cli
   :prog: mpldc
   :nested: short


.. click:: mpl_data_cast.cli.cli:cast
   :prog: mpldc cast
   :nested: full


.. click:: mpl_data_cast.cli.cli:list_recipes
   :prog: mpldc list-recipes
   :nested: full