from importlib import resources
import pathlib
import time
import threading
from typing import Literal

from PyQt6 import QtWidgets, QtCore, QtGui, uic

from ..recipe import map_recipe_name_to_class
from ..util import is_dir_writable


class TreeObjectCounter(threading.Thread):
    """Thread running in the background, counting objects and their size"""
    def __init__(self, *args, **kwargs):
        super(TreeObjectCounter, self).__init__(*args, **kwargs)
        self.daemon = True
        self.recipe = None
        self.path = None
        self.num_objects = 0
        self.size_objects = 0
        self.must_break = False
        self.is_counting = False
        self.has_counted = False

    def run(self):
        recipe = self.recipe
        path = self.path
        while True:
            if self.must_break:
                # user requested we quit
                break
            elif recipe is None or path is None:
                # not initialized yet
                recipe = self.recipe
                path = self.path
            elif (self.recipe is None
                  or self.path is None
                  or self.recipe != recipe
                    or self.path != path):
                # reset
                self.num_objects = 0
                self.size_objects = 0
                self.has_counted = False
                recipe = self.recipe
                path = self.path
            elif self.num_objects or self.has_counted:
                # already counted
                pass
            else:
                # start crawling the directory tree
                self.is_counting = True
                self.has_counted = False
                try:
                    rcp = recipe(path, path)
                except BaseException:
                    pass
                else:
                    tree_iterator = rcp.get_raw_data_iterator()
                    while True:
                        # check whether we have to abort
                        if (self.must_break
                                or recipe != self.recipe or path != self.path):
                            self.num_objects = 0
                            break
                        try:
                            item = next(tree_iterator)
                        except StopIteration:
                            break
                        except BaseException:
                            # Windows might encounter PermissionError.
                            pass
                        else:
                            self.num_objects += 1
                            try:
                                self.size_objects += sum(
                                    [it.stat().st_size for it in item])
                            except BaseException:
                                pass
                self.is_counting = False
                self.has_counted = True
            time.sleep(0.5)


class TreeWidget(QtWidgets.QWidget):
    def __init__(self,
                 which: Literal["input", "output"] = "input",
                 *args,
                 **kwargs):
        """Widget handling tree views for directories"""
        super(TreeWidget, self).__init__(*args, **kwargs)
        ref_ui = resources.files("mpl_data_cast.gui") / "widget_tree.ui"
        with resources.as_file(ref_ui) as path_ui:
            uic.loadUi(path_ui, self)

        #: keep track of recipe
        self._recipe = map_recipe_name_to_class("CatchAll")
        #: whether we are "output" or "input"
        self.which = which
        #: whether the directory tree should be read-only
        self.readonly = which == "input"
        #: path of current working directory
        self._path = None
        #: tree data structure
        self.p_tree = None

        # tree spider counter daemon
        self.tree_counter = TreeObjectCounter()
        self.tree_counter.start()

        # tree view model
        self.model = QtGui.QFileSystemModel()
        self.model.setReadOnly(True)
        self.treeView.setModel(self.model)

        # UI update function
        self.tree_label_timer = QtCore.QTimer(self)
        self.tree_label_timer.timeout.connect(self.on_update_object_count)
        self.tree_label_timer.start(300)

        self.groupBox.setTitle(self.which.capitalize())
        self.pushButton_dir.setText(f"Select {self.which} directory")
        self.settings = QtCore.QSettings()
        self.tree_depth_limit = int(self.settings.value(
            "main/tree_depth_limit", 3))

        self.pushButton_dir.clicked.connect(
            self.on_tree_browse_button)
        self.lineEdit_dir.editingFinished.connect(
            self.on_tree_edit_line)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        path = pathlib.Path(path)
        if not self.readonly and not is_dir_writable(path):
            msg_txt = f"The {self.which} directory '{path}' is not " \
                      f"writable. Please select a different directory."
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText(msg_txt)
            msg.setWindowTitle(f"{self.which.capitalize()} directory invalid")
            msg.exec()
        else:
            self._path = path
            self.tree_counter.path = path
            self.model.setRootPath(str(path))
            self.treeView.setRootIndex(self.model.index(str(path)))
            self.lineEdit_dir.setText(str(path))

    @property
    def recipe(self):
        """The current recipe we are working with"""
        return self._recipe

    @recipe.setter
    def recipe(self, recipe):
        self._recipe = recipe
        self.tree_counter.recipe = recipe

    @QtCore.pyqtSlot(object)
    def dragEnterEvent(self, e) -> None:
        """Whether files are accepted"""
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    @QtCore.pyqtSlot(object)
    def dropEvent(self, e) -> None:
        """Add dropped directory to treeview and lineedit."""
        urls = e.mimeData().urls()
        file_1 = urls[0]
        pp = pathlib.Path(file_1.toLocalFile())
        if pp.is_dir():
            path_tree = pp
        else:
            path_tree = pp.parent
        self.path = path_tree

    @QtCore.pyqtSlot()
    def on_tree_browse_button(self) -> None:
        p = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption=f"Select {self.which} directory:",
            directory=str(self.path) if self.path else None)
        if p:
            self.path = p

    @QtCore.pyqtSlot()
    def on_tree_edit_line(self) -> None:
        """User edited the lineEdit manually"""
        tree_dir = pathlib.Path(self.lineEdit_dir.text())
        if tree_dir.is_dir():
            self.path = tree_dir

    @QtCore.pyqtSlot()
    def on_update_object_count(self):
        """`self.tree_label_timer` calls this regularly"""
        objects = self.tree_counter.num_objects
        size = self.tree_counter.size_objects
        size_str = human_size(size)
        if self.tree_counter.is_counting:
            label = f"counting {objects} objects ({size_str})"
        else:
            label = f"{objects} objects ({size_str})"
        self.label_objects.setText(label)


def human_size(bt, units=None):
    """Return a human-eadable string representation of bytes """
    if units is None:
        units = [' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    return str(bt) + units[0] if bt < 1024 else human_size(bt >> 10, units[1:])
