import json
import warnings

import h5py
import numpy as np
import tifffile

from ..recipe import Recipe


class QLSIRecipe(Recipe):
    """TIF file format from MicroManager with Phasics SID4Bio camera"""
    def convert_dataset(self, path_list, temp_path,
                        wavelength: float = None,
                        pixel_size: float = None,
                        medium_index: float = None,
                        ):
        """Convert QLSI TIF data to qpformat HDF5 format"""
        # get the metadata
        meta_data_full = json.loads(path_list[1].read_text())

        # extract the information from every frame
        meta_data_list = []
        for key in meta_data_full:
            if not key == "Summary":
                meta_data_list.append(meta_data_full[key])
        meta_data_list = sorted(meta_data_list, key=lambda x: x["Frame"])

        # get the data from the tif file
        data = []
        with tifffile.TiffFile(path_list[0]) as tif:
            for ii in range(len(tif.pages)):
                data.append(tif.asarray(ii))

        if meta_data_full["Summary"]["Slices"] != len(data):
            raise ValueError("Size mismatch in data and meta data!")

        # write the data
        with h5py.File(temp_path, "w") as h5:
            for ii, img in enumerate(data):
                meta_data = meta_data_list[ii]
                if meta_data["Frame"] != ii:
                    raise ValueError(f"Frame mismatch at index {ii}!")
                ds = h5.create_dataset(
                    name=str(ii),
                    chunks=img.shape,
                    data=img,
                    fletcher32=True,
                )
                # QPI metadata

                if wavelength:
                    ds.attrs["wavelength"] = wavelength
                else:
                    warnings.warn(f"No wavelength defined for {path_list[0]}!")

                # ds.attrs["pos x"] = mat["positionVal"][0].item() * 1e-6
                # ds.attrs["pos y"] = mat["positionVal"][1].item() * 1e-6
                # ds.attrs["focus"] = mat["positionVal"][2].item() * 1e-6
                warnings.warn(f"No XYZ position defined for {path_list[0]}!")

                if pixel_size:
                    ds.attrs["pixel size"] = pixel_size
                else:
                    px_size = meta_data.get("PixelSize_um", 0) * 1e-6
                    if px_size == 0:
                        warnings.warn(
                            f"No pixel size defined for {path_list[0]}!")
                    else:
                        ds.attrs["pixel size"] = px_size

                if medium_index:
                    ds.attrs["medium index"] = medium_index
                else:
                    ds.attrs["medium index"] = 1.333
                    warnings.warn(
                        f"No medium index defined for {path_list[0]}!")

                ds.attrs["date"] = meta_data_full["Summary"]["Date"]

                # set time
                ds.attrs["time"] = meta_data["ElapsedTime-ms"] * 1e-3

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
            h5.attrs["imaging_modality"] = \
                "quadriwave lateral shearing interferometry"

    def get_raw_data_iterator(self):
        # This is from the preliminary data
        for pp in sorted(self.path_raw.rglob("*.tif")):
            meta_file = pp.with_name("metadata.txt")
            if meta_file.exists():
                if meta_file.read_text().count(
                        '"ODTCamera-Camera": "33365 Retiga 2000R S/N Q33365"'):
                    yield [pp, meta_file]
        # This might work in the future
        for pp in sorted(self.path_raw.rglob("*.ome")):
            meta_file = pp.with_suffix(".json")
            if meta_file.exists():
                # check meta_file for QLSI key
                if meta_file.read_text().count("QLSI"):
                    yield [pp, meta_file]

    def get_target_path(self, path_list):
        """Get the target path .h5 for a path_list"""
        target_mat = super(QLSIRecipe,
                           self).get_target_path(path_list)
        return target_mat.with_suffix(".h5")
