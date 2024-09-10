import os
import pdfplumber
from utils.file_utils import delete_file_by_type, is_file_write_complete


def read_pdf_text(
    path=os.path.join(os.getcwd(), os.getenv("TEMP_DIRECTORY", "temp")), file_type="pdf"
):
    """
    Read the text content from a PDF file.

    Parameters:
    - path (str): The path to the folder containing the PDF files. Default is TEMP_PATH.
    - file_type (str): The file extension to search for. Default is 'pdf'.

    Returns:
    - str: The extracted text content if a single PDF file is found. Otherwise returns None.
    """

    files = [
        f
        for f in os.listdir(path)
        if f.endswith((f".{file_type}", f".{file_type.upper()}"))
    ]
    if len(files) == 1:
        file_path = os.path.join(path, files[0])
        if is_file_write_complete(file_path):
            with pdfplumber.open(file_path) as pdf:
                pdf_text = "".join(
                    page.extract_text() for page in pdf.pages if page.extract_text()
                )
            delete_file_by_type(path, "pdf")
            delete_file_by_type(path, "tmp")
            delete_file_by_type(path, "crdownload")
            return pdf_text
    return None
