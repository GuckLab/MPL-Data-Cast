from abc import ABC, abstractmethod
import atexit
import pathlib
import shutil
import tempfile
import uuid


class Converter(ABC):
    def __init__(self, path_raw, path_con):
        """Base class for data conversion

        Parameters
        ----------
        path_raw: str or pathlib.Path
            Directory containing raw experimental data
        path_con: str or pathlib.Path
            Target directory for converted data
        """
        self.path_raw = pathlib.Path(path_raw)
        self.path_con = pathlib.Path(path_con)
        if not self.path_raw.exists():
            raise ValueError(f"Raw data path '{self.path_raw}' doesn't exist!")
        if not self.path_con.exists():
            raise ValueError(f"Target path '{self.path_con}' doesn't exist!")
        if not self.get_raw_data_list():
            raise ValueError(f"No raw data files found matching {self.format}")
        #: Temporary directory (will be deleted upon application exit)
        self.tempdir = pathlib.Path(tempfile.mktemp("MPL-Data-Cast_"))
        atexit.register(shutil.rmtree, self.tempdir, ignore_errors=True)

    @property
    def format(self):
        return self.__class__.__name__

    def convert(self):
        dataset_list = self.get_raw_data_list()
        for ii, path_list in enumerate(dataset_list):
            targ_path = self.get_target_path(path_list)
            temp_path = self.tempdir / f"{ii}_{uuid.uuid4()}_{targ_path.name}"
            self.convert_dataset(path_list=path_list, temp_path=temp_path)
            self.transfer_to_target_path(temp_path=temp_path,
                                         target_path=targ_path)

    @abstractmethod
    def convert_dataset(self, path_list, temp_path):
        """Implement in subclass to do conversion"""

    @abstractmethod
    def get_raw_data_list(self):
        """Return list of lists of raw data paths

        Returns
        -------
        raw_data_path: list
            list containing lists where each item contains all files
            that belong to one dataset.
        """

    def get_target_path(self, path_list):
        # TODO:
        #  - relative path of path_list[0] to self.path_raw on top of path_con
        pass

    def transfer_to_target_path(self, temp_path, target_path):
        # TODO:
        # - compute md5hash of temp_path
        # - transfer to target_path
        # - compute md5hash of target path
        # - compare md5hashes (verification)
        pass