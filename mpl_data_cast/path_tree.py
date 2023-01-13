"""
Structuring paths in a tree to efficiently handle files.
"""

import pathlib
import numpy as np
from PyQt6 import QtWidgets


class PathError(BaseException):
    pass


class PathTree:
    def __init__(self, path: pathlib.Path, depth_limit: int = 8):
        """
        Class for handling paths in a tree structure.

        Parameters
        ----------
        path : str or pathlib.Path
            The root of the path tree. Must be absolute path. If the path
            points to a file, the parent directory of that file is used.
        depth_limit : int
            Maximum depth of subdirectories that the PathTree object will load.
            Avoid large numbers on directories with many subfolders and files
            to reduce speed and performance issues.
        """
        if not isinstance(path, pathlib.Path):
            raise TypeError(f"Path for PathTree must be `pathlib.Path`. Got "
                            f"{type(path)} instead!")
        if path.is_dir():
            self.tree_root = path
        elif path.is_file():
            self.tree_root = path.parent
        else:
            raise PathError("Root path given as input for PathTree is neither "
                            "a valid directory nor a valid file. Don't know "
                            "what to do.")
        self.depth_limit = depth_limit
        self.children = {}

        for file_obj in self.tree_root.iterdir():
            if file_obj.is_dir() and self.depth_limit > 1:
                self.children[file_obj.name] = PathTree(file_obj,
                                                        self.depth_limit - 1)
        self.list_child_dirs = []
        if self.depth_limit == 1:
            # in case we are in the "deepest" PathTree, only make a list of
            # subdirectories, but not full PathTree objects. This will make
            # sure that the function `get_tree_depth` will always return
            # correct values
            for file_obj in self.tree_root.iterdir():
                if file_obj.is_dir():
                    self.list_child_dirs.append(file_obj.name)
        self.tree_depth = self.get_tree_depth()

    def __contains__(self, other_path: pathlib.Path) -> bool:
        # this will not work perfectly, since the tree might just not have
        # enough depth to contain the path in question (if self.depth_limit is
        # rather small).
        # To check the whole tree, use:
        # path in tree.retrieve_full_path_tree()
        if other_path.samefile(self.tree_root):
            return True
        elif self.children:
            for child_tree in self.children.values():
                return other_path in child_tree
        elif self.list_child_dirs:
            contained = False
            for sub_dir in self.list_child_dirs:
                if other_path.samefile(self.tree_root / sub_dir):
                    contained = True
                    break
            return contained
        else:
            return False

    def get_tree_depth(self) -> int:
        """Returns the depth of the path tree. If there are no subfolders,
        the depth is 1. Works recursively!"""
        if self.children:
            child_depths = [child.get_tree_depth() for child in
                            self.children.values()]
            return np.max(child_depths) + 1
        else:
            return 1

    def get_file_list(self) -> list[pathlib.Path]:
        """Return a list of all files in the root directory."""
        return [x for x in self.tree_root.glob("*.*") if
                x.is_file() and not x.name[0] == "."]

    def retrieve_full_path_tree(self):
        """Returns a `PathTree` object containing all files and subdirectories,
        without a depth limit (depth_limit=100)."""
        return PathTree(self.tree_root, depth_limit=100)


def list_items_in_tree(p_tree: PathTree,
                       tree_widget: QtWidgets.QTreeWidget,
                       h_level: int = 0,
                       depth_limit: int = 24) -> None:
    """Recursive function used for visualisation of the paths saved in a
    `PathTree` object.
    To avoid problems when working with many nested subdirectories, a limit
    for the maximum depth of subfolders is given by the parameter
    `depth_limit`.

    Parameters
    ----------
    p_tree : PathTree
        An instance of :class:`PathTree`, contains all the information about
        files and subfolders.
    tree_widget : QtWidgets.QTreeWidget
        The QtWidget used to display the files and subfolders in a certain
        directory (=the root directory of :PathTree:`p_tree`)
    h_level : int
        Counter for the hierarchy level, tells how deep into subfolders the
        algorithms went. Needed for displaying files in the right column of the
        QTreeWidget. Basically counts the recursion depth of the function.
    depth_limit : int
        Maximum depth of subfolders that will be displayed.
    """
    root_item = QtWidgets.QTreeWidgetItem(tree_widget)
    root_item.setText(h_level, p_tree.tree_root.name)
    if h_level < depth_limit:
        for file in p_tree.get_file_list():
            item = QtWidgets.QTreeWidgetItem(tree_widget)
            item.setText(h_level + 1, file.name)
    if p_tree.children and h_level < depth_limit:
        for child_tree in p_tree.children.values():
            list_items_in_tree(child_tree, tree_widget, h_level + 1,
                               depth_limit)
    if p_tree.list_child_dirs and h_level <= depth_limit:
        for sub_dir in p_tree.list_child_dirs:
            item = QtWidgets.QTreeWidgetItem(tree_widget)
            item.setText(h_level + 1, sub_dir)
