# app/config.py
import os
from dotenv import load_dotenv
import logging

def load_env():
    load_dotenv()

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

logger = setup_logging()