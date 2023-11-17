Introduction
============

Installation
------------

For Windows and macOS users, there are installers available at the
`release page <https://github.com/GuckLab/MPL-Data-Cast/releases>`_. The
Windows installer also includes the :ref:`command line interface (CLI) <sec_cli>`
``mpldc.exe``. You might want to add the installation directory to your Windows
PATH variable for conveniently using the CLI (see e.g.
`this guide <https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-2010/ee537574(v=office.14)>`_).


If you have Python installed, you can install MPL-Data-Cast with::

    pip install mpl_data_cast

The :ref:`Command-line interface <sec_cli>` is available via::

    mpldc
    # or
    python -m mpl_data_cast.cli

To start the GUI, run::

    mpldc-gui
    # or
    python -m mpl_data_cast.gui


Issue tracker
-------------

If you encounter bugs or have suggestions for improvement, open an issue on
`GitHub <https://github.com/GuckLab/MPL-Data-Cast/issues>`_.


Motivation
----------

If you do a lot of experiments, you have a lot of data. If you want to analyze
the data on a different computer, you have to make sure that the data are
transferred correctly to that computer. MPL-Data-Cast can help you with that
process and it also allows you to simplify the subsequent data analysis by
reformatting your raw input data. The main features of MPL-Data-Cast are:

- Copy a directory tree from a local file system to a network share (or any
  other mountable location) and verify that all files are copied correctly
  via comparison of `MD5 checksums <https://en.wikipedia.org/wiki/MD5#Applications>`_
- Convert your raw data to a file format that your data analysis pipeline
  understands (e.g. convert TIF files to
  `HDF5 <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ files) or
  repack/compress your input data
- Append additional meta data from your experiments that you were not able to
  set in your data acquisition software

MPL-Data-Cast is developed at the `Max Planck Institute for the Science of Light
<https://mpl.mpg.de/>`_, where we have a lot of such data. For us, it
addresses several data management issues:

- When you copy a directory tree containing large (~20GB) files from a local
  Windows machine to a remote network share using the built-in File Explorer,
  sometimes the files were corrupted (e.g. HDF5 files could not be opened
  anymore).
- When you deal with
  `RT-DC <https://mpl.mpg.de/divisions/guck-division/methods/deformability-cytometry>`_
  data, you always have to (losslessly) compress the data (or at least
  repack the file so that a dataset is not scattered over the entire HDF5 file)
  to properly work with it.
- We also have very basic data acquisition pipelines that work with
  `Micro-Manager <https://github.com/micro-manager/micro-manager>`_ which
  outputs TIF files and metadata files. We needed to merge these files into
  properly formatted (including metadata) HDF5 files.


Design
------

MPL-Data-Cast is a Python library with a command-line interface (CLI) and
a very simple GUI on top that lets you apply a "recipe" to data files. A
recipe defines how your acquisition data is transformed into the final raw data
for your analysis pipeline. You can define your own recipes or use the recipes
that come with MPL-Data-Cast.

See also:

- :ref:`Command-line interface <sec_cli>`
- :ref:`Graphical user interface <sec_gui>`

Good to know
------------

- MPL-Data-Cast does not create a directory with the same name as the input
  directory in the output directory, it copies the content of the input
  directory into the output directory. That means that you have to be careful when
  entering the output path, or otherwise you might end up mixing up data.

- Right now, it is not possible to copy only selected files or subfolders from
  a given directory, you can only transfer complete directories.
