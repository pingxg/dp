# -*- coding: utf-8 -*-
import io
import sys
import os
from os import system
import datetime as dt
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

from selenium.common.exceptions import TimeoutException

from contextlib import contextmanager


from extractor import info_extractor, expressions
import logging
import logger_config

logger_config.setup_logging()

TEMP_PATH = os.path.join(os.getcwd(), 'temp')

# Check if the folder exists, and if not, create it
if not os.path.exists(TEMP_PATH):
    os.makedirs(TEMP_PATH)
    logging.info(f"Created temp folder at: {TEMP_PATH}")
else:
    logging.info(f"Temp folder already exists at: {TEMP_PATH}")

def wait_for_element(driver, locator, timeout=10, clickable=True):
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
            return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
        else:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
    except TimeoutException:
        logging.error(f"Element with locator {locator} not found within {timeout} seconds.")
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
        wait_for_element(driver, (By.ID, "txtUsername")).send_keys(username)
        wait_for_element(driver, (By.ID, "txtPasswd")).send_keys(password)
        wait_for_element(driver, (By.ID, "btnLogin")).click()
        logging.info("Login successful")
    except Exception as e:
        logging.error(f"Login failed: {e}")


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
        logging.error(
            "No valid information found in bw_bot_log.csv to process!")
        pass
    try:
        df['vendor_id'] = df['vendor'].str.split(' / ', expand=True)[1]
        supported_vendor = list(expressions.keys())

        df.drop_duplicates(inplace=True)
        df.loc[~df['vendor_id'].isin(supported_vendor),
               'status'] = 'Not Supported'

    except:
        logging.info("No data in the bot input file!")
        return False
    return df


def delete_file_by_type(path=TEMP_PATH, file_type='pdf'):
    files = [f for f in os.listdir(path)]
    files = list(
        filter(
            lambda f: f.endswith((f'.{file_type}', f'.{file_type.upper()}')),
            files))

    for i in files:
        os.remove(os.path.join(path, i))


def read_pdf_text(path=TEMP_PATH, file_type='pdf'):
    """
    Read the text content from a PDF file.

    Parameters:
    - path (str): The path to the folder containing the PDF files. Default is TEMP_PATH.
    - file_type (str): The file extension to search for. Default is 'pdf'.

    Returns:
    - str: The extracted text content if a single PDF file is found. Otherwise returns None.
    """
    files = [f for f in os.listdir(path)]
    files = list(
        filter(lambda f: f.endswith((f'.{file_type}', f'.{file_type.upper()}')), files))
    if len(files) == 1:
        with pdfplumber.open(os.path.join(path, files[0])) as pdf:
            pdfToString = "".join(page.extract_text() for page in pdf.pages)
        delete_file_by_type()
        return pdfToString



