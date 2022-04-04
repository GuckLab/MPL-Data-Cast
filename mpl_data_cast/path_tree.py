"""
Structuring paths in a tree to efficiently handle files.
"""

import pathlib
import os


class PathTree:
    def __init__(self, path: pathlib.Path):
        """
        Class for handling paths in a tree structure.

        Parameters
        ----------
        path : pathlib.Path
            Can be a relative or absolute path

        """
        dirs = path.parts
        self.name = dirs[0]
        self.children = {}
        if len(dirs) > 1:
            self.children[dirs[1]] = PathTree(path.relative_to(self.name))

    def __contains__(self, other_path):
        """"""
        # might need an if here.
        if other_path.parts[0] in self.children:
            return other_path.relative_to(self.name)
        else:
            return False
