import json
import warnings

import h5py
import numpy as np
import tifffile

from ..recipe import Recipe


meta_data_mapping = {
    "pixel size": ["pixel_size", "PixelSizeUm", lambda x: x * 1e-6],
    "time": ["UNUSED", "ElapsedTime-ms", lambda x: x * 1e3],
    "date": ["UNUSED", "ReceivedTime", lambda x: x.split()[0]],
    "identifier": ["UNUSED", "UUID", lambda x: x],
    "pos x": ["UNUSED", "XPositionUm", lambda x: x * 1e-6],
    "pos y": ["UNUSED", "YPositionUm", lambda x: x * 1e-6],
    "focus": ["UNUSED", "ZPositionUm", lambda x: x * 1e-6],
    # TODO
    "wavelength": ["wavelength", "WAVELENGTH_UNDEFINED", lambda x: x]
    "medium index": ["medium_index", "RI_UNDEFINED", lambda x: x],
    "numerical aperture": ["UNUSED", "NA_UNDEFINED", lambda x: x],
}


class QLSIRecipe(Recipe):
    """ome.tif file format from MicroManager with Phasics SID4Bio camera"""
    def convert_dataset(self, path_list, temp_path,
                        wavelength: float = None,
                        pixel_size: float = None,
                        medium_index: float = None,
                        qlsi_pitch_term: float = 1.87711e-08
                        ):
        """Convert QLSI TIF data to qpformat HDF5 format"""
        # get the metadata
        meta_text = path_list[1].read_text(errors="ignore")
        meta_data_full = json.loads(meta_text)

        # extract the information from every frame
        meta_data_list = []
        for key in meta_data_full:
            if key.startswith("FrameKey"):
                meta_data_list.append(meta_data_full[key])
        meta_data_list = sorted(meta_data_list,
                                key=lambda x: x["ElapsedTime-ms"])

        # get the data from the tif file
        data = []
        with tifffile.TiffFile(path_list[0]) as tif:
            for ii in range(len(tif.pages)):
                data.append(tif.asarray(ii))

        # Sanity checks
        slices = meta_data_full["Summary"].get("Slices", 1)
        frames = meta_data_full["Summary"].get("Frames", 1)
        # (positions are individual files)
        # (channels are not handled here)
        if frames * slices != len(data):
            raise ValueError("Size mismatch in data and meta data!")

        # write the data
        with h5py.File(temp_path, "w") as h5:
            for ii, img in enumerate(data):
                meta_data = meta_data_list[ii]
                ds = h5.create_dataset(
                    name=str(ii),
                    chunks=img.shape,
                    data=img,
                    fletcher32=True,
                    compression=True,
                    compression_opts=9,
                )
                # QPI metadata
                local_parms = locals()
                for key in meta_data_mapping:
                    parname, spim_name, converter = meta_data_mapping[key]
                    # extract keyword argument given to this function
                    kw_val = local_parms.get(parname, None)
                    if kw_val is not None:  # e.g. `if wavelength is not None`
                        ds.attrs[key] = kw_val
                    else:
                        mval = meta_data.get(spim_name, None)
                        if mval is None:
                            warnings.warn(
                                f"No {key} defined for {path_list[0]}!")
                        else:
                            ds.attrs[key] = converter(mval)

                if qlsi_pitch_term:
                    ds.attrs["qlsi_pitch_term"] = qlsi_pitch_term

                ds.attrs["device"] = meta_data_full["Summary"]["ComputerName"]
                ds.attrs["software"] = \
                    "MicroManager " \
                    + meta_data_full["Summary"]["MicroManagerVersion"]

                # Create and Set image attributes:
                # HDFView recognizes this as a series of images.
                # Use np.string_ as per
                # http://docs.h5py.org/en/stable/strings.html#compatibility
                ds.attrs.create('CLASS', np.string_('IMAGE'))
                ds.attrs.create('IMAGE_VERSION', np.string_('1.2'))
                ds.attrs.create('IMAGE_SUBCLASS',
                                np.string_('IMAGE_GRAYSCALE'))

            # Also store the entire log file
            write_text_dataset(h5.require_group("logs"),
                               "meta_data",
                               meta_text.split("\n"))

            # write qpformat metadata identifier
            h5.attrs["file_format"] = "qpformat"
            h5.attrs["imaging_modality"] = \
                "quadriwave lateral shearing interferometry"

    def get_raw_data_iterator(self):
        # This is from the preliminary data
        for pp in sorted(self.path_raw.rglob("*.tif")):
            if self.is_valid_file(pp):
                meta_path = pp.with_name(pp.name[:-8] + "_metadata.txt")
                junk1 = pp.parent / "comments.txt"
                junk2 = pp.parent / "DisplaySettings.json"
                yield [pp, meta_path, junk1, junk2]

    def get_target_path(self, path_list):
        """Get the target path .h5 for a path_list"""
        target_p = super(QLSIRecipe,
                         self).get_target_path(path_list)
        return target_p.with_name(target_p.name[:-8] + ".h5")

    @staticmethod
    def is_valid_file(path):
        valid = False
        if path.name.endswith(".ome.tif"):
            meta_path = path.with_name(path.name[:-8] + "_metadata.txt")
            if (meta_path.exists()
                    and meta_path.read_text(
                        errors="ignore").count("QLSICamera")):
                valid = True
        return valid


def write_text_dataset(group, name, lines):
    """Write text to an HDF5 dataset

    Text data are written as a fixed-length string dataset.

    Parameters
    ----------
    group: h5py.Group
        parent group
    name: str
        name of the dataset containing the text
    lines: list of str or str
        the text, line by line
    """
    # replace text
    if name in group:
        del group[name]

    lnum = len(lines)
    # Determine the maximum line length and use fixed-length strings,
    # because compression and fletcher32 filters won't work with
    # variable length strings.
    # https://github.com/h5py/h5py/issues/1948
    # 100 is the recommended maximum and the default, because if
    # `mode` is e.g. "append", then this line may not be the longest.
    max_length = 100
    lines_as_bytes = []
    for line in lines:
        # convert lines to bytes
        if not isinstance(line, bytes):
            lbytes = line.encode("UTF-8")
        else:
            lbytes = line
        max_length = max(max_length, len(lbytes))
        lines_as_bytes.append(lbytes)

    # Create the dataset
    txt_dset = group.create_dataset(
        name,
        shape=(lnum,),
        dtype=f"S{max_length}",
        maxshape=(None,),
        chunks=True,
        fletcher32=True,
        compression="gzip",
        compression_opts=9)

    # Write the text data line-by-line
    for ii, lbytes in enumerate(lines_as_bytes):
        txt_dset[ii] = lbytes
