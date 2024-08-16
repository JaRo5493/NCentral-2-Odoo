# logger.py
import logging
from pathlib import Path


def setup_logger():
    base_path = Path(__file__).parent
    file_path = (base_path / "../helpdesk.log").resolve()
    logging.basicConfig(filename=file_path, filemode='a',
                        format='[%(levelname)s] %(asctime)s - %(message)s',
                        datefmt='%d.%m.%y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    return logger
