import h5py
import numpy as np

from ..helper import is_valid_h5_file, h5_file_contains
from ..recipe import Recipe


class OffAxisHolographyRecipe(Recipe):
    """Matlab file format (TopogMap.mat) for DHM data"""

    def convert_dataset(self, path_list, temp_path):
        """Convert DHM .mat data to qpformat HDF5 format"""
        with h5py.File(path_list[0]) as mat, h5py.File(temp_path, "w") as h5:
            topog = mat["topogMap"][:]
            # make sure we have a 3D stack
            if len(topog.shape) == 2:
                topog.reshape(1, topog.shape[0], -1)
            for ii in range(topog.shape[0]):
                ds = h5.create_dataset(
                    name=str(ii),
                    chunks=topog[ii].shape,
                    data=topog[ii],
                    fletcher32=True,
                )
                # QPI metadata
                ds.attrs["numerical aperture"] = mat["NA"][:].item()
                ds.attrs["wavelength"] = mat["lambda"][:].item() * 1e-6
                ds.attrs["pos x"] = mat["positionVal"][0].item() * 1e-6
                ds.attrs["pos y"] = mat["positionVal"][1].item() * 1e-6
                ds.attrs["focus"] = mat["positionVal"][2].item() * 1e-6
                ds.attrs["pixel size"] = mat["res"][:].item() * 1e-6
                ds.attrs["medium index"] = 1.333
                if "frameRate" in mat:
                    dt = 1 / mat["frameRate"][:].item()
                    ds.attrs["time"] = ii * dt
                # Create and Set image attributes:
                # HDFView recognizes this as a series of images.
                # Use np.string_ as per
                # http://docs.h5py.org/en/stable/strings.html#compatibility
                ds.attrs.create('CLASS', np.string_('IMAGE'))
                ds.attrs.create('IMAGE_VERSION', np.string_('1.2'))
                ds.attrs.create('IMAGE_SUBCLASS',
                                np.string_('IMAGE_GRAYSCALE'))

    def get_raw_data_list(self):
        datalist = []
        for pp in sorted(self.path_raw.rglob("*.mat")):
            if (is_valid_h5_file(pp)
                and h5_file_contains(pp, "topogMap")
                and h5_file_contains(pp, "res")
                    and h5_file_contains(pp, "lambda")):
                datalist.append([pp])
        return datalist
