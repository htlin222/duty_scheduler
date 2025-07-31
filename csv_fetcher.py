import requests
import csv
from io import StringIO
from typing import List, Dict


class CSVFetcher:
    def __init__(self, csv_url: str):
        self.csv_url = csv_url

    def fetch_csv_data(self) -> List[Dict[str, str]]:
        """
        Fetch CSV data from the Google Sheets URL or local file
        Returns a list of dictionaries representing each row
        """
        try:
            # Check if it's a URL or a local file
            if self.csv_url.startswith(("http://", "https://")):
                # Handle Google Sheets redirects
                response = requests.get(self.csv_url, allow_redirects=True)
                response.raise_for_status()
                # Parse CSV content
                csv_content = response.text
                csv_reader = csv.reader(StringIO(csv_content))
            else:
                # Handle local file
                with open(self.csv_url, "r", encoding="utf-8") as file:
                    csv_reader = csv.reader(file)
                    rows = list(csv_reader)
                    return rows

            # Convert to list for easier processing (for URL case)
            rows = list(csv_reader)

            if not rows:
                raise ValueError("No data found in CSV")

            # Assume first row contains dates (1, 2, 3, ... 31)
            # And subsequent rows contain duty assignments (a, b, c, etc.)
            return rows

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch CSV data: {e}")
        except Exception as e:
            raise Exception(f"Error processing CSV data: {e}")
