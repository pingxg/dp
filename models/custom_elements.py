from selenium.webdriver.remote.webelement import WebElement


# Define a new class that extends WebElement
class CustomWebElement(WebElement):
    def send_keys(self, keys):
        self.clear()  # Clear the text field before sending keys
        super().send_keys(keys)  # Call the original send_keys method
