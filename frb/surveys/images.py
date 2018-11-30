""" Module for image routines"""

import requests
from io import BytesIO
from PIL import Image

from matplotlib import pyplot as plt

def grab_from_url(url):
    """
    Grab a PIL Image from a URL

    Args:
        url: str

    Returns:
        img: PIL.Image

    """
    # Simple calls
    rtv = requests.get(url)
    img = Image.open(BytesIO(rtv.content))
    # Return
    return img


def gen_snapshot_plt(img, imsize, show=False):
    """
    Generate a simple figure from an input PIL.Image

    Args:
        img: PIL.Image
        imsize: Angle
          Angular dimension of the image
        show: bool, optional
          Show to the screen?  If done, will need to regenerate to then save to disk

    Returns:
        plt: matplotlib.pyplot object

    """
    # Convert to arcsec and float
    i_arcsec = imsize.to('arcsec').value
    #
    plt.clf()
    plt.imshow(img, aspect='equal', extent=(-i_arcsec / 2., i_arcsec / 2, -i_arcsec / 2., i_arcsec / 2))
    # Label me
    plt.xlabel('Relative arcsec', fontsize=20)
    xpos = 0.22 * i_arcsec
    ypos = 0.02 * i_arcsec
    plt.text(-i_arcsec / 2. - xpos, 0., 'EAST', rotation=90., fontsize=20)
    plt.text(0., i_arcsec / 2. + ypos, 'NORTH', fontsize=20, horizontalalignment='center')
    # Show?
    if show:
        plt.show()
    # Return
    return plt

