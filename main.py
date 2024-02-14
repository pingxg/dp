# -*- coding: utf-8 -*-
import io
import sys
import os
from os import system
import platform
import datetime as dt
import time
from time import sleep
import numpy as np
import pandas as pd
import pdfplumber
from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from contextlib import contextmanager
from extractor import info_extractor, expressions
import logging
import logger_config
from selenium.webdriver.remote.webelement import WebElement


logger_config.setup_logging()

TEMP_PATH = os.path.join(os.getcwd(), 'temp')


# Define a new class that extends WebElement
class CustomWebElement(WebElement):
    def send_keys(self, keys):
        self.clear()  # Clear the text field before sending keys
        super().send_keys(keys)  # Call the original send_keys method


def delete_file_by_type(path=TEMP_PATH, file_type='pdf'):
    """Deletes files of a given type in the provided path.

    Parameters:
    - path (str): The path to delete files from. Defaults to TEMP_PATH. 
    - file_type (str): The file extension/type to delete. Defaults to 'pdf'.
    """
    files = [f for f in os.listdir(path)]
    files = list(filter(lambda f: f.endswith((f'.{file_type}', f'.{file_type.upper()}')),files))
    for i in files:
        os.remove(os.path.join(path, i))

def setup_driver(chrome_driver_path=None, download_path=TEMP_PATH):
    chrome_options = Options()
    prefs = {
        "download.default_directory": download_path,
        # "plugins.always_open_pdf_externally": True,
        # "download.prompt_for_download": False,
        "plugins.plugins_list": [{
            "enabled": False,
            "name": "Chrome PDF Viewer"
        }],
        "download.extensions_to_open": "applications/pdf",
        # "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument('--disable-gpu')

    service = Service(chrome_driver_path) if chrome_driver_path else Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)



def wait_for_element(driver, locator, step_name='not specified', timeout=10, clickable=True):
    """
    Waits for an element to be present or clickable within a specified timeout.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - locator: A tuple specifying the locator strategy and value, e.g., (By.ID, "element_id").
    - timeout: The maximum number of seconds to wait for the element (default is 10 seconds).
    - clickable: If True, waits for the element to be clickable; otherwise, waits for the element's presence.

    Returns:
    - WebElement if found and satisfies the condition; otherwise, raises TimeoutException.

    Raises:
    - TimeoutException if the element does not satisfy the condition within the timeout period.
    """
    try:
        if clickable:
            element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
            logging.info(f"Step {step_name}: Element with locator {locator} found.")
            element.__class__ = CustomWebElement
            return element
        else:
            element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
            logging.info(f"Element with locator {locator} found.")
            element.__class__ = CustomWebElement
            return element
        
    except TimeoutException:
        logging.error(f"Step {step_name}: Element with locator {locator} not found within {timeout} seconds.")
        raise


def login(driver, username=os.getenv('bw_usr'), password=os.getenv('bw_psw'), login_url=os.getenv('bw_url')):
    """
    Logs into a website using the provided credentials.
    
    Parameters:
    - driver: Selenium WebDriver instance.
    - username: Username for login.
    - password: Password for login.
    - login_url: URL of the login page.
    """
    try:
        driver.get(login_url)
        wait_for_element(driver, (By.ID, "txtUsername"), 'find the username field and fill').send_keys(username)
        wait_for_element(driver, (By.ID, "txtPasswd"), 'find the password field and fill').send_keys(password)
        wait_for_element(driver, (By.ID, "btnLogin"), 'find the login button and click').click()
        logging.info("Login successful")
    except Exception as e:
        logging.error(f"Login failed: {e}")
        sys.exit(1)



def switch_to_iframe(driver, locator, timeout=10):
    """
    Waits for an iframe to be available and then switches to it.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - locator: A tuple specifying the locator strategy and value, e.g., (By.TAG_NAME, 'iframe').
    - timeout: The maximum number of seconds to wait for the iframe.
    """
    try:
        WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(locator))
        logging.info(f"Switched to iframe with locator {locator}")
    except TimeoutException:
        logging.error(f"Failed to switch to iframe with locator {locator} within {timeout} seconds")
        raise


def switch_to_default_content(driver):
    """
    Switches back to the main document content from an iframe.

    Parameters:
    - driver: The Selenium WebDriver instance.
    """
    driver.switch_to.default_content()
    logging.info("Switched back to the default content")

