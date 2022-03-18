from abc import ABC, abstractmethod
import atexit
import pathlib
import shutil
import tempfile
import uuid

from .util import hashfile


class Recipe(ABC):
    def __init__(self, path_raw, path_tar):
        """Base class recipe for data conversion

        Parameters
        ----------
        path_raw: str or pathlib.Path
            Directory tree containing raw experimental data
        path_tar: str or pathlib.Path
            Target directory for converted data
        """
        #: The dataset format (defined by class name)
        self.format = self.__class__.__name__
        #: Path to raw data tree
        self.path_raw = pathlib.Path(path_raw)
        #: path to target data tree
        self.path_tar = pathlib.Path(path_tar)
        if not self.path_raw.exists():
            raise ValueError(f"Raw data path '{self.path_raw}' doesn't exist!")
        if not self.get_raw_data_list():
            raise ValueError(f"No raw data files found matching {self.format}")
        #: Temporary directory (will be deleted upon application exit)
        self.tempdir = pathlib.Path(tempfile.mkdtemp(prefix="MPL-Data-Cast_"))
        atexit.register(shutil.rmtree, self.tempdir, ignore_errors=True)

    def cast(self):
        """Cast the entire data tree to the target directory"""
        dataset_list = self.get_raw_data_list()
        for ii, path_list in enumerate(dataset_list):
            targ_path = self.get_target_path(path_list)
            temp_path = self.tempdir / f"{ii}_{uuid.uuid4()}_{targ_path.name}"
            self.convert_dataset(path_list=path_list, temp_path=temp_path)
            ok = self.transfer_to_target_path(temp_path=temp_path,
                                              target_path=targ_path)
            if not ok:
                raise ValueError(f"Creation of {temp_path} failed!")

    @abstractmethod
    def convert_dataset(self, path_list, temp_path):
        """Implement in subclass to do conversion"""

    @abstractmethod
    def get_raw_data_list(self):
        """Return list of lists of raw data paths

        Returns
        -------
        raw_data_paths: list
            list (containing lists of pathlib.Path) of which
            each item contains all files that belong to one dataset.
        """

    def get_target_path(self, path_list):
        """Get the target path for a path_list

        The target path is computed such that these relative paths
        are the same:

        - self.path_raw - path_list[0]
        - self.path_tar - target_path
        """
        prel = path_list[0].relative_to(self.path_raw)
        target_path = self.path_tar / prel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    @staticmethod
    def transfer_to_target_path(temp_path, target_path,
                                check_existing=True):
        """Transfer a file to another location

        Parameters
        ----------
        temp_path: pathlib.Path
            input file to be transferred
        target_path: pathlib.Path
            target location of the output file (including file name)
        check_existing: bool
            if `target_path` already exists, perform an MD5sum check
            and re-copy the file if the check fails

        Returns
        -------
        success: bool
            whether everything went as planned
        """
        # compute md5hash of temp_path
        hash_ok = hashfile(temp_path)
        if target_path.exists():
            if check_existing:
                # first check the size, then the hash
                if (temp_path.stat().st_size != temp_path.stat().st_size
                        or hashfile(target_path) != hash_ok):
                    # The file is not the same, delete it and try again.
                    target_path.unlink()
                    success = Recipe.transfer_to_target_path(
                        temp_path=temp_path,
                        target_path=target_path,
                        check_existing=False
                    )
                else:
                    # The file is the same, everything is good.
                    success = True
            else:
                # We don't know whether the file is the same, but
                # we don't care.
                success = True
        else:
            # transfer to target_path
            shutil.copy2(temp_path, target_path)
            # compute md5hash of target path
            hash_cp = hashfile(target_path)
            # compare md5hashes (verification)
            success = hash_ok == hash_cp
        return success


def guess_recipe(path_raw):
    """Guess the best data processing recipe for a raw data tree

    This is done by counting the files returned by `get_raw_data_list`
    for each recipe.
    """
    score = []
    path_tar = tempfile.mkdtemp()
    for cls in Recipe.__subclasses__():
        count = len(cls(path_raw, path_tar).get_raw_data_list())
        score.append([count, cls])
    score = sorted(score)
    return score[-1][1]
