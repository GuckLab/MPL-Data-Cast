from PyQt6 import QtCore, QtWidgets
import pathlib
import tempfile as tf

from mpl_data_cast.gui.main import MPLDataCast
from helper import retrieve_data

data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_setting_paths(qtbot, tmp_path):
    """Check that setting the input and output paths works."""
    mpldc = MPLDataCast()
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    path_out = tmp_path
    mpldc.widget_input.lineEdit_input.setText(str(path_in))
    mpldc.widget_output.lineEdit_output.setText(str(path_out))


def test_transfer_data(qtbot, monkeypatch):
    """Check that data is transfered when clicking on the button 'Transfer'."""
    mpldc = MPLDataCast()
    qtbot.add_widget(mpldc)
    path_in = data_path / "example_dir" / "calibration_beads_47.rtdc"
    tmp_dir = tf.TemporaryDirectory()
    path_out = pathlib.Path(tmp_dir.name)

    assert path_in.exists()
    # now insert the paths and simulate pressing 'enter', so that the
    # signal 'finishedEditing' is emitted.
    # mpldc.widget_input.lineEdit_input.setText(str(path_in))
    # qtbot.keyPress(mpldc.widget_input.lineEdit_input, QtCore.Qt.Key.Key_Enter)
    # mpldc.widget_output.lineEdit_output.setText(str(path_out.name))
    # qtbot.keyPress(mpldc.widget_output.lineEdit_output,
    #                QtCore.Qt.Key.Key_Enter)

    mpldc.widget_input.update_input_dir(path_in)
    mpldc.widget_output.update_output_dir(path_out)

    bt = mpldc.pushButton_transfer

    # Monkeypatch message box to always return OK
    monkeypatch.setattr(QtWidgets.QMessageBox,
                        "information",
                        lambda *args: QtWidgets.QMessageBox.StandardButton.Ok)
    qtbot.mouseClick(bt, QtCore.Qt.MouseButton.LeftButton)

    print(tmp_dir)
    assert path_out.exists()
    # assert (path_out / "calibration_beads_47.rtdc").exists()
    # tmp_dir.cleanup()
