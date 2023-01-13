"""basic tests"""
from PyQt6 import QtWidgets
from unittest import mock

import mpl_data_cast
from mpl_data_cast.gui.main import MPLDataCast
from mpl_data_cast.gui.widget_output import OutputWidget
from mpl_data_cast.gui.widget_input import InputWidget


def test_simple(qtbot):
    """Open the main window and close it again, check that some basic
    attributes exist."""
    mw = MPLDataCast()
    assert isinstance(mw.widget_input, InputWidget)
    assert isinstance(mw.widget_output, OutputWidget)
    assert isinstance(mw.pushButton_transfer, QtWidgets.QPushButton)
    mw.close()


def test_on_action_about(qtbot):
    """Check that the 'About' menu works."""
    with mock.patch("PyQt6.QtWidgets.QMessageBox.about") as mock_about:
        mw = MPLDataCast()
        mw.on_action_about()
        mw.close()

        assert mock_about.call_args.args[1] == \
               f"MPL-Data-Cast {mpl_data_cast.__version__}"
        assert "MPL-Data-Cast" in mock_about.call_args.args[2]