def filtering_invoice(
    driver,
    company="Spartao",
    status="All",
    supplier=False,
    invoice_num=False,
):
    driver.switch_to.default_content()


    purchase_invoices = wait_for_element(driver, (By.XPATH, '/html/body/form/table[12]/tbody/tr/td[6]'))
    purchase_invoices.click()
    process_purchase_invoices = wait_for_element(driver, (By.XPATH, '/html/body/form/table[4]/tbody/tr[2]/td/table/tbody/tr/td[1]'))
    process_purchase_invoices.click()


    global applicationframe
    applicationframe = wait_for_element(driver, (By.XPATH, "/html/body/div[1]/iframe"), clickable=False)
    driver.switch_to.frame(applicationframe)

    global mainframehdr
    mainframehdr = wait_for_element(driver, (By.ID, "mainframehdr"))
    global mainframe
    mainframe = wait_for_element(driver, (By.XPATH, "/html/body/div[2]/iframe"))

    driver.switch_to.frame(mainframe)

    select_company = Select(wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/select"), clickable=False))
    select_company.select_by_visible_text(company)

    inv_num_input = wait_for_element(driver, (By.ID, "InvoiceNumberCtrl"))
    inv_num_input.clear()
    logging.error(f"inv_num_input: {inv_num_input}")

    if invoice_num:
        inv_num_input.send_keys(invoice_num)

    supplier_input = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/div[2]/div/input"))
    supplier_input.clear()
    logging.error(f"supplier_input: {supplier_input}")

    if supplier:
        supplier_input.send_keys(expressions[supplier][0])

    if expressions[supplier][0] == "AB Tingstad Papper":
        status = "Data Incomplete"

    select_status = Select(wait_for_element(driver, (By.XPATH, "/html/body/div[1]/form/div[3]/div[5]/select"), clickable=False))
    select_status.select_by_visible_text(status)

    update_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[6]/input"))
    update_btn.click()


def get_invoice_text(vendor, invoice_num):
    filtering_invoice(driver, supplier=vendor, invoice_num=invoice_num)
    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    logging.info("Checking Tingstad...")
    if vendor != "1301716":
        is_tingstad = False
        invoice_button = wait_for_element(driver, (By.XPATH, '/html/body/div/form/div[4]/table/tbody/tr[2]/td[11]/a'))

    elif vendor == "1301716":
        is_tingstad = True
        invoice_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '/html/body/div/form/div[4]/table/tbody/tr[2]/td[12]/a')))
    logging.info(f"Tingstad: {is_tingstad}")
    driver.execute_script("arguments[0].click();", invoice_button)
    try:
        driver.switch_to.default_content()
        errorframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/iframe')))
        driver.switch_to.frame(errorframe)
        override_lock_status_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div/div[4]/input[1]')))
        override_lock_status_button.click()
    except:
        pass
    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    logging.info("Downloading the pdf...")
    attachment_frame = wait_for_element(driver, 
            (By.XPATH, '/html/body/div/div/div/div[3]/iframe'))
    driver.switch_to.frame(attachment_frame)

    viewer_frame = wait_for_element(driver, 
            (By.XPATH, '/html/body/form/div[3]/div/iframe'))
    driver.switch_to.frame(viewer_frame)


    save_button = wait_for_element(driver, (By.XPATH, 'html/body/div/div/a/button'))
    save_button.click()

    logging.info("Extacting the posting value...")
    posting_info = info_extractor(text=read_pdf_text(file_type='pdf'),
                                  vendor=vendor)
    logging.info(f"Posting info: {posting_info}")

    posting_info['INV No.'] = invoice_num

    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    global info_page_frame
    info_page_frame = wait_for_element(driver, (By.XPATH, '/html/body/div/div/div/div[1]/iframe'))

    driver.switch_to.frame(info_page_frame)

    organizational_unit_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]/div/div/button'))
    driver.execute_script("arguments[0].click();", organizational_unit_btn)

    driver.switch_to.default_content()
    dialog_frame = wait_for_element(driver, 
            (By.XPATH, "/html/body/div[3]/div/iframe"))
    driver.switch_to.frame(dialog_frame)
    select_org_unit_btn = wait_for_element(driver, 
            (By.XPATH, "/html/body/div/div[2]/form/div[4]/input[1]"))
    select_org_unit_btn.click()

    driver.switch_to.default_content()
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    driver.switch_to.frame(info_page_frame)
    post_btn = wait_for_element(driver, 
            (By.XPATH, '/html/body/form/div[3]/div[2]/input[3]'))
    if vendor == "1381774":
        logging.info("Modifing the S-Card due date...")
        due_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[14]/td[2]/div[1]/div/div/input'
            )))
        due_date.clear()
        due_date.send_keys(dt.datetime.today().strftime("%d.%m.%Y"))
        # post_btn.click()
    elif is_tingstad is True:
        logging.info("Modifing the Tingstad invoice info...")
        ref_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[13]/td[2]/input'
            )))
        logging.info(f"ref_field: {ref_field}")
        ref_field.clear()
        msg_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[12]/td[2]/textarea'
            )))
        logging.info(f"msg_field: {msg_field}")

        msg_field.clear()
        msg_field.send_keys(str(invoice_num))
        po_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[3]/td[2]/div[1]/div/div/input'
            )))
        logging.info(f"po_field: {po_field}")

        po_field.clear()
        total_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[15]/td[2]/div[1]/input'
            )))
        logging.info(f"total_field: {total_field}")
        inv_total = total_field.get_attribute('value')
        total_field.click()
        click_random_location = ActionChains(driver)
        click_random_location.move_by_offset(1000, 500).click().perform()
        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        driver.switch_to.frame(info_page_frame)
        post_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/form/div[3]/div[2]/input[3]')))
        logging.info(f"post_btn: {post_btn}")
        driver.execute_script("arguments[0].click();", post_btn)
    
    try:
        driver.execute_script("arguments[0].click();", post_btn)
    except:
        pass

    try:
        driver.switch_to.default_content()
        driver.switch_to.frame(errorframe)
        next_time_check = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div/div[3]/span/label')))
        next_time_check.click()
        driver.switch_to.default_content()
        driver.switch_to.frame(errorframe)
        next_ok_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="yesbutton"]')))
        next_ok_btn.click()

        # driver.execute_script("arguments[0].click();", popup_ok)
    except:
        pass

    try:
        logging.info("Deleting the old posting info...")

        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        action_frame = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/form/div[3]/iframe')))
        # /html/body/form/div[3]/iframe
        driver.switch_to.frame(action_frame)
        # delete_posting = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located(
        #         (By.XPATH, '/html/body/form/div[3]/input[2]')))
        delete_posting = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/form/div[3]/input[2]')))
        driver.execute_script("arguments[0].click();", delete_posting)

        ""
        # create alert object
        alert = Alert(driver)

        # get alert text
        # logging.info(alert.text)

        # accept the alert
        alert.accept()

    except:
        pass

    driver.switch_to.default_content()
    logging.info("Open posting page...")
    driver.switch_to.frame(applicationframe)
    driver.switch_to.frame(mainframe)
    posting_frame = wait_for_element(driver, 
            (By.XPATH, '/html/body/form/div[2]/div[3]/iframe'))
    driver.switch_to.frame(posting_frame)
    posting_sum = Select(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/form/div[3]/div/div[2]/select"))))
    logging.info("Updating posting values...")
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
                logging.info("Updating department...")
                department = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'
                    )))

                department.clear()
                department.send_keys(posting_info['department'])

            if 'class_code' in posting_info:
                logging.info("Updating class...")
                
                class_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'
                    )))

                class_code.clear()
                class_code.send_keys(posting_info['class_code'])

            location = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'
                )))
            location.clear()
            location.send_keys(posting_info['location'])

        if '14' in posting_info:
            logging.info("Updating 14% row...")
            if 'department' in posting_info:
                # posting_sum.select_by_visible_text("Tax included")
                department = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'
                    )))
                department.clear()
                department.send_keys(posting_info['department'])
                logging.info("Updating department...")

            if 'class_code' in posting_info:

                
                class_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'
                    )))

                class_code.clear()
                class_code.send_keys(posting_info['class_code'])
                logging.info("Updating class...")

            
            location = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'
                )))
            
            location.clear()
            
            logging.info("Updating location...")

            location.send_keys(posting_info['location'])
            

            posting_sum.select_by_visible_text("Tax included")
            logging.info("Change to Tax included...")
            if posting_info['14_total'] >= 0:
                logging.info("Updating debit amount...")
                debit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[7]/input'
                    )))
                debit.clear()
                debit.send_keys(
                    str(posting_info['14_total']).replace('.', ','))

            elif posting_info['14_total'] < 0:
                logging.info("Updating credit amount...")

                credit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'
                    )))
                credit.clear()
                credit.send_keys(
                    str(-posting_info['14_total']).replace('.', ','))
            tax_code = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'
                )))
            tax_code.clear()
            tax_code.send_keys('8')
            logging.info("Updating tax code...")

            driver.switch_to.default_content()
            driver.switch_to.frame(applicationframe)
            driver.switch_to.frame(mainframe)
            driver.switch_to.frame(posting_frame)
            logging.info(posting_frame)
            save_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]"
                )))
            logging.info(save_btn)

            
            # logging.info('Clicking save button...')

            driver.execute_script("arguments[0].click();", save_btn)
            # save_btn.click()

            if '24' in posting_info:
                logging.info("Updating 24% row...")
                if 'department' in posting_info:

                    department = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'
                            '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[2]/div/div/input'
                        )))
                    department.clear()
                    department.send_keys(posting_info['department'])

                if 'class_code' in posting_info:

                    
                    class_code = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'
                            '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[4]/div/div/input'
                        )))

                    class_code.clear()
                    class_code.send_keys(posting_info['class_code'])

                location = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[3]/div/div/input'
                    )))
                location.clear()

                location.send_keys(posting_info['location'])
                if posting_info['24_total'] >= 0:
                    debit = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[7]/input'
                        )))
                    debit.clear()
                    debit.send_keys(
                        str(posting_info['24_total']).replace('.', ','))

                elif posting_info['24_total'] < 0:
                    credit = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'
                            '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[8]/input'
                        )))
                    credit.clear()
                    credit.send_keys(
                        str(-posting_info['24_total']).replace('.', ','))
                    
                tax_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[5]/div/div/input'
                    )))
                tax_code.clear()
                tax_code.send_keys('6')
                save_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        # '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]'
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[9]/a[1]'
                    )))

                driver.execute_script("arguments[0].click();", save_btn)

        if '24' in posting_info and '14' not in posting_info:
            logging.info("Updating 24% row only...")
            if 'department' in posting_info:
                # posting_sum.select_by_visible_text("Tax included")
                department = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'
                    )))
                department.clear()
                department.send_keys(posting_info['department'])

            if 'class_code' in posting_info:

                
                class_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'
                    )))

                class_code.clear()
                class_code.send_keys(posting_info['class_code'])

            location = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'
                )))
            location.clear()

            location.send_keys(posting_info['location'])

            posting_sum.select_by_visible_text("Tax included")
            if posting_info['24_total'] >= 0:
                debit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[7]/input'
                    )))
                debit.clear()
                debit.send_keys(
                    str(posting_info['24_total']).replace('.', ','))

            elif posting_info['24_total'] < 0:
                credit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'
                    )))
                credit.clear()
                credit.send_keys(
                    str(-posting_info['24_total']).replace('.', ','))
            tax_code = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'
                )))
            tax_code.clear()
            tax_code.send_keys('6')
            save_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]'
                )))
            driver.execute_script("arguments[0].click();", save_btn)

        if '24' not in posting_info and '14' not in posting_info and is_tingstad is True:
            logging.info("Updating Tingstad row only...")
            if 'department' in posting_info:
                # posting_sum.select_by_visible_text("Tax included")
                department = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[2]/div/div/input'
                    )))
                department.clear()
                department.send_keys(posting_info['department'])

            if 'class_code' in posting_info:

                
                class_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[4]/div/div/input'
                    )))

                class_code.clear()
                class_code.send_keys(posting_info['class_code'])

            location = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[3]/div/div/input'
                )))
            location.clear()

            location.send_keys(posting_info['location'])

            if inv_total >= 0:
                debit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[7]/input'
                    )))
                debit.clear()
                debit.send_keys(str(inv_total).replace('.', ','))

            elif inv_total < 0:
                credit = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[8]/input'
                    )))
                credit.clear()
                credit.send_keys(str(-inv_total).replace('.', ','))
            tax_code = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[5]/div/div/input'
                )))
            tax_code.clear()
            tax_code.send_keys('17')
            save_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]'
                )))
            driver.execute_script("arguments[0].click();", save_btn)

        

        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        action_frame = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/form/div[3]/iframe')))
        logging.info(f'Action frame: {action_frame}')

        

        driver.switch_to.frame(action_frame)

        ok_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/form/div[3]/input[1]')))
        logging.info(f'OK button: {ok_btn}')

        driver.execute_script("arguments[0].click();", ok_btn)


        
        driver.switch_to.default_content()
        driver.switch_to.frame(applicationframe)
        driver.switch_to.frame(mainframe)
        
        info_page_frame = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div/div/div/div[1]/iframe')))
        logging.info(f'Info page frame: {info_page_frame}')

        driver.switch_to.frame(info_page_frame)

        if 'approver' in posting_info:
            logging.info("Updating approver...")
            processor_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '/html/body/form/div[5]/input[2]')))

            driver.execute_script("arguments[0].click();", processor_btn)
            driver.switch_to.default_content()
            processor_frame = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '/html/body/div[3]/div/iframe')))
            driver.switch_to.frame(processor_frame)

            current_processor_select = Select(
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[3]/div/select"
                    ))))
            reset_processor = True
            for option in current_processor_select.options:
                if option.text == f"Approve: {posting_info['approver']}":
                    reset_processor = False
                    cancel_btn = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH,
                             '/html/body/div/div[2]/form/div[4]/input[2]')))
                    driver.execute_script("arguments[0].click();", cancel_btn)

            if reset_processor:

                processor_list = Select(
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[1]/div/select'
                        ))))
                processor_list.select_by_visible_text(posting_info['approver'])

                
                add_processor_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td/table/tbody/tr[1]/td/input'
                    )))
                driver.execute_script("arguments[0].click();",
                                      add_processor_btn)
                conform_processor = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         '/html/body/div/div[2]/form/div[4]/input[1]')))
                driver.execute_script("arguments[0].click();",
                                      conform_processor)
            driver.switch_to.default_content()
            driver.switch_to.frame(applicationframe)
            driver.switch_to.frame(mainframe)
            driver.switch_to.frame(info_page_frame)
            save_inv_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '/html/body/form/div[3]/div[2]/input[1]')))
            driver.execute_script("arguments[0].click();", save_inv_btn)
        logging.info(
            f'Invoice {invoice_num} from {expressions[vendor][0]} has been processed successfully!'
        )
        return True


