import pandas as pd

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from PIL import Image as PILImage

from io import BytesIO
from pdf2image import convert_from_path

from lib.utils.logging_utils import custom_logger

logging = custom_logger(__name__)

def get_image(path, width=1*cm, **kwargs):
    img = ImageReader(path)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    return Image(path, width=width, height=(width * aspect), **kwargs)


def get_image_from_bytes(buf, width=1*cm, **kwargs):
    # Load the image from BytesIO object
    pil_image = PILImage.open(buf)

    # Get image size and calculate aspect ratio
    iw, ih = pil_image.size
    aspect = ih / float(iw)

    # Calculate the height based on the aspect ratio
    height = width * aspect

    # Reset buffer position
    buf.seek(0)

    # Create and return the ReportLab Image
    return Image(buf, width=width, height=height, **kwargs)


def add_figures(report, style, info):
    for key, info in info.items():
        # Add figure title
        title = f'<font style = "font-family:Lato" size=12><b>{info["title"]}</b><br/></font>'
        report.append(Paragraph(title, ParagraphStyle(name='centered', alignment=TA_CENTER)))

        # Add some space
        report.append(Spacer(1, 5))

        # Check if the source is a BytesIO object or a file path
        if isinstance(info['source'], BytesIO):
            # Load image from BytesIO
            buf = info['source']
            #report.append(Image(info['source'], width=info['size'][0]*cm, height=info['size'][1]*cm, hAlign='CENTER'))
        elif isinstance(info['source'], Path):
            # Convert PDF page to image
            print(info['source'])
            pil_image = convert_from_path(info['source'], info['size'][0])[0]
            buf = BytesIO()
            pil_image.save(buf, format='PNG')
            buf.seek(0)
            #report.append(Image(buf, width=info['size'][0]*cm, height=info['size'][1]*cm, hAlign='CENTER'))
        else:
            logging.error(f"Unrecognized source type: {type(info['source'])}")
            print(info['source'])

        # Add image to report using aspect ratio
        report.append(get_image_from_bytes(buf, width=info['size'][1]*cm, hAlign='CENTER'))

        # Add space and legend
        report.append(Spacer(1, 10))
        parts = info["legend"].split("\n")
        for part in parts:
            text = f'<font style = "font-family:Lora" size=8>{part}</font>'
            report.append(Paragraph(text, style["Justify"]))
            report.append(Spacer(1, 5))

        # Add a page break after each figure
        report.append(PageBreak())

    return report


# TODO: Fix and use this to automatically get zUMIs' version
def get_zumis_version(project_dir, sample_plate):
    """Returns the zUMIs version that the given plate was rabn on."""
    # TODO: Try-Except in case the folder or file does not exist

    sample_zumis_log_path = Path(project_dir / sample_plate / f"{sample_plate}.zUMIs_runlog.txt")

    log_file = open(sample_zumis_log_path, 'r')
    lines = log_file.readlines()
    version = "--"

    for line in reversed(lines):
        if "zUMIs version" in line:
            version = line.split()[-1]

    log_file.close()

    return version


def get_bc_wells(bc_set, bc_file, reagent="1.5"):
    if reagent == '1.5':
        target_col = 'XC'
    elif reagent == '1.0':
        target_col = 'XC_NovaSeq'
    else:
        logging.error(f"No recognized reagent version: {reagent}. Currently supported versions: 1.0, 1.5")
        # TODO: Handle this error properly and possibly raise an exception

    bc = pd.read_csv(bc_file, sep=',')
    bc = bc.set_index(target_col)
    return bc.loc[ bc.loc[:, 'BCset'] == bc_set , 'WellID']


def prepare_data(input_data, bc_wells, target_cols=['N', 'RG']) -> pd.DataFrame:
    data = pd.DataFrame()

    # TODO: the loop is not correct. merge or join by using the barcode as indices
    # Could use the bc_wells barcodes, just to prevent missing barcodes when taken from `input_data`?
    for t in input_data['type'].unique():
        type_ext = input_data[input_data['type'] == t]

        type_ext = type_ext.rename(columns={target_cols[0]:t}).drop(columns=['type'])

        if data.empty:
            data[target_cols[1]] = input_data[target_cols[1]].unique()
        data = pd.merge(data, type_ext, on=[target_cols[1]], how='left')

    data = data.fillna(0)

    # # Add a column with the WellID in respect to barcodes
    # data['WellID'] = data[target_cols[1]].map(bc_wells)
    # # Create a categorical order in the WellID col, using natsort
    # data['WellID'] = pd.Categorical(data['WellID'], ordered=True, categories= ns.natsorted(data['WellID'].unique()))
    # # Sort (natural sort) data on WellID. [A1,A2,A3,...,A10,A11,...,A24,B1,...,P24]
    # data = data.sort_values('WellID', ignore_index=True)

    return data


def check_high_nan_percentage(data, threshold_percent):
    """
    Checks if the percentage of NaN values in a DataFrame exceeds a specified threshold.

    Args:
        data (pd.DataFrame): DataFrame to be checked for NaN values.
        threshold_percent (float): Threshold percentage of NaN values to check against.

    Returns:
        float or bool: The percentage of NaN values if it exceeds the threshold, otherwise False.
    """
    nan_count = data.isna().sum().sum()  # Total number of NaNs
    total_elements = data.size
    nan_percentage = (nan_count / total_elements) * 100

    # print(nan_percentage)

    if nan_percentage > threshold_percent:
        return nan_percentage
    
    return False