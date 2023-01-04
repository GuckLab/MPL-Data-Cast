def main(splash=True):
    import os
    import pkg_resources
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imdir = pkg_resources.resource_filename("mpl_data_cast", "img")

    if splash:
        from PyQt6.QtWidgets import QSplashScreen
        from PyQt6.QtGui import QPixmap
        splash_path = os.path.join(imdir, "splash.png")
        splash_pix = QPixmap(splash_path)
        splash = QSplashScreen(splash_pix)
        splash.setMask(splash_pix.mask())
        splash.show()

    from PyQt6 import QtGui
    from mpl_data_cast.gui import MPLDataCast

    # Set Application Icon
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    window = MPLDataCast()

    if splash:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
