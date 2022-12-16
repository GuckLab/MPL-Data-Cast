import json
import warnings
import pathlib
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
    "wavelength": ["wavelength", "QLSIIllumFilter-Label",
                   # "QLSIIllumFilter-FBH488-10-CWL488-FWHM10-St483-Stp493"
                   lambda x: float(x.split("-")[3].strip("CWL"))*1e-9],
    # TODO
    "medium index": ["medium_index", "RI_UNDEFINED", lambda x: x],
    "numerical aperture": ["UNUSED", "NA_UNDEFINED", lambda x: x],
}


class QLSIRecipe(Recipe):
    """ome.tif file format from MicroManager with Phasics SID4Bio camera"""
    def _write_h5_dataset_metadata(self, path, ds, json_meta_data=None,
                                   warn=True):
        if json_meta_data is None:
            json_meta_data = {}
        for key in meta_data_mapping:
            parname, spim_name, converter = meta_data_mapping[key]
            # check if the attributes are set
            kw_ds = ds.attrs.get(key, None)
            if kw_ds is None:
                # fill in missing metadata from json dictionary
                mval = json_meta_data.get(spim_name, None)
                if mval is None:
                    if warn:
                        warnings.warn(f"No {key} defined for {path}!")
                else:
                    ds.attrs[key] = converter(mval)

        # Create and Set image attributes:
        # HDFView recognizes this as a series of images.
        # Use np.string_ as per
        # http://docs.h5py.org/en/stable/strings.html#compatibility
        ds.attrs.create('CLASS', np.string_('IMAGE'))
        ds.attrs.create('IMAGE_VERSION', np.string_('1.2'))
        ds.attrs.create('IMAGE_SUBCLASS', np.string_('IMAGE_GRAYSCALE'))

    def convert_dataset(self, path_list: list, temp_path: pathlib.Path,
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

        # get the reference data
        ref_data = tifffile.imread(str(path_list[2]))

        # Sanity checks
        slices = meta_data_full["Summary"].get("Slices", 1)
        frames = meta_data_full["Summary"].get("Frames", 1)
        # (positions are individual files)
        # (channels are not handled here)
        if frames * slices != len(data):
            raise ValueError("Size mismatch in data and meta data!")

        # prepare HDF5 metadata
        dsattrs = {}
        local_parms = locals()
        for key in meta_data_mapping:
            parname, spim_name, converter = meta_data_mapping[key]
            # get keyword argument given to this function
            kw_val = local_parms.get(parname, None)
            if kw_val is not None:  # e.g. `if wavelength is not None`
                dsattrs[key] = kw_val

        if qlsi_pitch_term:
            dsattrs["qlsi_pitch_term"] = qlsi_pitch_term

        dsattrs["device"] = meta_data_full["Summary"]["ComputerName"]
        dsattrs["software"] = "MicroManager " \
            + meta_data_full["Summary"]["MicroManagerVersion"]

        # Create the HDF5 file
        with h5py.File(temp_path, "w") as h5:
            # Store the entire meta data file
            write_text_dataset(h5.require_group("logs"),
                               "meta_data",
                               meta_text.split("\n"))

            # Store the reference meta data file
            write_text_dataset(
                h5.require_group("logs"),
                "meta_data_ref",
                path_list[3].read_text(errors="ignore").split("\n"))

            # write qpformat metadata identifier
            h5.attrs["file_format"] = "qpformat"
            h5.attrs["imaging_modality"] = \
                "quadriwave lateral shearing interferometry"

            # Write reference data
            ds = h5.create_dataset(
                name="reference",
                chunks=ref_data.shape,
                data=ref_data,
                fletcher32=True,
                compression=True,
                compression_opts=9,
            )
            ds.attrs.update(dsattrs)
            self._write_h5_dataset_metadata(
                path=path_list[2],
                ds=ds,
                warn=False,
            )

            # Write series data
            for ii, img in enumerate(data):
                json_meta_data = meta_data_list[ii]
                ds = h5.create_dataset(
                    name=str(ii),
                    chunks=img.shape,
                    data=img,
                    fletcher32=True,
                    compression=True,
                    compression_opts=9,
                )
                ds.attrs.update(dsattrs)
                self._write_h5_dataset_metadata(
                    path=path_list[0],
                    ds=ds,
                    json_meta_data=json_meta_data
                )

    def get_raw_data_iterator(self):
        """ Get raw data files

        Data directory structure for measurement and reference (ref) data.

        - QLSI_2022-04-29_ZStack_Example_1
          - comments.txt
          - DisplaySettings.json
          - QLSI_2022-04-26_ZStack_Example_1_MMStack_Pos0_metadata.txt
          - QLSI_2022-04-26_ZStack_Example_1_MMStack_Pos0.ome.tif
        - QLSI_2022-04-29_ZStack_Example_ref_1
          - comments.txt
          - DisplaySettings.json
          - QLSI_2022-04-26_ZStack_Example_ref_1_MMStack_Pos0_metadata.txt
          - QLSI_2022-04-26_ZStack_Example_ref_1_MMStack_Pos0.ome.tif
        """
        # This is from the preliminary data
        for pp in sorted(self.path_raw.rglob("*.tif")):
            if pp.name.count("_ref_"):
                # ignore reference measurements
                continue
            if self.is_valid_file(pp):
                meta_path = pp.with_name(pp.name[:-8] + "_metadata.txt")
                name_stem, num = pp.parent.name.rsplit("_", 1)
                ref_dir = pp.parent.with_name(f"{name_stem}_ref_{num}")
                ref_pp = list(ref_dir.glob("*.tif"))[0]
                ref_meta = ref_pp.with_name(ref_pp.name[:-8] + "_metadata.txt")
                # handle junk data (included, so we don't copy it)
                junk = []
                for pi in [pp, ref_pp]:
                    junk.append(pi.parent / "comments.txt")
                    junk.append(pi.parent / "DisplaySettings.json")
                yield [pp, meta_path, ref_pp, ref_meta] + junk

    def get_target_path(self, path_list):
        """Get the target path .h5 for a path_list"""
        target_p = super(QLSIRecipe,
                         self).get_target_path(path_list)
        name = target_p.name[:-8] + ".h5"
        # get rid of one directory hierarchy level
        return target_p.parent.parent / name

    @staticmethod
    def is_valid_file(path):
        valid = False
        if path.name.endswith(".ome.tif"):
            meta_path = path.with_name(path.name[:-8] + "_metadata.txt")
            # also check for reference measurement
            name_stem, num = path.parent.name.rsplit("_", 1)
            ref_dir = path.parent.with_name(f"{name_stem}_ref_{num}")
            if (ref_dir.exists()
                and bool(list(ref_dir.glob("*.ome.tif")))
                    and bool(list(ref_dir.glob("*_metadata.txt")))
                    and meta_path.exists()
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
