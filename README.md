# Basware AP automation

## Description

This project is a web automation tool designed to interact with a SharePoint site for downloading, processing, and uploading invoice data. It leverages Selenium for web automation, pdfplumber for PDF text extraction, and integrates with SharePoint using SharePlum.

## Features

- **Web Automation**: Automates the login and navigation processes on SharePoint.
- **PDF Extraction**: Utilizes pdfplumber to extract structured data from PDF invoices.
- **Data Processing**: Validates and formats extracted data before uploading.
- **SharePoint Integration**: Uploads processed data back to SharePoint with error handling and logging.
- **Logging**: Comprehensive logging for tracking application behavior and errors.

## Technical Details

### Technologies Used

- **Python 3.10+**: The primary programming language for the application.
- **Selenium**: For automating web browser interaction.
- **pdfplumber**: For extracting text and data from PDF files.
- **SharePlum**: For interacting with SharePoint's REST API.
- **Flask**: (Optional) For creating a web interface if needed in the future.
- **SQLite**: (Optional) For local data storage and caching.

### Architecture

- **Modular Design**: The application is structured into several modules for better maintainability:
  - **Config**: Contains configuration settings and constants.
  - **Drivers**: Manages WebDriver setup and browser interactions.
  - **Extractors**: Handles PDF extraction logic.
  - **Models**: Defines data models for structured data representation.
  - **Services**: Contains business logic for SharePoint interactions.
  - **Utils**: Provides utility functions for file handling and logging.

### Directory Structure

```
yourproject/
│
├── config/                  # Configuration files
│   ├── __init__.py
│   ├── iframe_config.py
│   ├── logger_config.py
│   └── re_pattern_config.py
│
├── drivers/                 # WebDriver setup
│   ├── __init__.py
│   └── webdriver.py
│
├── extractor.py             # PDF extraction logic
│
├── models/                  # Data models
│   ├── __init__.py
│   └── custom_elements.py
│
├── services/                # Service layer for SharePoint interactions
│   ├── __init__.py
│   ├── authentication.py
│   ├── sharepoint.py
│   └── ...
│
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── file_utils.py
│   ├── pdf_utils.py
│   └── webdriver_utils.py
│
├── logs/                    # Log files
│
├── temp/                    # Temporary files
│
├── .env                     # Environment variables
├── .gitignore               # Git ignore file
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

### Environment Variables

Set up environment variables in a `.env` file for sensitive information:
```
BW_USR=your_username
BW_PSW=your_password
BW_URL=your_login_url
OFFICE_SITE=your_office_site
OFFICE_USN=your_office_username
OFFICE_PSW=your_office_password
SHAREPOINT_SITE=your_sharepoint_site
TEMP_DIRECTORY=temp
LOG_DIRECTORY=logs
LOG_FILENAME=application.log
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```bash
python main.py
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Selenium](https://www.selenium.dev/) for web automation.
- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF text extraction.
- [SharePlum](https://github.com/jasonrbriggs/shareplum) for SharePoint integration.
