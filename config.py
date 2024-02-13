from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Helper function to convert "True"/"False" strings to booleans
def str_to_bool(s):
    return s.lower() in ['true', '1', 't', 'y', 'yes']

# Convert comma-separated emails to a list (if necessary)
def to_email_list(s):
    return [email.strip() for email in s.split(',')]

# Define global logging configuration using environment variables
LOGGING_CONFIG = {
    'log_directory': os.getenv('LOG_DIRECTORY', 'logs'),
    'log_filename': os.getenv('LOG_FILENAME', 'application.log'),
    'max_log_size': int(os.getenv('MAX_LOG_SIZE', 10485760)),
    'backup_count': int(os.getenv('BACKUP_COUNT', 5)),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_notify_level': os.getenv('LOG_NOTIFY_LEVEL', 'ERROR'),
    'email_alerts': str_to_bool(os.getenv('EMAIL_ALERTS', 'False')),
    'email_config': {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.example.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'from_email': os.getenv('FROM_EMAIL', 'your-email@example.com'),
        'to_emails': to_email_list(os.getenv('TO_EMAILS', 'recipient@example.com')),
        'subject': os.getenv('EMAIL_SUBJECT', 'Critical Error Logged'),
        'username': os.getenv('SMTP_USERNAME', 'your-smtp-username'),
        'password': os.getenv('SMTP_PASSWORD', 'your-smtp-password')
    }
}


def get_expressions():
    return expressions
expressions = {
    "1381774": [
        "S-Business Oy",
        r"alv % alv yht. alv 0 % yht. sis. alv ([-0-9. ​]+) yhteensä alv 0%",
        None
    ],
    "1367729": [
        "METOS OY AB",
        r"veroton loppusumma ([-0-9., ​]+) arvonlisävero 24,00 % ([-0-9., ]+) yhteensä eur ([-0-9., ]+) metos oy ab",
        None
    ],
    "1578999": [
        "Oy Golden Crop AB",
        r"tax base amount vat ([- 0-9vat.%, €​]+)",
        "manager"
    ],
    "1394052": [
        "HÄTÄLÄ OY F56451", r"veroton summa ([-0-9a-z.%, €​]+) lasku yhteensä",
        "manager"
    ],
    "1426362": [
        "Kalaneuvos Oy", r"_____________ ([-0-9a-z.%, €​]+) _____________",
        "manager"
    ],
    "1389643": [
        "FINNISH FRESHFISH OY",
        r"veroton summa ([-0-9a-z.%, €​]+) lasku yhteensä", "manager"
    ],
    "1276917": [
        "KANTA-HÄMEEN TUORETUOTE OY",
        r"alv-erittely: netto: ([alvnetto:0-9, %-]+)", "manager"
    ],
    "1375629": [
        "Tukkutalo Heinonen Oy", r"alv-erittely: netto: ([alvnetto:0-9, %-]+)",
        "manager"
    ],
    "2000088": [
        "Hallin Deli Oy",
        r"yhteensäilman arvonlisäveroa ([0-9, -]+ [arvonlisävero 0-9 %,-]+)",
        "manager"
    ],
    "1714901": [
        "AGRICA AB",
        r"arvonlisäveroerittely: alv % netto vero brutto specifikation av mervärdesskatt: mvs % skatt ([0-9. -]+)",
        "manager"
    ],
    "2000009": ["Fisu Pojat Oy", r"14% ([-0-9 ,]+)", "manager"],
    "1566645": [
        "Yellow Service Oy Grönroos",
        r"verokanta veroton vero yhteensä ([-0-9 ,]+)", "manager"
    ],
    "1433275": [
        "Kesko Oyj",
        r"alv erittely veron peruste alv % vero verollinen ([-0-9 ,]+)",
        "manager"
    ],
    "1553180":
    ["Oy Hartwall Ab", r"alv-erittely verokanta([-0-9 ,%]+)", "manager"],
    "2000211":
    ["Kungfu Pot Oy", r"yhteensäilman ([-0-9 ,%arvonlisävero]+)", "manager"],
    "2000224": [
        "FinBlu Safety Oy", r"yhteensäilman ([-0-9 ,%arvonlisävero]+)",
        "manager"
    ],
    "1357805": [
        "SPARTAO OY",
        r"veroprosentti veron peruste veron määrä([-0-9,. eur%]+)", "manager"
    ],
    "2000219": [
        "Firewok Finland Oy",
        r"veroprosentti veron peruste veron määrä([-0-9,. eur%]+)", "manager"
    ],
}