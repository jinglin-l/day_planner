import logging
import os
from datetime import datetime

def setup_logger():
    log_dir = 'dayplanner_logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('dayplanner')
    logger.setLevel(logging.INFO)

    log_filename = os.path.join(log_dir, f'dayplanner_{datetime.now().strftime("%Y%m%d")}.log')
    
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 