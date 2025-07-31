#!/usr/bin/env python3
import yaml
import sys
from csv_fetcher import CSVFetcher
from duty_parser import DutyParser
from ics_generator import ICSGenerator


def load_config(config_path: str = "config.yml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file: {e}")
        sys.exit(1)


def main():
    print("=== Duty Schedule ICS Generator ===")
    print()

    # Load configuration
    config = load_config()

    # Extract configuration values
    year = config["schedule"]["year"]
    month = config["schedule"]["month"]
    csv_url = config["schedule"]["csv_url"]

    weekday_start = config["duty_times"]["weekday"]["start_time"]
    weekday_end = config["duty_times"]["weekday"]["end_time"]
    weekend_start = config["duty_times"]["weekend"]["start_time"]
    weekend_end = config["duty_times"]["weekend"]["end_time"]

    output_dir = config["output"]["directory"]
    filename_pattern = config["output"]["filename_pattern"]

    # Extract new configuration sections
    calendar_config = config["calendar"]
    locations_config = config["locations"]
    duty_types = config["duty_types"]
    csv_format = config.get("csv_format", {"orientation": "columns"})

    print(f"Generating duty schedules for {year}-{month:02d}")
    print(f"CSV URL: {csv_url}")
    print()

    # Step 1: Fetch CSV data
    print("Step 1: Fetching CSV data...")
    fetcher = CSVFetcher(csv_url)
    try:
        csv_data = fetcher.fetch_csv_data()
        print(f"✓ Successfully fetched CSV data ({len(csv_data)} rows)")

        # Debug: Show first few rows of raw CSV data
        print("\nRaw CSV data preview (first 5 rows):")
        for i, row in enumerate(csv_data[:5]):
            print(f"  Row {i}: {row}")

        # Show total structure
        print(
            f"\nCSV structure: {len(csv_data)} rows, max {max(len(row) for row in csv_data if row)} columns"
        )

    except Exception as e:
        print(f"✗ Error fetching CSV: {e}")
        sys.exit(1)

    # Step 2: Parse duty schedule
    print(
        f"\nStep 2: Parsing duty schedule (orientation: {csv_format['orientation']})..."
    )
    parser = DutyParser(year, month, locations_config, csv_format)
    try:
        duty_schedule = parser.parse_duty_schedule(csv_data)
        print(f"✓ Found duty assignments for {len(duty_schedule)} people:")
        for person, assignments in sorted(duty_schedule.items()):
            locations = list(set(assignment.location for assignment in assignments))
            print(
                f"  - Person {person.upper()}: {len(assignments)} duty days at {', '.join(locations)}"
            )
    except Exception as e:
        print(f"✗ Error parsing duty schedule: {e}")
        sys.exit(1)

    # Step 3: Generate ICS files
    print(f"\nStep 3: Generating ICS files in '{output_dir}' directory...")
    generator = ICSGenerator(
        weekday_start=weekday_start,
        weekday_end=weekday_end,
        weekend_start=weekend_start,
        weekend_end=weekend_end,
        output_dir=output_dir,
        calendar_config=calendar_config,
        duty_types=duty_types,
        filename_pattern=filename_pattern,
    )

    generated_files = []
    for person, duty_assignments in duty_schedule.items():
        # Get duty dates with weekend/weekday and location info
        duty_dates = parser.get_duty_dates_with_types(duty_assignments)

        if not duty_dates:
            print(f"  ⚠ No valid duty dates for person {person.upper()}, skipping...")
            continue

        # Group duty dates by location for separate files
        duties_by_location = {}
        for duty_date, is_weekend, location in duty_dates:
            if location not in duties_by_location:
                duties_by_location[location] = []
            duties_by_location[location].append((duty_date, is_weekend, location))

        # Generate one file per location for this person
        for location, location_duties in duties_by_location.items():
            try:
                filepath = generator.generate_ics_file(person, location_duties)
                generated_files.append(filepath)
                print(f"  ✓ Generated: {filepath}")

                # Show duty summary for this location
                weekday_count = sum(
                    1 for _, is_weekend, _ in location_duties if not is_weekend
                )
                weekend_count = sum(
                    1 for _, is_weekend, _ in location_duties if is_weekend
                )
                print(
                    f"    → {len(location_duties)} duties at {location} ({weekday_count} weekday, {weekend_count} weekend)"
                )

            except Exception as e:
                print(
                    f"  ✗ Error generating ICS for person {person.upper()} at {location}: {e}"
                )

    # Summary
    print("\n" + "=" * 50)
    print(f"✓ Complete! Generated {len(generated_files)} ICS files.")
    print("\nTo import these calendars:")
    print("1. Open your calendar application")
    print("2. Import the ICS file for your assigned letter")
    print("3. The duty events will appear in your calendar with reminders")
    print("\nFiles are located in:", output_dir)


if __name__ == "__main__":
    main()
