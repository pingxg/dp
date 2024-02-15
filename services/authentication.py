import sys
import logging
from selenium.webdriver.common.by import By
from utils.webdriver_utils import wait_for_element

def bw_login(driver, username, password, login_url):
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
        return True
    except Exception as e:
        logging.error(f"Login failed: {e}")
        sys.exit(1)

