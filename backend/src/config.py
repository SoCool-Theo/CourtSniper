import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL")
BOOKING_MESSAGE = os.getenv("BOOKING_MESSAGE")

TARGET_HOUR = int(os.getenv("TARGET_HOUR", 8))
TARGET_MINUTE = int(os.getenv("TARGET_MINUTE", 0))
TARGET_SECOND = int(os.getenv("TARGET_SECOND", 0))