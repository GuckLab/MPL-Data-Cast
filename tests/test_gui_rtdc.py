from PyQt6 import QtCore, QtTest, QtWidgets
import pathlib
import tempfile as tf
import shutil

from mpl_data_cast.gui.main import MPLDataCast
from helper import retrieve_data

data_path = pathlib.Path(__file__).resolve().parent / "data"


def test_setting_paths(qtbot, tmp_path):
    """Check that setting the input and output paths works."""
    mw = MPLDataCast()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    QtTest.QTest.qWait(100)
    path_in = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    mw.widget_input.lineEdit_dir.setText(str(path_in))
    mw.widget_output.lineEdit_dir.setText(str(tmp_path))
    mw.widget_input.update_tree_dir_from_lineedit()
    mw.widget_output.update_tree_dir_from_lineedit()
    assert str(mw.widget_output.path) == str(tmp_path)
    assert mw.widget_input.p_tree.tree_depth == 1
    assert mw.widget_output.p_tree.tree_depth == 1
    mw.close()
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)


def test_transfer_data_simple(qtbot, tmp_path, monkeypatch):
    """Check that data is transfered when clicking on the button 'Transfer'."""
    mw = MPLDataCast()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    QtTest.QTest.qWait(100)

    data = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    test_file = data / "M001_data.rtdc"
    test_file_dst = tmp_path / "M001_data.rtdc"
    shutil.copy(test_file, test_file_dst)
    tmp_dir = tf.TemporaryDirectory()
    path_out = pathlib.Path(tmp_dir.name)
    assert tmp_path.exists()
    assert path_out.exists()

    mw.widget_input.update_tree_dir(tmp_path)
    mw.widget_output.update_tree_dir(path_out)

    bt = mw.pushButton_transfer

    # Monkeypatch message box to always return OK
    monkeypatch.setattr(QtWidgets.QMessageBox,
                        "information",
                        lambda *args: QtWidgets.QMessageBox.StandardButton.Ok)
    qtbot.mouseClick(bt, QtCore.Qt.MouseButton.LeftButton)

    assert (path_out / "M001_data.rtdc").exists()
    tmp_dir.cleanup()
    mw.close()
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)


def test_transfer_data_advanced(qtbot, tmp_path, monkeypatch):
    """Check that data is transfered when clicking on the button 'Transfer'.
    Now includes subdirectories"""
    mw = MPLDataCast()
    qtbot.addWidget(mw)
    QtWidgets.QApplication.setActiveWindow(mw)
    QtTest.QTest.qWait(100)

    mw.settings.clear()

    data = retrieve_data("rcp_rtdc_mask-contour_2018.zip")
    test_file = data / "M001_data.rtdc"
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

    mw.widget_input.update_tree_dir(path_in)
    mw.widget_output.update_tree_dir(path_out)
    assert mw.widget_output.p_tree.tree_depth == 1

    bt = mw.pushButton_transfer

    # Monkeypatch message box to always return OK
    monkeypatch.setattr(QtWidgets.QMessageBox,
                        "information",
                        lambda *args: QtWidgets.QMessageBox.StandardButton.Ok)
    qtbot.mouseClick(bt, QtCore.Qt.MouseButton.LeftButton)

    assert tmp_file1.exists()
    assert tmp_file2.exists()
    assert mw.widget_output.p_tree.tree_depth == 3
    assert mw.widget_input.treeWidget.columnCount() == 4
    assert mw.widget_output.treeWidget.columnCount() == 4
    mw.close()
    QtTest.QTest.qWait(100)
    QtWidgets.QApplication.processEvents(
        QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 5000)
