from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
from typing import List, Tuple
import os


class ICSGenerator:
    def __init__(
        self,
        weekday_start: str,
        weekday_end: str,
        weekend_start: str,
        weekend_end: str,
        output_dir: str,
        calendar_config: dict,
        duty_types: dict,
        filename_pattern: str,
    ):
        self.weekday_start = weekday_start  # "17:00"
        self.weekday_end = weekday_end  # "08:00" (next day)
        self.weekend_start = weekend_start  # "08:00"
        self.weekend_end = weekend_end  # "08:00" (next day)
        self.output_dir = output_dir
        self.calendar_config = calendar_config
        self.duty_types = duty_types
        self.filename_pattern = filename_pattern

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def create_duty_event(
        self, duty_date: date, is_weekend: bool, person: str, location: str
    ) -> Event:
        """
        Create a single duty event for the calendar

        Args:
            duty_date: The date of the duty
            is_weekend: Whether this is a weekend duty
            person: The person assigned to this duty (letter)
            location: The location/ward for this duty

        Returns:
            An iCalendar Event object
        """
        event = Event()

        # Determine start and end times based on weekend/weekday
        if is_weekend:
            start_hour, start_min = map(int, self.weekend_start.split(":"))
            end_hour, end_min = map(int, self.weekend_end.split(":"))
            duty_type_key = "weekend"
        else:
            start_hour, start_min = map(int, self.weekday_start.split(":"))
            end_hour, end_min = map(int, self.weekday_end.split(":"))
            duty_type_key = "weekday"

        # Get localized duty type
        duty_type = self.duty_types.get(duty_type_key, duty_type_key)

        # Create start datetime
        start_dt = datetime.combine(duty_date, datetime.min.time())
        start_dt = start_dt.replace(hour=start_hour, minute=start_min)

        # Create end datetime (next day)
        end_dt = datetime.combine(duty_date + timedelta(days=1), datetime.min.time())
        end_dt = end_dt.replace(hour=end_hour, minute=end_min)

        # Format template variables
        template_vars = {
            "person": person.upper(),
            "location": location,
            "duty_type": duty_type,
            "date": duty_date.strftime("%Y-%m-%d"),
            "start_time": start_dt.strftime("%H:%M"),
            "end_time": end_dt.strftime("%H:%M"),
        }

        # Set event properties using templates
        event_title = self.calendar_config["event_title_template"].format(
            **template_vars
        )
        event_description = self.calendar_config["event_description_template"].format(
            **template_vars
        )
        alarm_message = self.calendar_config["alarm_message_template"].format(
            **template_vars
        )

        event.add("summary", event_title)
        event.add("dtstart", start_dt)
        event.add("dtend", end_dt)
        event.add("description", event_description)

        # Add alarm reminder using VALARM subcomponent
        from icalendar import Alarm

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", alarm_message)
        alarm.add("trigger", timedelta(minutes=-30))
        event.add_component(alarm)

        return event

    def generate_ics_file(
        self, person: str, duty_dates: List[Tuple[date, bool, str]]
    ) -> str:
        """
        Generate an ICS file for a specific person's duty schedule

        Args:
            person: The person's identifier (letter)
            duty_dates: List of tuples (date, is_weekend, location)

        Returns:
            Path to the generated ICS file
        """
        # Determine primary location for this person (use the most common location)
        if duty_dates:
            location_counts = {}
            for _, _, location in duty_dates:
                location_counts[location] = location_counts.get(location, 0) + 1
            primary_location = max(location_counts, key=location_counts.get)
        else:
            primary_location = "一般病房"

        # Create calendar
        cal = Calendar()
        cal.add("prodid", "-//Duty Schedule Generator//duty.ics//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")

        # Use template for calendar name
        calendar_title = self.calendar_config["title_template"].format(
            person=person.upper(), location=primary_location
        )
        cal.add("x-wr-calname", calendar_title)
        cal.add("x-wr-timezone", "Asia/Taipei")

        # Add all duty events
        for duty_date, is_weekend, location in duty_dates:
            event = self.create_duty_event(duty_date, is_weekend, person, location)
            cal.add_component(event)

        # Generate filename using pattern
        filename = self.filename_pattern.format(
            char=person, location=primary_location.replace(" ", "")
        )
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(cal.to_ical())

        return filepath
