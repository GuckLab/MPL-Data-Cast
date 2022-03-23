import shutil

from ..util import hashfile
from ..recipe import Recipe


class CatchAllRecipe(Recipe):
    """Copy all files, except known junk files"""

    def convert_dataset(self, path_list, temp_path):
        shutil.copy2(path_list[0], temp_path)
        # Perform a preliminary hash check to make sure that this
        # copy process was done properly.
        if hashfile(path_list[0]) != hashfile(temp_path):
            raise ValueError(
                f"Initial hash verification failed for {path_list[0]}!")

    def get_raw_data_list(self):
        ignore_list = [
            ".DS_Store",
            "._.DS_Store",
            "Thumbs.db",
        ]
        datalist = []
        for pp in sorted(self.path_raw.rglob("*")):
            if not pp.is_dir() and pp.name not in ignore_list:
                datalist.append([pp])
        return datalist
