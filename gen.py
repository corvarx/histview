import yaml
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from collections import defaultdict

# ----------------------------
# Configuration via Lambda Functions
# ----------------------------

# 1. Search Criteria: A list of lambda functions that take an event and return True if it should be included.
search_criteria = [
    lambda event: event.get('x', 0) < 100,   # Example: x < 100
    lambda event: event.get('y', 0) > 20     # Example: y > 20
]

# To display all events without filtering, set search_criteria to an empty list
search_criteria = [
]

# 2. Display Columns: A list of tuples containing the column name, a lambda function for condition, and the width percentage.

display_columns = [
    ('China', lambda event: event.get('country') == 'China', 25),
    ('US', lambda event: event.get('country') == 'US', 25),
]
# ----------------------------
# Helper Functions
# ----------------------------

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def filter_events(events, criteria):
    if not criteria:
        return events  # No filtering
    filtered = []
    for event in events:
        if all(criterion(event) for criterion in criteria):
            filtered.append(event)
    return filtered

def organize_events_by_date_and_column(events, columns):
    # Extract unique sorted dates
    unique_dates = sorted(
        {event['date'] for event in events},
        key=lambda date: datetime.strptime(date, "%Y-%m-%d")
    )

    # Initialize a dictionary to hold events per date and per column
    events_by_date = {date: {col[0]: [] for col in columns} for date in unique_dates}

    # Assign events to their respective date and column
    for event in events:
        date = event['date']
        for col_name, condition, _ in columns:
            if condition(event):
                events_by_date[date][col_name].append(event)
                break  # Place event in the first matching column

    return unique_dates, events_by_date

def sort_events_within_columns(events_by_date):
    for date in events_by_date:
        for col in events_by_date[date]:
            events_by_date[date][col].sort(key=lambda x: x.get('name', ''))
    return events_by_date

# ----------------------------
# Main Function
# ----------------------------

def main():
    # Load event data
    try:
        events = load_yaml('events.yaml')
    except FileNotFoundError:
        print("Error: 'events.yaml' not found. Please ensure the file exists in the current directory.")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing 'events.yaml': {e}")
        return

    # Apply search criteria
    filtered_events = filter_events(events, search_criteria)
    print(f"Total events after filtering: {len(filtered_events)}")

    # Organize events by date and column
    unique_dates, events_by_date = organize_events_by_date_and_column(filtered_events, display_columns)

    # Sort events within columns
    events_by_date = sort_events_within_columns(events_by_date)

    # Prepare column widths for template rendering
    column_widths = {col[0]: col[2] for col in display_columns}

    # Generate HTML using Jinja2
    env = Environment(loader=FileSystemLoader('.'))
    try:
        template = env.get_template('template.html')
    except Exception as e:
        print(f"Error loading 'template.html': {e}")
        return

    html_output = template.render(
        timeline_dates=unique_dates,
        events_by_date=events_by_date,
        display_columns=display_columns,
        column_widths=column_widths
    )

    # Write to output.html
    with open('output.html', 'w') as f:
        f.write(html_output)

    print("HTML page generated successfully as 'output.html'.")

if __name__ == "__main__":
    main()
