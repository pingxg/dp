from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import platform


def setup_driver(download_path=None):
    # Determine the ChromeDriver path based on the operating system
    if platform.system() == 'Windows':
        chrome_driver_path = r'C:\Program Files\chromedriver.exe'
    elif platform.system() == 'Linux':
        chrome_driver_path = r'/usr/bin/chromedriver'
    else:
        # Default to using webdriver_manager to manage the driver for non-Windows OS
        chrome_driver_path = None

    chrome_options = Options()
    prefs = {
        "download.default_directory": download_path,
        "download.extensions_to_open": "applications/pdf",
        "safebrowsing.enabled": True,
        "plugins.plugins_list": [{"enabled": False, "name": "Chrome PDF Viewer"}],
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-gpu')

    # Use the ChromeDriverManager if no path is provided (useful for non-Windows OS or if no specific path is set)
    service = Service(ChromeDriverManager().install()) if chrome_driver_path is None else Service(chrome_driver_path)
    return webdriver.Chrome(service=service, options=chrome_options)
