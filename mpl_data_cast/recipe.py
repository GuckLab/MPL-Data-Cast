import hashlib
from abc import ABC, abstractmethod
import atexit
import pathlib
import shutil
import tempfile
import traceback
import uuid
from typing import Type, Callable, List

from .util import hashfile


#: Files that are not copied (unless specified explicitly by a recipe)
IGNORED_FILE_NAMES = [
    ".DS_Store",
    "._.DS_Store",
    "Thumbs.db",
]


class Recipe(ABC):
    #: Ignored files as specified by the recipe (an addition
    #: to `IGNORED_FILE_NAMES`)
    ignored_file_names: List[str] = []

    def __init__(self,
                 path_raw: str | pathlib.Path,
                 path_tar: str | pathlib.Path):
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

    def cast(self, path_callback: Callable = None, **kwargs) -> dict:
        """Cast the entire data tree to the target directory

        Parameters
        ----------
        path_callback: Callable
            Callable function accepting a path; used for tracking
            the progress (e.g. via the CLI)

        Returns
        -------
        result: dict
            Results dictionary with keys "success" (bool) and "errors"
            (list of tuples (path, formatted traceback))
        """
        errors = []
        # TODO: use more efficient tree structure to keep track of known files
        known_files = []
        # Copy the raw data specified by the recipe
        ds_iterator = self.get_raw_data_iterator()
        for path_list in ds_iterator:
            known_files += path_list
            if path_callback is not None:
                path_callback(path_list[0])
            targ_path = self.get_target_path(path_list)
            temp_path = self.get_temp_path(path_list)
            try:
                self.convert_dataset(path_list=path_list, temp_path=temp_path,
                                     **kwargs)
            except BaseException:
                errors.append((path_list[0], traceback.format_exc()))
                continue
            ok = self.transfer_to_target_path(temp_path=temp_path,
                                              target_path=targ_path)
            if not ok:
                raise ValueError(f"Transfer to {targ_path} failed!")
        # Walk the directory tree and copy any other files
        ignored = IGNORED_FILE_NAMES + self.ignored_file_names
        for pp in self.path_raw.rglob("*"):
            if pp.is_dir() or pp.name in ignored:
                continue
            elif pp in known_files:  # this might be slow
                continue
            else:
                if path_callback is not None:
                    path_callback(pp)
                prel = pp.relative_to(self.path_raw)
                target_path = self.path_tar / prel
                target_path.parent.mkdir(parents=True, exist_ok=True)
                ok = self.transfer_to_target_path(temp_path=pp,
                                                  target_path=target_path)
                if not ok:
                    raise ValueError(f"Transfer to {target_path} failed!")
        return {
            "success": not bool(errors),
            "errors": errors,
        }

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

    def get_target_path(self, path_list: list) -> pathlib.Path:
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
        return target_path

    def get_temp_path(self, path_list: list) -> pathlib.Path:
        """Return a unique temporary file name"""
        hash1 = hashlib.md5(str(path_list[0]).encode("utf-8")).hexdigest()
        self.tempdir.mkdir(parents=True, exist_ok=True)
        return self.tempdir / f"{hash1}_{uuid.uuid4()}_{path_list[0].name}"

    @staticmethod
    def transfer_to_target_path(temp_path: pathlib.Path,
                                target_path: pathlib.Path,
                                check_existing: bool = True) -> bool:
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
        target_path.parent.mkdir(parents=True, exist_ok=True)
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


def get_available_recipe_names() -> list[str]:
    names = []
    for cls in Recipe.__subclasses__():
        names.append(map_class_to_recipe_name(cls))
    return sorted(names)


def map_class_to_recipe_name(cls: Type[Recipe]) -> str:
    cls_name = cls.__name__
    assert cls_name.endswith("Recipe")
    return cls_name[:-6]


def map_recipe_name_to_class(recipe_name: str) -> Type[Recipe]:
    for cls in Recipe.__subclasses__():
        if cls.__name__.lower() == recipe_name.lower() + "recipe":
            return cls
    else:
        raise KeyError(f"Could not find class recipe for '{recipe_name}'!")
