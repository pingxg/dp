import io
import os
from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
import pandas as pd
import logging

def get_site():
    """
    Authenticate and get the SharePoint site instance.
    """
    office_site = os.getenv('OFFICE_SITE')
    username = os.getenv('OFFICE_USN')
    password = os.getenv('OFFICE_PSW')
    sharepoint_site = os.getenv('SHAREPOINT_SITE')

    authcookie = Office365(office_site, username=username, password=password).GetCookies()
    site = Site(sharepoint_site, version=Version.v365, authcookie=authcookie)

    return site

def download_csv_data(file_name='bot_status.csv'):
    """
    Download specified invoice data file from SharePoint.
    """
    try:
        site = get_site()
        folder = site.Folder('Shared Documents')
        response = folder.get_file(file_name)

        # Assuming the file is a CSV for this example
        data = io.StringIO(str(response, 'ISO-8859-1', errors='replace'))
        df = pd.read_csv(data, sep=';')

        logging.info(f"Successfully downloaded '{file_name}' from SharePoint.")
        return df

    except Exception as e:
        logging.error(f"Failed to download '{file_name}' from SharePoint: {e}")
        return None

def download_file(file_path):
    """
    Download specified invoice data file from SharePoint.
    """
    try:
        site = get_site()
        folder = site.Folder(os.path.join(*file_path.split("/")[:-1]))
        response = folder.get_file(file_path.split("/")[-1])

        logging.info(f"Successfully downloaded '{file_path}' from SharePoint.")
        return response

    except Exception as e:
        logging.error(f"Failed to download '{file_path}' from SharePoint: {e}")
        return None

def upload_invoice_data(df, file_name='bot_status.csv'):
    """
    Upload invoice data file to SharePoint.
    """
    try:
        site = get_site()
        folder = site.Folder('Shared Documents')

        # Convert DataFrame to CSV string
        csv_data = df.to_csv(index=False, sep=';')
        folder.upload_file(csv_data, file_name)

        logging.info(f"Successfully uploaded '{file_name}' to SharePoint.")
    except Exception as e:
        logging.error(f"Failed to upload '{file_name}' to SharePoint: {e}")