@contextmanager
def iframe_context(driver, locator):
    """
    A context manager for switching to an iframe and automatically returning to the default content afterwards.

    Parameters:
    - driver: The Selenium WebDriver instance.
    - locator: A tuple specifying the locator strategy and value for the iframe.
    """
    try:
        switch_to_iframe(driver, locator)
        yield
    finally:
        switch_to_default_content(driver)



def get_inv_number(df):
    try:
        df = df.rename(columns={'Invoice Number': 'invoice_num'})
        df = df.rename(columns={'Document Number': 'invoice_num'})
        df = df.rename(columns={'Supplier': 'vendor'})
        df = df.rename(columns={'Description': 'vendor'})
        df = df.loc[:, ['vendor', 'invoice_num']]
    except:
        logging.error("No valid information found in bw_bot_log.csv to process!")
        pass
    try:
        df['vendor_id'] = df['vendor'].str.split(' / ', expand=True)[1]
        supported_vendor = list(expressions.keys())
        df.drop_duplicates(inplace=True)
        df.loc[~df['vendor_id'].isin(supported_vendor), 'status'] = 'Not Supported'
    except:
        logging.info("No data in the bot input file!")
        return False
    return df

def is_file_write_complete(file_path, check_interval=1, retries=5):
    """
    Check if a file's write operation is complete by comparing its size over a short interval.

    Parameters:
    - file_path (str): The path to the file.
    - check_interval (int): How long to wait between checks (in seconds).
    - retries (int): How many times to check the file size for changes.

    Returns:
    - bool: True if the file size is stable (write operation likely complete), False otherwise.
    """
    prev_size = -1
    current_size = os.path.getsize(file_path)
    while retries > 0:
        time.sleep(check_interval)
        prev_size = current_size
        current_size = os.path.getsize(file_path)
        if current_size == prev_size:
            return True
        retries -= 1
    return False

def read_pdf_text(path=TEMP_PATH, file_type='pdf'):
    """
    Read the text content from a PDF file.

    Parameters:
    - path (str): The path to the folder containing the PDF files. Default is TEMP_PATH.
    - file_type (str): The file extension to search for. Default is 'pdf'.

    Returns:
    - str: The extracted text content if a single PDF file is found. Otherwise returns None.
    """

    files = [f for f in os.listdir(path) if f.endswith((f'.{file_type}', f'.{file_type.upper()}'))]
    if len(files) == 1:
        file_path = os.path.join(path, files[0])
        if is_file_write_complete(file_path):
            with pdfplumber.open(file_path) as pdf:
                pdf_text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())
            delete_file_by_type(TEMP_PATH, 'pdf')
            delete_file_by_type(TEMP_PATH, 'tmp')
            delete_file_by_type(TEMP_PATH, 'crdownload')
            return pdf_text
    return None


