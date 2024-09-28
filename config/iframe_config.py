from selenium.webdriver.common.by import By


IFRAME_HIERARCHY = {
    "application_iframe": {
        "locator": (By.ID, "applicationframe"),
        "name": "Application Frame",
        "children": {
            "main_iframe_header": {
                "locator": (By.ID, "mainframehdr"),
                "name": "Main Frame Header",
                "children": {},
            },
            "main_iframe": {
                "locator": (By.ID, "mainframe"),
                "name": "Main Frame",
                "children": {
                    "info_iframe": {
                        "locator": (By.ID, "infoPage"),
                        "name": "Info Frame",
                        "children": {},
                    },
                    "attachment_iframe": {
                        "locator": (By.ID, "attachmentPage"),
                        "name": "Attachment Frame",
                        "children": {
                            "viewer_iframe": {
                                "locator": (By.ID, "ViewerFrame"),
                                "name": "Viewer Frame",
                                "children": {},
                            }
                        },
                    },
                    "action_iframe": {
                        "locator": (By.ID, "actions"),
                        "name": "Action Frame",
                        "children": {},
                    },
                    "posting_iframe": {
                        "locator": (By.ID, "postingPage"),
                        "name": "Posting Frame",
                        "children": {},
                    },
                },
            },
        },
    },
    "error_iframe": {
        "locator": (By.ID, "errorframe"),
        "name": "Error Frame",
        "children": {},
    },
    "dialog_iframe": {
        "locator": (By.ID, "ifa1"),
        "name": "Dialog Frame",
        "children": {},
    },
}
