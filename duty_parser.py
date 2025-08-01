from typing import List, Dict, Tuple, NamedTuple
from datetime import date


class DutyAssignment(NamedTuple):
    """Represents a duty assignment with location context"""

    day: int
    location: str
    row_index: int


class DutyParser:
    def __init__(self, year: int, month: int, location_config: dict, csv_format: dict):
        self.year = year
        self.month = month
        self.location_config = location_config
        self.csv_format = csv_format

    def parse_duty_schedule(
        self, csv_rows: List[List[str]]
    ) -> Dict[str, List[DutyAssignment]]:
        """
        Parse CSV data where each row represents duty assignments by position
        Format: Each cell position corresponds to a day (column 0 = day 1, column 1 = day 2, etc.)
        If a cell contains a letter, that person is on duty for that day

        Args:
            csv_rows: List of rows from CSV, where each row contains duty assignments by day position

        Returns:
            Dictionary like {'a': [DutyAssignment(day=1, location='北邊病房', row_index=0), ...], ...}
        """
        if not csv_rows:
            raise ValueError("CSV data is empty")

        if not csv_rows:
            raise ValueError("No valid data found in CSV")

        # Dictionary to store duty assignments for each person
        duty_schedule = {}

        # Check orientation from config
        orientation = self.csv_format.get("orientation", "columns")

        if orientation == "rows":
            # Row-based: Each row represents a day (don't filter out empty rows for day calculation)
            for row_idx, row in enumerate(csv_rows):
                # Day number is row index + 1 (0-based to 1-based)
                day = row_idx + 1

                # Validate day is within reasonable range for the month
                if not (1 <= day <= 31):
                    continue

                # Check each cell in the row (each column represents a location)
                for col_idx, cell in enumerate(row):
                    # Clean and validate cell content
                    cell_clean = cell.strip() if cell else ""

                    # Skip empty cells or cells with no alphabetic characters
                    if not cell_clean or not any(c.isalpha() for c in cell_clean):
                        continue

                    # Get location for this column (Column A = 0, Column B = 1, etc.)
                    location = self.location_config.get("by_column", {}).get(
                        col_idx, self.location_config.get("default", "一般病房")
                    )

                    # Parse multiple people in the same cell (e.g., "a/b", "a,b", "a b")
                    people = self._parse_multiple_people(cell_clean)

                    # Create duty assignment for each person
                    for person in people:
                        assignment = DutyAssignment(
                            day=day, location=location, row_index=row_idx
                        )

                        # Add this assignment to the person's duty list
                        if person not in duty_schedule:
                            duty_schedule[person] = []
                        duty_schedule[person].append(assignment)

        else:
            # Column-based: Each column represents a day (original logic)
            # Filter out completely empty rows for column-based processing
            non_empty_rows = [
                row for row in csv_rows if any(cell.strip() for cell in row if cell)
            ]

            if len(non_empty_rows) < 1:
                raise ValueError("No valid data found in CSV")

            for row_idx, row in enumerate(non_empty_rows):
                # Check each cell in the row
                for col_idx, cell in enumerate(row):
                    # Clean and validate cell content
                    cell_clean = cell.strip() if cell else ""

                    # Skip empty cells or cells with no alphabetic characters
                    if not cell_clean or not any(c.isalpha() for c in cell_clean):
                        continue

                    # Day number is column index + 1 (0-based to 1-based)
                    day = col_idx + 1

                    # Validate day is within reasonable range for the month
                    if not (1 <= day <= 31):
                        continue

                    # Get location for this column (Column A = 0, Column B = 1, etc.)
                    location = self.location_config.get("by_column", {}).get(
                        col_idx, self.location_config.get("default", "一般病房")
                    )

                    # Parse multiple people in the same cell (e.g., "a/b", "a,b", "a b")
                    people = self._parse_multiple_people(cell_clean)

                    # Create duty assignment for each person
                    for person in people:
                        assignment = DutyAssignment(
                            day=day, location=location, row_index=row_idx
                        )

                        # Add this assignment to the person's duty list
                        if person not in duty_schedule:
                            duty_schedule[person] = []
                        duty_schedule[person].append(assignment)

        return duty_schedule

    def _parse_multiple_people(self, cell_content: str) -> List[str]:
        """
        Parse a cell that may contain multiple people separated by various delimiters.

        Args:
            cell_content: Raw cell content (e.g., "a/b", "a,b", "a b", "a")

        Returns:
            List of normalized person identifiers (lowercase single letters)
        """
        import re

        # Common separators: /, ,, space, &, +, -
        separators = r"[/,\s&+\-]+"

        # Split by separators and clean each part
        parts = re.split(separators, cell_content.strip())

        people = []
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract first alphabetic character and normalize to lowercase
            for char in part:
                if char.isalpha():
                    people.append(char.lower())
                    break  # Only take the first alphabetic char from each part

        # Remove duplicates while preserving order
        seen = set()
        unique_people = []
        for person in people:
            if person not in seen:
                seen.add(person)
                unique_people.append(person)

        return unique_people

    def is_weekend(self, day: int) -> bool:
        """
        Check if a given day is a weekend (Saturday or Sunday)

        Args:
            day: Day of the month

        Returns:
            True if weekend, False if weekday
        """
        try:
            date_obj = date(self.year, self.month, day)
            # Monday is 0, Sunday is 6
            return date_obj.weekday() in [5, 6]  # Saturday or Sunday
        except ValueError:
            return False

    def get_duty_dates_with_types(
        self, duty_assignments: List[DutyAssignment]
    ) -> List[Tuple[date, bool, str]]:
        """
        Convert duty assignments to date objects with weekend/weekday and location info

        Args:
            duty_assignments: List of DutyAssignment objects

        Returns:
            List of tuples (date_object, is_weekend, location)
        """
        duty_dates = []

        for assignment in duty_assignments:
            try:
                date_obj = date(self.year, self.month, assignment.day)
                is_weekend_duty = self.is_weekend(assignment.day)
                duty_dates.append((date_obj, is_weekend_duty, assignment.location))
            except ValueError:
                # Skip invalid dates
                continue

        return duty_dates
