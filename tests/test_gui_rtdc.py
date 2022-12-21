from PyQt6 import QtCore, QtWidgets
import pathlib
import tempfile as tf
import shutil

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


def test_transfer_data_simple(qtbot, monkeypatch):
    """Check that data is transfered when clicking on the button 'Transfer'."""
    mpldc = MPLDataCast()
    qtbot.add_widget(mpldc)
    path_in = data_path / "example_dir"
    tmp_dir = tf.TemporaryDirectory()
    path_out = pathlib.Path(tmp_dir.name)
    assert path_in.exists()
    assert path_out.exists()

    mpldc.widget_input.update_input_dir(path_in)
    mpldc.widget_output.update_output_dir(path_out)

    bt = mpldc.pushButton_transfer

    # Monkeypatch message box to always return OK
    monkeypatch.setattr(QtWidgets.QMessageBox,
                        "information",
                        lambda *args: QtWidgets.QMessageBox.StandardButton.Ok)
    qtbot.mouseClick(bt, QtCore.Qt.MouseButton.LeftButton)

    assert (path_out / "calibration_beads_47.rtdc").exists()
    tmp_dir.cleanup()


def test_transfer_data_advanced(qtbot, tmp_path, monkeypatch):
    """Check that data is transfered when clicking on the button 'Transfer'.
    Now includes subdirectories"""
    mpldc = MPLDataCast()
    mpldc.settings.clear()
    qtbot.add_widget(mpldc)
    test_file = data_path / "example_dir" / "calibration_beads_47.rtdc"
    path_in = tf.mkdtemp(prefix="input", dir=tmp_path)
    path_in = pathlib.Path(path_in)
    path_out = tf.mkdtemp(prefix="output", dir=tmp_path)
    path_out = pathlib.Path(path_out)

    tmp_dir1 = pathlib.Path(tf.mkdtemp(dir=str(path_in)))
    tmp_dir2 = pathlib.Path(tf.mkdtemp(dir=str(tmp_dir1)))

    tmp_file1 = tmp_dir1 / "m1.rtdc"
    tmp_file2 = tmp_dir2 / "m2.rtdc"
    shutil.copy(test_file, tmp_file1)
    shutil.copy(test_file, tmp_file2)

    assert path_in.exists()
    assert path_out.exists()
    assert tmp_file1.exists()
    assert tmp_file2.exists()
    assert len(list(path_out.rglob("*.rtdc"))) == 0

    mpldc.widget_input.update_input_dir(path_in)
    mpldc.widget_output.update_output_dir(path_out)
    assert mpldc.widget_output.p_tree.tree_depth == 1

    bt = mpldc.pushButton_transfer

    # Monkeypatch message box to always return OK
    monkeypatch.setattr(QtWidgets.QMessageBox,
                        "information",
                        lambda *args: QtWidgets.QMessageBox.StandardButton.Ok)
    qtbot.mouseClick(bt, QtCore.Qt.MouseButton.LeftButton)

    assert tmp_file1.exists()
    assert tmp_file2.exists()
    assert mpldc.widget_output.p_tree.tree_depth == 3
    assert mpldc.widget_input.treeWidget_input.columnCount() == 4
    assert mpldc.widget_output.treeWidget_output.columnCount() == 4
