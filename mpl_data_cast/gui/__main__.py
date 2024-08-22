def main():
    from importlib import resources
    import logging
    import sys
    from PyQt6 import QtWidgets, QtCore, QtGui

    from .main import MPLDataCast
    from .._version import version

    logging.basicConfig(
        level=logging.DEBUG if version.count("post") else logging.INFO,
        format="%(asctime)s %(levelname)s %(processName)s/%(threadName)s "
               + "in %(name)s: %(message)s",
        datefmt='%H:%M:%S')

    app = QtWidgets.QApplication(sys.argv)
    ref_ico = resources.files("mpl_data_cast.gui.img") / "mpldc_icon.png"
    with resources.as_file(ref_ico) as path_icon:
        app.setWindowIcon(QtGui.QIcon(str(path_icon)))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.c()))

    window = MPLDataCast()  # noqa: F841

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
