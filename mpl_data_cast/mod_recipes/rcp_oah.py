import pathlib
import h5py
import numpy as np

from ..helper import is_valid_h5_file, h5_file_contains
from ..recipe import Recipe


class OAHRecipe(Recipe):
    """Matlab file format (TopogMap.mat) for DHM data"""

    def convert_dataset(self, path_list: list, temp_path: pathlib.Path,
                        wavelength: float = None,
                        pixel_size: float = None,
                        medium_index: float = None,
                        ):
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

                ds.attrs["wavelength"] = \
                    wavelength or mat["lambda"][:].item() * 1e-6

                ds.attrs["pos x"] = mat["positionVal"][0].item() * 1e-6
                ds.attrs["pos y"] = mat["positionVal"][1].item() * 1e-6
                ds.attrs["focus"] = mat["positionVal"][2].item() * 1e-6

                ds.attrs["pixel size"] = \
                    pixel_size or mat["res"][:].item() * 1e-6

                if "mediumIndex" in mat:  # TODO: get correct key
                    ds.attrs["medium index"] = mat["mediumIndex"].item()
                elif medium_index:
                    ds.attrs["medium index"] = medium_index

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

            # write qpformat metadata identifier
            h5.attrs["file_format"] = "qpformat"
            h5.attrs["imaging_modality"] = "off-axis holography"

    def get_raw_data_iterator(self):
        for pp in sorted(self.path_raw.rglob("*.mat")):
            if (is_valid_h5_file(pp)
                and h5_file_contains(pp, "topogMap")
                and h5_file_contains(pp, "res")
                    and h5_file_contains(pp, "lambda")):
                yield [pp]

    def get_target_path(self, path_list):
        """Get the target path .h5 for a path_list"""
        target_mat = super(OAHRecipe, self).get_target_path(path_list)
        return target_mat.with_suffix(".h5")
