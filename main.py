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

def filtering_invoice(driver, company="Spartao", status="All", supplier=False, invoice_num=False):

    with iframe_context(driver, 'main_iframe'):
        select_company = Select(wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/select"), 'change company selection to all', clickable=False)).select_by_visible_text(company)
        inv_num_input = wait_for_element(driver, (By.ID, "InvoiceNumberCtrl"), 'clear invoice number and input').send_keys(invoice_num)
        supplier_input = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[1]/div[2]/div/input"), 'clear supplier name and input').send_keys(expressions[supplier][0])
        if expressions[supplier][0] == "AB Tingstad Papper":
            status = "Data Incomplete"
        select_status = Select(wait_for_element(driver, (By.XPATH, "/html/body/div[1]/form/div[3]/div[5]/select"), 'change process invoice filter status', clickable=False)).select_by_visible_text(status)
        update_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/form/div[3]/div[6]/input"), 'find update button and click').click()


def try_click_invoice_button(driver, vendor, invoice_num, statuses=["Data Incomplete", "All"]):
    """
    Attempts to click on the invoice button for given statuses.
    """
    # Loop through statuses
    for status in statuses:
        try:
            filtering_invoice(driver, supplier=vendor, status=status, invoice_num=invoice_num)
            with iframe_context(driver, 'main_iframe'):
                # Determine the correct XPATH based on the status
                xpath = '/html/body/div/form/div[4]/table/tbody/tr[2]/td[11]/a' if status == "All" else '/html/body/div/form/div[4]/table/tbody/tr[2]/td[12]/a'
                invoice_button = wait_for_element(driver, (By.XPATH, xpath), f'attempting find invoice button with status {status}')
                invoice_button.click()
                return True  # Stop trying after successful click
        except Exception as e:
            logging.error(f"Attempt with status '{status}' failed.")

    # If we reach this point, all attempts have failed
    logging.error(f"Failed to find the invoice button for invoice number: {invoice_num}")
    return False


def get_invoice_text(driver, vendor, invoice_num):
    nav_to_purchase_invoice(driver)
    try_click_invoice_button(driver, vendor, invoice_num)

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
        logging.info("Step: extacting the posting value.")
        text = read_pdf_text(file_type='pdf')
        posting_info = info_extractor(text=text, vendor=vendor)
        posting_info['INV No.'] = invoice_num

    with iframe_context(driver, 'info_iframe'):
        organizational_unit_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[2]/td[2]/div/div/button'), 'find the organizational unit and click').click()

    with iframe_context(driver, 'dialog_iframe'):
        select_org_unit_btn = wait_for_element(driver, (By.XPATH, "/html/body/div/div[2]/form/div[4]/input[1]"), 'select the default org unit').click()

    with iframe_context(driver, 'info_iframe'):
        if vendor == "1381774" or vendor == "1433275":
            due_date = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[1]/div[2]/table/tbody/tr[14]/td[2]/div[1]/div/div/input'), 'modifing the S-Card/Kesko invoices due date to current date').send_keys(dt.datetime.today().strftime("%d.%m.%Y"))
        if vendor == "1301716":
            ref_field =  wait_for_element(driver, (By.ID, 'ReferenceCtrl'), 'find the ref number and clear the field').clear()
            msg_field = wait_for_element(driver, (By.ID, 'MessageCtrl'), 'find the ref number and clear the field').send_keys(invoice_num)

    try:
        with iframe_context(driver, 'error_iframe'):
            next_time_check = wait_for_element(driver, (By.XPATH, '/html/body/div/div[3]/span/label'), 'find the show next time check and click', silent=True).click()
            next_ok_btn = wait_for_element(driver, (By.XPATH, '//*[@id="yesbutton"]'), 'find the don\'t show next time check and click', silent=True).click()
    except:
        pass

    if 'approver' in posting_info.keys():
        with iframe_context(driver, 'info_iframe'):
            if 'approver' in posting_info:
                logging.info("Updating approver.")
                processor_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[5]/input[2]'), 'find the processor button and click').click()

        with iframe_context(driver, 'dialog_iframe'):
            current_processor_select = Select(wait_for_element(driver, (By.XPATH,"/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[3]/div/select"), 'find the current processor select'))
            reset_processor = True
            for option in current_processor_select.options:
                if option.text == f"Approve: {posting_info['approver']}":
                    reset_processor = False
                    cancel_btn = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[4]/input[2]'), 'find the cancel button and click').click()
            if reset_processor:
                processor_list = Select(wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[1]/div/select'), 'find the processor list'))
                processor_list.select_by_visible_text(posting_info['approver'])
                add_processor_btn = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[3]/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td/table/tbody/tr[1]/td/input'), 'find the add processor button and click').click()
                conform_processor = wait_for_element(driver, (By.XPATH, '/html/body/div/div[2]/form/div[4]/input[1]'), 'find the conform processor button and click').click()

    with iframe_context(driver, 'info_iframe'):
        post_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[2]/input[3]'), 'find the post button and click').click()

    try:
        with iframe_context(driver, 'error_iframe'):
            next_time_check = wait_for_element(driver, (By.XPATH, '/html/body/div/div[3]/span/label'), 'find the show next time check and click', silent=True).click()
            next_ok_btn = wait_for_element(driver, (By.XPATH, '//*[@id="yesbutton"]'), 'find the don\'t show next time check and click', silent=True).click()
    except:
        pass


    try:
        with iframe_context(driver, 'action_iframe'):
            delete_posting = wait_for_element(driver, (By.ID, 'DeletePostingButton'), 'click delete posting value').click()
            alert = Alert(driver).accept()
    except:
        logging.info(f"Posting values are empty, no need to delete posting.")
        pass
    if vendor != "1301716":
        with iframe_context(driver, 'posting_iframe'):
            posting_sum = Select(wait_for_element(driver, (By.ID, "PostingControl1_VATHandlingCtrl"), 'find the posting sum'))
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
                    save_btn = wait_for_element(driver, (By.XPATH, "/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]"), 'find the save button and click').click()

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
                        save_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[3]/td[9]/a[1]'), 'find the save button and click').click()

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

    try:
        with iframe_context(driver, 'error_iframe'):
            next_time_check = wait_for_element(driver, (By.XPATH, '/html/body/div/div[3]/span/label'), 'find the show next time check and click', silent=True).click()
            next_ok_btn = wait_for_element(driver, (By.XPATH, '//*[@id="yesbutton"]'), 'find the don\'t show next time check and click', silent=True).click()
    except:
        pass

    if vendor == "1301716" or vendor == "1367729":
        with iframe_context(driver, 'posting_iframe'):
            save_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div/div[3]/table/tbody/tr[2]/td[9]/a[1]'), 'find the save button and click').click()
    with iframe_context(driver, 'action_iframe'):
        ok_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/input[1]'), 'find the OK button and click').click()


    try:
        with iframe_context(driver, 'error_iframe'):
            next_time_check = wait_for_element(driver, (By.XPATH, '/html/body/div/div[3]/span/label'), 'find the show next time check and click', silent=True).click()
            next_ok_btn = wait_for_element(driver, (By.XPATH, '//*[@id="yesbutton"]'), 'find the don\'t show next time check and click', silent=True).click()
            next_ok_btn_ = wait_for_element(driver, (By.XPATH, '/html/body/div/div[5]/input'), 'find the don\'t show next time check and click', silent=True).click()
    except:
        pass


    with iframe_context(driver, 'info_iframe'):
        save_inv_btn = wait_for_element(driver, (By.XPATH, '/html/body/form/div[3]/div[2]/input[1]'), 'find the save invoice button and click').click()
    return True


def main():
    load_dotenv()
    bot_input = download_csv_data()
    bot_input = bot_input[bot_input['status'] != "Success"]
    operational_data = get_inv_number(bot_input)
    filtered_df = operational_data[operational_data['status'].isin([np.nan, 'Failed'])]

    driver = setup_driver(download_path=os.path.join(os.getcwd(), os.getenv('TEMP_DIRECTORY', 'temp')))

    driver.switch_to.default_content()
    if bw_login(driver, username=os.getenv('BW_USR'), password=os.getenv('BW_PSW'), login_url=os.getenv('BW_URL')):

        for index, row in filtered_df.iterrows():
            try:
                if row['status'] != 'Success':
                    logging.info(f'==================================== Processing invoice {row["invoice_num"]} from {row["vendor"]} ====================================')
                    reset_folder(os.path.join(os.getcwd(), os.getenv('TEMP_DIRECTORY', 'temp')))
                    get_invoice_text(driver=driver, vendor=row['vendor'].split(" / ")[-1], invoice_num=row['invoice_num'])
                    filtered_df.at[index, 'status'] = 'Success'
                    logging.info(f"Invoice {row['invoice_num']} from {row['vendor']} has been processed successfully!")

            except Exception as e:
                timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(os.getcwd(), f"screenshot_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                filtered_df.at[index, 'status'] = 'Failed'
                logging.error(f"Invoice {row['invoice_num']} from {row['vendor']} failed! Error message: {e}")
            finally:
                try:
                    filtered_df = filtered_df.drop(columns='vendor_id')
                except Exception as e: 
                    pass
                upload_invoice_data(filtered_df)


if __name__ == '__main__':
    main()