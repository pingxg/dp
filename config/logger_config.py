import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import smtplib

# Load environment variables from .env file

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



class SSLSMTPHandler(logging.Handler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject, credentials):
        logging.Handler.__init__(self)
        self.mailhost = mailhost
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.credentials = credentials

    def emit(self, record):
        try:
            port = 465  # SSL port
            smtp = smtplib.SMTP_SSL(self.mailhost, port)
            smtp.login(self.credentials[0], self.credentials[1])

            msg = self.format(record)
            message = f"From: {self.fromaddr}\r\nTo: {','.join(self.toaddrs)}\r\nSubject: {self.subject}\r\n\r\n{msg}"
            
            smtp.sendmail(self.fromaddr, self.toaddrs, message)
            smtp.quit()
        except Exception as e:
            print(f"Error sending email: {e}")

def setup_logging():
    # Unpack settings from global configuration
    config = LOGGING_CONFIG
    log_path = os.path.join(config['log_directory'], config['log_filename'])
    
    # Ensure log directory exists
    if not os.path.exists(config['log_directory']):
        os.makedirs(config['log_directory'])

    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config['log_level'].upper()))

    # File handler
    fh = RotatingFileHandler(log_path, maxBytes=config['max_log_size'], backupCount=config['backup_count'])
    fh.setLevel(getattr(logging, config['log_level'].upper()))
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - [%(filename)s:%(lineno)d - %(funcName)s()] - %(message)s',
        '%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, config['log_notify_level'].upper()))  # Example: Only show ERROR and above in console
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Email handler (if enabled)
    if config['email_alerts']:
        email_cfg = config['email_config']
        if email_cfg['smtp_port'] == 465:
            eh = SSLSMTPHandler(
            mailhost=email_cfg['smtp_server'],
            fromaddr=email_cfg['from_email'],
            toaddrs=email_cfg['to_emails'],
            subject=email_cfg['subject'],
            credentials=(email_cfg['username'], email_cfg['password'])
            )
        else:
            eh = SMTPHandler(
                mailhost=(email_cfg['smtp_server'], email_cfg['smtp_port']),
                fromaddr=email_cfg['from_email'],
                toaddrs=email_cfg['to_emails'],
                subject=email_cfg['subject'],
                credentials=(email_cfg['username'], email_cfg['password']),
                secure=None
            )
        eh.setLevel(getattr(logging, config['log_notify_level'].upper()))  # Customize this as needed
        eh.setFormatter(formatter)
        logger.addHandler(eh)
