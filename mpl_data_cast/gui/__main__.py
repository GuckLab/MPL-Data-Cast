def main():
    import os
    import pkg_resources
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imdir = pkg_resources.resource_filename("mpl_data_cast", "img")

    from PyQt6 import QtGui
    from mpl_data_cast.gui import MPLDataCast

    # Set Application Icon
    icon_path = os.path.join(imdir, "mpldc_icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    window = MPLDataCast()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
