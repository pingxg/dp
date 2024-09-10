import logging
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models.custom_elements import CustomWebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.iframe_config import IFRAME_HIERARCHY

logging = logging.getLogger(__name__)


def wait_for_element(
    driver, locator, step_name="not specified", timeout=10, clickable=True, silent=False
):
    """
    Enhanced with more detailed logging.
    """
    try:
        if clickable:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            logging.info(f"{step_name}: Clickable element {locator} found.")
        else:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            logging.info(f"{step_name}: Element {locator} found.")

        element.__class__ = CustomWebElement
        return element

    except TimeoutException as e:
        if not silent:
            logging.warning(
                f"{step_name}: Element with locator {locator} not found within {timeout} seconds."
            )
        raise


def switch_to_iframe_by_name(driver, iframe_name):
    """
    Switches to an iframe by its name by navigating through the iframe hierarchy.
    Collects the 'breadcrumbs' (locator paths) to reach the target iframe,
    then switches through each iframe sequentially to reach the target.
    """
    breadcrumbs = []

    def find_and_switch(iframe_name, iframe_config=IFRAME_HIERARCHY):
        for key, value in iframe_config.items():
            if key == iframe_name:
                breadcrumbs.append(value["locator"])
                return True
            elif "children" in value:
                breadcrumbs.append(value["locator"])  # Add parent iframe locator
                if find_and_switch(iframe_name, value["children"]):
                    return True
                breadcrumbs.pop()  # Remove parent iframe locator if not the correct path
        return False

    if not find_and_switch(iframe_name, IFRAME_HIERARCHY):
        logging.error(f"Iframe named '{iframe_name}' not found in hierarchy.")
        raise NoSuchElementException(
            f"Iframe named '{iframe_name}' not found in hierarchy."
        )
    # Switch through iframes using breadcrumbs
    for locator in breadcrumbs:
        try:
            # Assuming wait_for_element is defined to wait and return the element
            iframe_element = wait_for_element(
                driver, locator, "Switching to iframe", clickable=False, silent=True
            )
            driver.switch_to.frame(iframe_element)
        except TimeoutException:
            logging.error(f"Failed to switch to iframe with locator {locator}")
            raise


def switch_to_default_content(driver):
    """
    Enhanced with logging for clarity.
    """
    driver.switch_to.default_content()


@contextmanager
def iframe_context(driver, iframe_name):
    """
    Context manager for switching to an iframe by name and automatically returning to default content.
    """
    try:
        switch_to_iframe_by_name(driver, iframe_name)
        yield
    finally:
        switch_to_default_content(driver)
