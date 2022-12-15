"""basic tests"""
from mpl_data_cast.gui.main import MPLDataCast


def test_simple(qtbot):
    """Open the main window and close it again"""
    main_window = MPLDataCast()
    main_window.close()