def filtering_invoice(driver, company="Spartao", status="All", supplier=False, invoice_num=False):
    driver.switch_to.default_content()
    purchase_invoices = wait_for_element(driver, (By.XPATH, '/html/body/form/table[12]/tbody/tr/td[6]'), "navigate to purchase invoices").click()
    process_purchase_invoices = wait_for_element(driver, (By.XPATH, '/html/body/form/table[4]/tbody/tr[2]/td/table/tbody/tr/td[1]'), 'navigate to process purchase invoices').click()

    global applicationframe
    applicationframe = wait_for_element(driver, (By.XPATH, "/html/body/div[1]/iframe"), 'find the application frame', clickable=False)
    driver.switch_to.frame(applicationframe)

    global mainframehdr
    mainframehdr = wait_for_element(driver, (By.ID, "mainframehdr"), 'find the main frame header')

    global mainframe
    mainframe = wait_for_element(driver, (By.XPATH, "/html/body/div[2]/iframe"), 'find the main frame')
    driver.switch_to.frame(mainframe)

    select_company = Select(wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/select"), 'change company selection to all', clickable=False)).select_by_visible_text(company)
    inv_num_input = wait_for_element(driver, (By.ID, "InvoiceNumberCtrl"), 'clear invoice number and input').send_keys(invoice_num)
    supplier_input = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/div[2]/div/input"), 'clear supplier name and input').send_keys(expressions[supplier][0])
    if expressions[supplier][0] == "AB Tingstad Papper":
        status = "Data Incomplete"

    select_status = Select(wait_for_element(driver, (By.XPATH, "/html/body/div[1]/form/div[3]/div[5]/select"), 'change process invoice filter status', clickable=False)).select_by_visible_text(status)

    update_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[6]/input"), 'find update button and click').click()


def get_invoice_text(driver, vendor, invoice_num):
    filtering_invoice(driver, supplier=vendor, invoice_num=invoice_num)
    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    if vendor != "1301716":
        is_tingstad = False
        invoice_button = wait_for_element(driver, (By.XPATH, '/html/body/div/form/div[4]/table/tbody/tr[2]/td[11]/a'), 'find invoice button for non-tingstad invoices').click()

    elif vendor == "1301716":
        is_tingstad = True
        invoice_button = wait_for_element(driver(By.XPATH,'/html/body/div/form/div[4]/table/tbody/tr[2]/td[12]/a'), 'find invoice button for tingstad invoices').click()
    
    try:
        driver.switch_to.default_content()
        logging.info('Try to find the lock frame.')
        errorframe = wait_for_element(driver, (By.XPATH, '/html/body/iframe'), 'try to locate the lock error frame', clickable=False)
        if errorframe is not None:
            driver.switch_to.frame(errorframe)
            override_lock_status_button = wait_for_element(driver, (By.XPATH, '/html/body/div/div[4]/input[1]'), 'try to override the lock frame and click').click()
        else:
            logging.info('Step: the invoice not lcocked, skipping this step.')
    except:
        pass

    logging.info('Step: clearing the temp folder.')
    delete_file_by_type(TEMP_PATH, 'pdf')
    delete_file_by_type(TEMP_PATH, 'tmp')

    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    logging.info("Step: downloading the pdf.")
    attachment_frame = wait_for_element(driver, (By.XPATH, '/html/body/div/div/div/div[3]/iframe'), 'find the attachment frame', clickable=False)
    driver.switch_to.frame(attachment_frame)

    viewer_frame = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/iframe'), 'find the viewer frame', clickable=False)
    driver.switch_to.frame(viewer_frame)

    try:
        save_pdf_btn = wait_for_element(driver, (By.ID, 'open-button'), 'find the pdf attachement save btn', clickable=False).click()
    except (NoSuchElementException, TimeoutException):
        logging.info("Save PDF button not found or not clickable, but continuing since the file downloads successfully.")

    logging.info('Step: waiting for the pdf to be downloaded.')
    sleep(3)

    logging.info("Step: extacting the posting value.")
    text = read_pdf_text(file_type='pdf')
    posting_info = info_extractor(text=text, vendor=vendor)

    posting_info['INV No.'] = invoice_num

    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    global info_page_frame
    info_page_frame = wait_for_element(driver, (By.XPATH, '/html/body/div/div/div/div[1]/iframe'), "find the info page frame", clickable=False)

    driver.switch_to.frame(info_page_frame)

    organizational_unit_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]/div/div/button'), 'find the organizational unit and click').click()

    driver.switch_to.default_content()
    dialog_frame = wait_for_element(driver, (By.XPATH, "/html/body/div[3]/div/iframe"), 'find the dialog frame for the org unit', clickable=False)
    driver.switch_to.frame(dialog_frame)
    select_org_unit_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/div[2]/form/div[4]/input[1]"), 'select the default org unit').click()


    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    driver.switch_to.frame(info_page_frame)

    if vendor == "1381774":
        due_date = wait_for_element(driver(By.XPATH, '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[14]/td[2]/div[1]/div/div/input'), 'modifing the S-Card due date to current date').clear().send_keys(dt.datetime.today().strftime("%d.%m.%Y"))

    post_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[2]/input[3]'), 'find the post button and click').click()

    try:
        driver.switch_to.default_content()
        driver.switch_to.frame(errorframe)
        next_time_check = wait_for_element(driver, (By.XPATH, '/html/body/div/div[3]/span/label'), 'find the show next time check and click').click()
        driver.switch_to.default_content()
        driver.switch_to.frame(errorframe)
        next_ok_btn = wait_for_element(driver, (By.XPATH, '//*[@id="yesbutton"]'), 'find the don\'t show next time check and click').click()
    except:
        pass

    try:
        logging.info("Deleting the old posting info.")

        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        action_frame = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/iframe'), 'find the action frame', clickable=False)
        driver.switch_to.frame(action_frame)
        delete_posting = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/input[2]'), 'click delete posting value').click()
        # driver.execute_script("arguments[0].click();", delete_posting)

        # create alert object
        alert = Alert(driver)

        # accept the alert
        alert.accept()

    except:
        pass

    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    posting_frame = wait_for_element(driver, (By.XPATH, '/html/body/form/div[2]/div[3]/iframe'), 'find the posting frame', clickable=False)
    driver.switch_to.frame(posting_frame)
    posting_sum = Select(wait_for_element(driver, (By.XPATH, "/html/body/form/div[3]/div/div[2]/select"), 'find the posting sum'))

    if 'location' in posting_info:
        if posting_info['location'] == 'L102':
            posting_info['department'] = 'D4'
        elif posting_info['location'] == 'L101':
            posting_info['department'] = 'D208'
            posting_info['class_code'] = 'C7'
        elif posting_info['location'] == 'L76':
            posting_info['department'] = 'D208'
        elif posting_info['location'] == 'L67':
            posting_info['department'] = 'D208'
            posting_info['class_code'] = 'C1'
        elif posting_info['location'] == 'L73':
            posting_info['department'] = 'D208'
            posting_info['class_code'] = 'C1'
        elif posting_info['location'] == 'L72':
            posting_info['department'] = 'D208'
            posting_info['class_code'] = 'C1'
            if 'department' in posting_info:
                department = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'), 'update department').send_keys(posting_info['department'])

            if 'class_code' in posting_info:
                class_code = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'), 'update class').send_keys(posting_info['class_code'])
            location = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'), 'update location').send_keys(posting_info['location'])

        if '14' in posting_info:
            logging.info("Updating 14% row.")
            if 'department' in posting_info:
                department = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'), 'updating 14% department').send_keys(posting_info['department'])
            
            if 'class_code' in posting_info:
                class_code =  wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'), 'updating 14% class').send_keys(posting_info['class_code'])

            
            location = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'), 'updating 14% location').send_keys(posting_info['location'])


            logging.info("Change to Tax included.")
            posting_sum.select_by_visible_text("Tax included")

            if posting_info['14_total'] >= 0:
                debit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[7]/input'), 'updating 14% debit amount').send_keys(str(posting_info['14_total']).replace('.', ','))

            elif posting_info['14_total'] < 0:
                credit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'), 'updating 14% credit amount').send_keys(str(-posting_info['14_total']).replace('.', ','))
            
            tax_code = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'), 'updating 14% tax code').send_keys('8')

            driver.switch_to.default_content()
            driver.switch_to.frame(applicationframe)
            driver.switch_to.frame(mainframe)
            driver.switch_to.frame(posting_frame)
            
            save_btn = wait_for_element(driver, (By.XPATH, "/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]"), 'find the save button and click')
            driver.execute_script("arguments[0].click();", save_btn)


            if '24' in posting_info:
                if 'department' in posting_info:
                    department = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[2]/div/div/input'), 'updating 24% department').send_keys(posting_info['department'])
                if 'class_code' in posting_info:
                    class_code = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[4]/div/div/input'), 'updating 24% class').send_keys(posting_info['class_code'])
                location = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[3]/div/div/input'), 'updating 24% location').send_keys(posting_info['location'])
                if posting_info['24_total'] >= 0:
                    debit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[7]/input'), 'updating 24% debit amount').send_keys(str(posting_info['24_total']).replace('.', ','))
                elif posting_info['24_total'] < 0:
                    credit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[8]/input'), 'updating 24% credit amount').send_keys(str(-posting_info['24_total']).replace('.', ','))
                tax_code = wait_for_element(driver, (By.XPATH,'/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[5]/div/div/input'), 'updating 24% tax code').send_keys('6')
                save_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[9]/a[1]'), 'find the save button and click')
                driver.execute_script("arguments[0].click();", save_btn)

        if '24' in posting_info and '14' not in posting_info:
            if 'department' in posting_info:
                department = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'), 'updating 24% department only').send_keys(posting_info['department'])
            if 'class_code' in posting_info:
                class_code = wait_for_element(driver, (By.XPATH,'/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'), 'updating 24% class only').send_keys(posting_info['class_code'])
            location = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'), 'updating 24% class only').send_keys(posting_info['location'])

            posting_sum.select_by_visible_text("Tax included")

            if posting_info['24_total'] >= 0:
                debit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[7]/input'), 'updating 24% debit amount only').send_keys(str(posting_info['24_total']).replace('.', ','))

            elif posting_info['24_total'] < 0:
                credit = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'), 'updating 24% credit amount only').send_keys(str(-posting_info['24_total']).replace('.', ','))
            tax_code = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'), 'updating 24% tax code only').send_keys('6')
            save_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]'), 'find the save button and click')
            driver.execute_script("arguments[0].click();", save_btn)


        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        action_frame = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/iframe'), 'find the action frame', clickable=False)
        driver.switch_to.frame(action_frame)

        ok_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/input[1]'), 'find the OK button and click')
        driver.execute_script("arguments[0].click();", ok_btn)

        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        
        info_page_frame = wait_for_element(driver, (By.XPATH, '/html/body/div/div/div/div[1]/iframe'), 'find the info page frame', clickable=False)
        driver.switch_to.frame(info_page_frame)

        if 'approver' in posting_info:
            logging.info("Updating approver.")
            processor_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[5]/input[2]'), 'find the processor button and click')
            driver.execute_script("arguments[0].click();", processor_btn)

            driver.switch_to.default_content()
            processor_frame = wait_for_element(driver, (By.XPATH, '/html/body/div[3]/div/iframe'), 'find the processor frame', clickable=False)
            driver.switch_to.frame(processor_frame)

            current_processor_select = Select(wait_for_element(driver, (By.XPATH,"/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[3]/div/select"), 'find the current processor select'))
            reset_processor = True
            for option in current_processor_select.options:
                if option.text == f"Approve: {posting_info['approver']}":
                    reset_processor = False
                    cancel_btn = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[4]/input[2]'), 'find the cancel button and click')
                    driver.execute_script("arguments[0].click();", cancel_btn)
            if reset_processor:
                processor_list = Select(wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[1]/div/select'), 'find the processor list'))
                processor_list.select_by_visible_text(posting_info['approver'])
                add_processor_btn = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td/table/tbody/tr[1]/td/input'), 'find the add processor button and click')
                driver.execute_script("arguments[0].click();", add_processor_btn)
                conform_processor = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[4]/input[1]'), 'find the conform processor button and click')
                driver.execute_script("arguments[0].click();", conform_processor)
            driver.switch_to.default_content()
            driver.switch_to.frame(applicationframe)
            driver.switch_to.frame(mainframe)
            driver.switch_to.frame(info_page_frame)
            save_inv_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[2]/input[1]'), 'find the save invoice button and click')
            driver.execute_script("arguments[0].click();", save_inv_btn)
        logging.info(f'Invoice {invoice_num} from {expressions[vendor][0]} has been processed successfully!')
        return True

def main():
    # Ensure TEMP_PATH exists
    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH)

    authcookie = Office365(
        os.getenv('office_site'),
        username=os.getenv('office_usn'),
        password=os.getenv('office_psw')
        )
    site = Site('https://oyspartao.sharepoint.com/sites/SpartaoFinance',
                version=Version.v365,
                authcookie=authcookie.GetCookies())
    folder = site.Folder('Shared Documents')
    data = io.StringIO(
        str(folder.get_file('bot_status.csv'), 'ISO-8859-1', errors='replace'))
    bot_input = pd.read_csv(data, sep=';')
    bot_input = bot_input[bot_input['status'] != "Success"]
    operational_data = get_inv_number(bot_input)
    filtered_df = operational_data[operational_data['status'].isin([np.nan, 'Failed'])]

    # driver = setup_driver(chrome_driver_path=r'/usr/bin/chromedriver')
    # Check the operating system
    if platform.system() == 'Windows':
        # Windows path
        chrome_driver_path = r'C:\Program Files\chromedriver.exe'
    else:
        # Assuming Linux for any non-Windows OS
        chrome_driver_path = r'/usr/bin/chromedriver'
    driver = setup_driver(chrome_driver_path=chrome_driver_path)
    login(driver)

    for index, row in filtered_df.iterrows():
        try:
            if row['status'] != 'Success':
                logging.info(f'================== Processing invoice {row["invoice_num"]} from {row["vendor"]} ==================')
                get_invoice_text(driver=driver, vendor=row['vendor'].split(" / ")[-1], invoice_num=row['invoice_num'])
                filtered_df.at[index, 'status'] = 'Success'
            else:
                pass
        except Exception as e:  # Catching the generic Exception unless you have a specific one to catch
            filtered_df.at[index, 'status'] = 'Failed'
            logging.error(e)
            # driver.quit()
            # sys.exit(1)
        finally:
            try:
                filtered_df = filtered_df.drop(columns='vendor_id')
            except Exception as e: 
                pass
            folder.upload_file(filtered_df.to_csv(index=False, sep=';'), 'bot_status.csv')

if __name__ == '__main__':
    main()

