# -*- coding: utf-8 -*-
import io
import os
import logging
import time
import datetime as dt

import numpy as np
from dotenv import load_dotenv

from selenium.webdriver.support.ui import Select
from drivers.webdriver import setup_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config.logger_config import setup_logging
from extractor import info_extractor, expressions
from utils.pdf_utils import read_pdf_text
from utils.file_utils import reset_folder
from utils.webdriver_utils import wait_for_element, iframe_context
from services.authentication import bw_login
from services.sharepoint import download_csv_data, upload_invoice_data

setup_logging()

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


def nav_to_purchase_invoice(driver):
    purchase_invoices = wait_for_element(driver, (By.ID, 'Menu1-menuItem003'), "navigate to purchase invoices")
    action = ActionChains(driver).move_to_element(purchase_invoices).perform()
    process_purchase_invoices = wait_for_element(driver, (By.XPATH, '/html/body/form/table[4]/tbody/tr[2]/td/table/tbody/tr/td[1]'), 'navigate to process purchase invoices').click()

def nav_to_archive(driver):
    purchase_invoices = wait_for_element(driver, (By.ID, 'Menu1-menuItem004'), "navigate to archive")
    action = ActionChains(driver).move_to_element(purchase_invoices).perform()
    search_archive = wait_for_element(driver, (By.XPATH, '/html/body/form/table[5]/tbody/tr[1]/td/table/tbody/tr/td[1]'), 'navigate to search').click()

def filtering_invoice(driver, company="Spartao", status="All", supplier=False, invoice_num=False):
    with iframe_context(driver, 'main_iframe'):
        select_company = Select(wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/select"), 'change company selection to all', clickable=False)).select_by_visible_text(company)
        inv_num_input = wait_for_element(driver, (By.ID, "InvoiceNumberCtrl"), 'clear invoice number and input').send_keys(invoice_num)
        supplier_input = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/div[2]/div/input"), 'clear supplier name and input').send_keys(expressions[supplier][0])
        if expressions[supplier][0] == "AB Tingstad Papper":
            status = "Data Incomplete"
        select_status = Select(wait_for_element(driver, (By.XPATH, "/html/body/div[1]/form/div[3]/div[5]/select"), 'change process invoice filter status', clickable=False)).select_by_visible_text(status)
        update_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[6]/input"), 'find update button and click').click()

def filtering_archive(driver, invoice_num=False):
    with iframe_context(driver, 'main_iframe'):
        change_tab = wait_for_element(driver, (By.ID, "tabLnk3"), 'change tab to search').click()
        invoice_number_input = wait_for_element(driver, (By.ID, "CTRL_13a54b7263b344feb12eeb115345c055_TEXTBOX"), 'clear invoice number and input').send_keys(invoice_num)
        search_btn = wait_for_element(driver, (By.ID, "SearchButton"), 'find search button and click').click()

def try_click_invoice_button(driver, invoice_num):
    """
    Attempts to click on the invoice button for given statuses.
    """
    # Loop through statuses
    try:
        with iframe_context(driver, 'main_iframe'):
            # Determine the correct XPATH based on the status
            invoice_button = wait_for_element(driver, (By.XPATH, "/html/body/form/div[3]/div/table/tbody/tr[2]/td[1]/a"), f'attempting find invoice button').click()
            return True  # Stop trying after successful click
    except Exception as e:
        logging.error(f"Attempt with invoice '{invoice_num}' failed.")

    # If we reach this point, all attempts have failed
    logging.error(f"Failed to find the invoice button for invoice number: {invoice_num}")
    return False


def get_invoice_pdf(driver, vendor, invoice_num):
    nav_to_archive(driver)
    filtering_archive(driver, invoice_num=invoice_num)

    try_click_invoice_button(driver, invoice_num)

    try:
        with iframe_context(driver, 'error_iframe'):
            override_lock_status_button = wait_for_element(driver, (By.XPATH, '/html/body/div/div[4]/input[1]'), 'try to override the lock frame and click', silent=True).click()
    except:
        pass

    logging.info("Step: downloading the pdf.")
    with iframe_context(driver, 'viewer_iframe'):
        try:
            save_pdf_btn = wait_for_element(driver, (By.ID, 'open-button'), 'find the pdf attachement save btn', clickable=False, silent=True).click()
        except (NoSuchElementException, TimeoutException):
            logging.debug("Save PDF button not found or not clickable, but continuing since the file downloads successfully.")
        time.sleep(2)


def main():
    load_dotenv()
    bot_input = download_csv_data()
    bot_input = bot_input[bot_input['status'] != "Success"]
    operational_data = get_inv_number(bot_input)
    filtered_df = operational_data.copy()

    driver = setup_driver(download_path=os.path.join(os.getcwd(), os.getenv('TEMP_DIRECTORY', 'temp')))

    driver.switch_to.default_content()
    if bw_login(driver, username=os.getenv('BW_USR'), password=os.getenv('BW_PSW'), login_url=os.getenv('BW_URL')):

        for index, row in filtered_df.iterrows():
            try:
                if row['status'] != 'Success':
                    logging.info(f'==================================== Processing invoice {row["invoice_num"]} from {row["vendor"]} ====================================')
                    get_invoice_pdf(driver=driver, vendor=row['vendor'].split(" / ")[-1], invoice_num=row['invoice_num'])
                    filtered_df.at[index, 'status'] = 'Success'
                    logging.info(f"Invoice {row['invoice_num']} from {row['vendor']} has been processed successfully!")

            except Exception as e:
                filtered_df.at[index, 'status'] = 'Failed'
                logging.error(f"Invoice {row['invoice_num']} from {row['vendor']} failed! Error message: {e}")
            finally:
                try:
                    filtered_df = filtered_df.drop(columns='vendor_id')
                except Exception as e: 
                    pass
                upload_invoice_data(filtered_df, 'bot_status.csv')



if __name__ == '__main__':
    main()

