import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import smtplib
from config import LOGGING_CONFIG  # Import global settings


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