if __name__ == '__main__':
    authcookie = Office365(os.getenv('office_site'),
                           username=os.getenv('office_usn'),
                           password=os.getenv('office_psw'))
    
    site = Site('https://oyspartao.sharepoint.com/sites/SpartaoFinance',
                version=Version.v365,
                authcookie=authcookie.GetCookies())
    folder = site.Folder('Shared Documents')

    data = io.StringIO(
        str(folder.get_file('bot_status.csv'), 'ISO-8859-1', errors='replace'))

    bot_input = pd.read_csv(data, sep=';')
    bot_input = bot_input[bot_input['status'] != "Success"]

    operational_data = get_inv_number(bot_input)


    filtered_df = operational_data[operational_data['status'].isin(
        [np.nan, 'Failed'])]
    logging.error(filtered_df)

    chrome_options = Options()
    prefs = {
        "download.default_directory": TEMP_PATH,
        "plugins.always_open_pdf_externally": True,
        "download.prompt_for_download": False,
        "plugins.plugins_list": [{
            "enabled": False,
            "name": "Chrome PDF Viewer"
        }],
        "download.extensions_to_open": "applications/pdf",
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument('--disable-dev-shm-usage')


    driver = webdriver.Chrome(options=chrome_options,
                              executable_path=r'/usr/bin/chromedriver')
                            #   executable_path=r'C:\Program Files\chromedriver.exe')
                            #   service=Service(ChromeDriverManager().install()))
    
    login(driver)
    logging.error(filtered_df)

    for index, row in filtered_df.iterrows():
        try:
            if row['status'] != 'Success':
                get_invoice_text(vendor=row['vendor'].split(" / ")[-1],
                                 invoice_num=row['invoice_num'])

                filtered_df.at[index, 'status'] = 'Success'
            else:
                pass
        except Exception as e:  # Catching the generic Exception unless you have a specific one to catch
            filtered_df.at[index, 'status'] = 'Failed'

            # This will logging.info the type of exception and the message
            # logging.info(f"An error occurred: {repr(e)}")

            # If you want the full traceback, you can use:
            logging.error(e)
            driver.quit()
            sys.exit(1)
            # logging.error("\n\nRESTARTING NOW\n\n")
            # system("python restarter.py")
            # system('kill 1')

        finally:
            try:
                filtered_df = filtered_df.drop(columns='vendor_id')
            except Exception as e: 
                pass
            folder.upload_file(filtered_df.to_csv(index=False, sep=';'),
                               'bot_status.csv')
