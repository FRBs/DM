""" Methods related to galaxy photometry """

import os
import warnings
import numpy as np

from pkg_resources import resource_filename

from IPython import embed

from astropy.table import Table, hstack, vstack, join
from astropy.coordinates import SkyCoord
from astropy.coordinates import match_coordinates_sky
from astropy import units

from frb.galaxies import nebular
from frb.galaxies import defs

try:
    import extinction
except ImportError:
    print("extinction package not loaded.  Extinction corrections will fail")

# Photometry globals
table_format = 'ascii.fixed_width'
fill_values_list = [('-999', '0'), ('-999.0', '0')]
fill_value = -999.

def merge_photom_tables(new_tbl, old_file, tol=1*units.arcsec, debug=False):
    """
    Merge photometry tables

    Args:
        new_tbl (astropy.table.Table):
            New table of photometry
        old_file (str or Table):
            Path to the old table

    Returns:
        astropy.table.Table:
            Merged tables

    """
    fill_value = -999.
    # File or tbl?
    if isinstance(old_file, str):
        # New file?
        if not os.path.isfile(old_file):
            return new_tbl
        # Load me
        old_tbl = Table.read(old_file, format=table_format)
    elif isinstance(old_file, Table):
        old_tbl = old_file
    else:
        embed(header='42 of photom')
    # Coords
    new_coords = SkyCoord(ra=new_tbl['ra'], dec=new_tbl['dec'], unit='deg')
    old_coords = SkyCoord(ra=old_tbl['ra'], dec=old_tbl['dec'], unit='deg')
    idx, d2d, _ = match_coordinates_sky(new_coords, old_coords, nthneighbor=1)
    match = d2d < tol

    # Match?
    if np.sum(match) == len(new_coords):
        # Insist on the same RA, DEC
        new_tbl['ra'] = old_tbl['ra'][idx[0]]
        new_tbl['dec'] = old_tbl['dec'][idx[0]]
        # Join
        merge_tbl = join(old_tbl.filled(-999.), new_tbl, join_type='left').filled(-999.)
    elif np.sum(match) == 0:
        merge_tbl = vstack([old_tbl, new_tbl]).filled(-999.)
    else:
        embed(header='50 of photom')  # Best to avoid!!  Use photom_by_name
    # Return
    return merge_tbl

def photom_by_name(name, filelist):
    """
    Generate a Table for a given galaxy from a list of photom files

    Warning:  Order matters!  Use best data last

    Args:
        name (str):
        filelist (list):

    Returns:
        astropy.table.Table:

    """
    # Loop on tables
    final_tbl = None
    for ifile in filelist:
        # Load an insure it is a masked Table
        tbl = Table(Table.read(ifile, format=table_format, fill_values=fill_values_list), masked=True)
        idx = tbl['Name'] == name
        if np.sum(idx) == 1:
            sub_tbl = tbl[idx]
            if final_tbl is None:
                final_tbl = sub_tbl
            else:
                for key in sub_tbl.keys():
                    if sub_tbl[key].mask != True:  # Cannot use "is"
                        final_tbl[key] = sub_tbl[key]
    # Return
    return final_tbl.filled(fill_value)


def extinction_correction(filter, EBV, RV=3.1, max_wave=None, required=True):
    """
    calculate MW extinction correction for given filter

    Uses the Fitzpatrick & Massa (2007) extinction law

    Args:
        filter (str):
            filter name (name of file without .dat extension)
        EBV (float):
            E(B-V) (can get from frb.galaxies.nebular.get_ebv which uses IRSA Dust extinction query
        RV:
            from gbrammer/threedhst eazyPy.py -- characterizes MW dust
        max_wave (float, optional):
            If set, cut off the calculation at this maximum wavelength.
            A bit of a hack for the near-IR, in large part because the
            MW extinction curve ends at 1.4 microns.
        required (bool, optional):
            Crash out if the transmission curve is not present

    Returns:
             float: linear extinction correction

    """
    # Read in filter in Table
    path_to_filters = os.path.join(resource_filename('frb', 'data'), 'analysis', 'CIGALE')
    # Hack for LRIS which does not differentiate between cameras
    if 'LRIS' in filter:
        _filter = 'LRIS_{}'.format(filter[-1])
    else:
        _filter = filter
    filter_file = os.path.join(path_to_filters, _filter+'.dat')
    if not os.path.isfile(filter_file):
        msg = "Filter {} is not in the Repo.  Add it!!".format(filter_file)
        if required:
            raise IOError(msg)
        else:
            warnings.warn(msg)
            return 1.
    filter_tbl = Table.read(filter_file, format='ascii')

    #get wave and transmission (file should have these headers in first row)
    wave = filter_tbl['col1'].data
    throughput = filter_tbl['col2'].data

    if max_wave:
        warnings.warn("Cutting off the extinction correction calculation at {} Ang".format(max_wave))
        gdwv = wave < max_wave
        wave = wave[gdwv]
        throughput = throughput[gdwv]

    #get MW extinction correction
    AV = EBV * RV
    #AlAV = nebular.load_extinction('MW')
    Alambda = extinction.fm07(wave, AV)
    source_flux = 1.

    #calculate linear correction
    delta = np.trapz(throughput * source_flux * 10 ** (-0.4 * Alambda), wave) / np.trapz(
        throughput * source_flux, wave)

    correction = 1./delta

    return correction


def correct_photom_table(photom, EBV, name, max_wave=None, required=True):
    """
    Correct the input photometry table for Galactic extinction
    Table is modified in place

    If there is SDSS photometry, we look for the extinction values
    provided by the Survey itself.

    Uses extinction_correction()

    Args:
        photom (astropy.table.Table):
        EBV (float):
            E(B-V) (can get from frb.galaxies.nebular.get_ebv which uses IRSA Dust extinction query
        name (str):\
            Name of the object to correct
        required (bool, optional):
            Crash out if the transmission curve is not present

    """
    # Cut the table
    mt_name = photom['Name'] == name
    if not np.any(mt_name):
        print("No matches to input name={}.  Returning".format(name))
        return
    elif np.sum(mt_name) > 1:
        raise ValueError("More than 1 match to input name={}.  Bad idea!!".format(name))
    idx = np.where(mt_name)[0][0]
    cut_photom = photom[idx]  # This is a Row

    # Dust correct
    for key in photom.keys():
        if key in ['Name', 'ra', 'dec', 'extinction', 'SDSS_ID',
                   'run', 'rerun'] or 'err' in key:
            continue
        filter = key
        if filter not in defs.valid_filters:
            print("Assumed filter {} is not in our valid list.  Skipping extinction".format(filter))
            continue
        # -999? -- Not even measured
        try:
            if cut_photom[filter] <= -999.:
                continue
        except:
            embed(header='187')
        # SDSS
        if 'SDSS' in filter:
            if 'extinction_{}'.format(filter[-1]) in photom.keys():
                print("Appying SDSS-provided extinction correction")
                cut_photom[key] -= cut_photom['extinction_{}'.format(filter[-1])]
                continue
        # Hack for LRIS
        if 'LRIS' in filter:
            _filter = 'LRIS_{}'.format(filter[-1])
        else:
            _filter = filter
        # Do it
        dust_correct = extinction_correction(_filter, EBV, max_wave=max_wave, required=required)
        mag_dust = 2.5 * np.log10(1. / dust_correct)
        cut_photom[key] += mag_dust
    # Add it back in
    photom[idx] = cut_photom
