import datetime
import anthropic
import os
import re
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


def read_kanban_file(filename):
    # Get the path to the parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Construct the full path to kanban.md
    kanban_path = os.path.join(parent_dir, filename)
    with open(kanban_path, 'r') as file:
        return file.read()


def call_claude(kanban_content):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""
    Based on the following Kanban board content and context, create a detailed day plan for tomorrow:

    Kanban Board Content:
    {kanban_content}

    Context. You MUST follow these instructions:
    - This schedule is generated every night at 10:00pm for the following day. 
    - Tasks should be timeboxed - focus on allocated time blocks rather than completion goals (e.g., "2hr block for leetcode practice")
    - Include at least one social interaction block daily (e.g., quality conversation, coffee with friend)
    - After 2 hours of focused work, take a 30 minute break
    - I sleep from 12am-8:30am. I need about 30 minutes to get ready in the morning. 
    - 11pm-12am is for my wind down time.
    - Every Sunday from 1-4pm: Playspace
    - Tasks are prioritized as high, medium, and low. Prioritize high priority tasks first, then medium, then low.
    - There is a daily column for tasks that need to be done every day.

    Please create a schedule that takes into account these fixed commitments and prioritizes tasks accordingly. Format the output EXACTLY as follows. Do not fill in the thought dump or things I'm grateful for sections, only the tasks:

    # Day Planner
    - [ ] [TimeStart-TimeEnd] [Task]
    ...

    # Thought Dump

    # Things I'm Grateful For...

    # Scary thing(s) I did today...

    Ensure tasks are appropriately timed and include breaks. Add any necessary additional tasks or breaks to create a balanced day.
    Do not include a date or day of the week in the output.
    """

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0.7,
        system="You are a helpful assistant that creates detailed daily schedules based on Kanban board content and user context.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content


def preprocess_schedule(schedule, date):
    if isinstance(schedule, list) and len(schedule) > 0:
        schedule = schedule[0]

    if hasattr(schedule, 'text'):
        schedule = schedule.text

    schedule = str(schedule)
    schedule = re.sub(r'TextBlock\(text="(.*?)"\)', r'\1', schedule, flags=re.DOTALL)
    schedule = schedule.encode().decode('unicode_escape')

    # Remove everything before "# Day Planner"
    schedule = re.sub(r'^.*?# Day Planner', '# Day Planner', schedule, flags=re.DOTALL)

    # Remove any date or day of week that Claude might have included
    schedule = re.sub(r'^# Schedule for .*?\n', '', schedule, flags=re.MULTILINE)

    # Ensure the "Things I'm Grateful For" section is present and has numbered items
    # Ensure sections are empty
    schedule = re.sub(r'(# Thought Dump\s*)(1\..*?)(#|$)', r'\1\n\3', schedule, flags=re.DOTALL)
    schedule = re.sub(r'(# Things I\'m Grateful For\.\.\.\s*)(1\..*?)(#|$)', r'\1\n\3', schedule, flags=re.DOTALL)
    schedule = re.sub(r'(# Scary thing\(s\) I did today\.\.\.\s*)(1\..*?)($)', r'\1\n', schedule, flags=re.DOTALL)

    return schedule.strip()


def create_daily_file(date, schedule):
    filename = date.strftime("%Y-%m-%d.md")
    with open(filename, 'w') as file:
        file.write(schedule)
    print(f"Created schedule file: {filename}")


def generate_markdown():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    markdown_content = f"""# {tomorrow.strftime('%A, %B %d, %Y')}

# Schedule

# Scary things I did today

# Notes

"""
    return markdown_content


def main():
    try:
        kanban_content = read_kanban_file('../kanban.md')
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        claude_schedule = call_claude(kanban_content)
        processed_schedule = preprocess_schedule(claude_schedule, tomorrow)
        create_daily_file(tomorrow, processed_schedule)
        print("Schedule created successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Uncomment the following lines for more detailed error information:
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()