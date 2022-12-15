"""
Structuring paths in a tree to efficiently handle files.
"""

import pathlib
import numpy as np
from PyQt6 import QtWidgets


class PathError(BaseException):
    pass


class PathTree:
    def __init__(self, path: pathlib.Path):
        """
        Class for handling paths in a tree structure.
        Parameters
        ----------
        path : str or pathlib.Path
            The root of the path tree. Must be absolute path.
        """
        if not isinstance(path, pathlib.Path):
            raise TypeError("Path for PathTree is not")
        if path.is_dir():
            self.tree_root = path
        elif path.is_file():
            self.tree_root = path.parent
        else:
            raise PathError("Root path given as input for PathTree is neither "
                            "a directory nor a file. Don't know what to do.")
        self.children = {}
        for file_obj in self.tree_root.iterdir():
            if file_obj.is_dir():
                self.children[file_obj.name] = PathTree(file_obj)
        self.tree_depth = self.get_tree_depth()

    def __contains__(self, other_path):
        """"""
        # might need an if here.
        if other_path.parts[0] in self.children:
            return other_path.relative_to(self.tree_root)
        else:
            return False

    def get_tree_depth(self):
        """return the depth of the path tree. If there are no subfolders,
        the depth is 0. """
        if self.children:
            child_depths = [child.get_tree_depth() for child in
                            self.children.values()]
            return np.max(child_depths) + 1
        else:
            return 0

    def get_file_list(self):
        """return a list of all files in the root directory."""
        return [x for x in self.tree_root.glob("*.*") if x.is_file()]


def list_items_in_tree(p_tree, tree_widget, h_level=0):
    root_item = QtWidgets.QTreeWidgetItem(tree_widget)
    root_item.setText(h_level, p_tree.tree_root.name)
    for file in p_tree.get_file_list():
        item = QtWidgets.QTreeWidgetItem(tree_widget)
        item.setText(h_level + 1, file.name)
    if p_tree.children:
        print(p_tree.children)
        for child_tree in p_tree.children.values():
            list_items_in_tree(child_tree, tree_widget, h_level+1)
