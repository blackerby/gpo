import os
from datetime import date, timedelta

PAGE_SIZE = 1000
YESTERDAY = date.today() - timedelta(days=1)
TOMORROW = date.today() + timedelta(days=1)
CURRENT_CONGRESS = (date.today().year - 1789) // 2 + 1
COLLECTIONS = {
    "Bills": "bills",
    "Public Laws": "plaw",
    "Committee Reports": "crpt",
    "Committee Prints": "cprt",
    "Congressional Hearings": "chrg",
}
API_KEY = os.environ.get("GPO_API_KEY", "DEMO_KEY")
TITLE = "New/Updated Data from GPO"
