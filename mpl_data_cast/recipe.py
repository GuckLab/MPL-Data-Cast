import hashlib
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
        #: Temporary directory (will be deleted upon application exit)
        self.tempdir = pathlib.Path(tempfile.mkdtemp(prefix="MPL-Data-Cast_"))
        atexit.register(shutil.rmtree, self.tempdir, ignore_errors=True)

    def cast(self, **kwargs):
        """Cast the entire data tree to the target directory"""
        ds_iterator = self.get_raw_data_iterator()
        for path_list in ds_iterator:
            targ_path = self.get_target_path(path_list)
            temp_path = self.get_temp_path(path_list)
            self.convert_dataset(path_list=path_list, temp_path=temp_path,
                                 **kwargs)
            ok = self.transfer_to_target_path(temp_path=temp_path,
                                              target_path=targ_path)
            if not ok:
                raise ValueError(f"Creation of {temp_path} failed!")

    @abstractmethod
    def convert_dataset(self, path_list, temp_path, **kwargs):
        """Implement in subclass to do conversion"""

    @abstractmethod
    def get_raw_data_iterator(self):
        """Return list of lists of raw data paths

        Returns
        -------
        raw_data_iter: iterable of lists
            iterator (yielding lists of pathlib.Path) of which
            each item contains all files that belong to one dataset.
        """

    def get_target_path(self, path_list):
        """Get the target path for a path_list

        The target path is computed such that these relative paths
        are the same:

        - self.path_raw - path_list[0]
        - self.path_tar - target_path

        Parameters
        ----------
        path_list: list of pathlib.Path
            the input paths corresponding to a dataset

        Returns
        -------
        target_path: pathlib.Path
            the output path
        """
        prel = path_list[0].relative_to(self.path_raw)
        target_path = self.path_tar / prel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    def get_temp_path(self, path_list):
        """Return a unique temporary file name"""
        hash1 = hashlib.md5(str(path_list[0]).encode("utf-8")).hexdigest()
        self.tempdir.mkdir(parents=True, exist_ok=True)
        return self.tempdir / f"{hash1}_{uuid.uuid4()}_{path_list[0].name}"

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


def get_available_recipe_names():
    names = []
    for cls in Recipe.__subclasses__():
        names.append(map_class_to_recipe_name(cls))
    return sorted(names)


def map_class_to_recipe_name(cls):
    cls_name = cls.__name__
    assert cls_name.endswith("Recipe")
    return cls_name[:-6]


def map_recipe_name_to_class(recipe_name):
    for cls in Recipe.__subclasses__():
        if cls.__name__.lower() == recipe_name.lower() + "recipe":
            return cls
    else:
        raise KeyError(f"Could not find class recipe for '{recipe_name}'!")
