import datetime
import anthropic
import os
import re
from dotenv import load_dotenv
from datetime import timedelta
from gcal_service import GoogleCalendarService
from logger_config import setup_logger
import requests
import google.auth.exceptions
import time
import sys

load_dotenv()

logger = setup_logger()


def read_kanban_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    obsidian_dir = os.path.dirname(script_dir)
    kanban_path = os.path.join(obsidian_dir, filename)
    print(f"🔍 Looking for kanban file at: {kanban_path}")
    with open(kanban_path, 'r') as file:
        return file.read()


def call_claude(kanban_content):
    # Add retry logic for network operations
    max_retries = 3
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            print("🤖 Delegating all life decisions to Claude...")

            calendar_service = GoogleCalendarService()
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            
            # Get events specifically for tomorrow's full day
            tomorrow_start = datetime.datetime.combine(tomorrow, datetime.time.min)
            tomorrow_end = datetime.datetime.combine(tomorrow, datetime.time.max)
            calendar_events = calendar_service.get_events(tomorrow_start, tomorrow_end)
            
            prompt = f"""
            Based on the following Kanban board content, calendar events, and context, create a detailed day plan for {tomorrow.strftime('%Y-%m-%d')}:

            Kanban Board Content:
            {kanban_content}

            Calendar Events for {tomorrow.strftime('%Y-%m-%d')}:
            {calendar_events}

            Context. You MUST follow these instructions:
            - This schedule is generated every night at 10:00pm for the following day. 
            - Structure the day around 4 two-hour focus blocks, working around calendar events
            - After each 2-hour focus block, take a 30-minute break
            - Include at least one meaningful social interaction daily (e.g., coffee with a friend, quality conversation)
            - I sleep from 12am-8:30am. I need about 30 minutes to get ready in the morning. 
            - 11pm-12am is for my wind down time.
            - Tasks are prioritized as high and low. Prioritize high priority tasks first, then medium.
            - IMPORTANT: For each focus block, choose a SPECIFIC task from the Kanban board. Do not use generic descriptions like "work on medium priority tasks". Instead, use the exact task name from the board.
            - There is also another column for high context switching admin tasks, that all take <10 minutes each, so allocate a block of time for these.
            - There is a daily column for tasks that need to be done every day.

            Please create a schedule that takes into account these fixed commitments and prioritizes tasks accordingly. 
            Format the output EXACTLY as follows. Mark focus blocks with ###:

            # Day Planner
            - [ ] [TimeStart-TimeEnd] Regular task
            - [ ] [TimeStart-TimeEnd] ### Focus Block: [Description]

            # Thought Dump

            # Things I'm Grateful For...

            # Scary thing(s) I did today...

            Ensure tasks are appropriately timed and include breaks. Add any necessary additional tasks or breaks to create a balanced day.
            Do not include a date or day of the week in the output.
            IMPORTANT: Leave the Thought Dump, Things I'm Grateful For, and Scary Things sections completely empty - do not add any content to these sections.
            """

            message = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.01,
                system="You are a helpful assistant that creates detailed daily schedules based on Kanban board content and user context.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content
            
        except (requests.exceptions.ConnectionError, google.auth.exceptions.TransportError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Network error occurred (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                raise


def preprocess_schedule(schedule, date):
    if isinstance(schedule, list) and len(schedule) > 0:
        schedule = schedule[0]

    if hasattr(schedule, 'text'):
        schedule = schedule.text

    schedule = str(schedule)
    schedule = re.sub(r'TextBlock\(text="(.*?)"\)', r'\1', schedule, flags=re.DOTALL)
    schedule = schedule.encode().decode('unicode_escape')
    
    print("\n🔍 DEBUG: Schedule content before processing:")
    print(schedule)
    print("\n🔍 DEBUG: Looking for pattern:")
    print(r'\[ \] \[(\d{2}:\d{2})-(\d{2}:\d{2})\] ### Focus Block: (.*?)(?=\n|$)')
    
    # Remove claude's preamble yap
    schedule = re.sub(r'^.*?# Day Planner', '# Day Planner', schedule, flags=re.DOTALL)
    schedule = re.sub(r'^# Schedule for .*?\n', '', schedule, flags=re.MULTILINE)

    # Ensure journal prompt sections are empty
    schedule = re.sub(r'(# Thought Dump\s*)(1\..*?)(#|$)', r'\1\n\3', schedule, flags=re.DOTALL)
    schedule = re.sub(r'(# Things I\'m Grateful For\.\.\.\s*)(1\..*?)(#|$)', r'\1\n\3', schedule, flags=re.DOTALL)
    schedule = re.sub(r'(# Scary thing\(s\) I did today\.\.\.\s*)(1\..*?)($)', r'\1\n', schedule, flags=re.DOTALL)

    focus_blocks = re.findall(r'\[ \] \[(\d{1,2}:\d{2}(?:am|pm)?)-(\d{1,2}:\d{2}(?:am|pm)?)\] ### Focus Block: (.*?)(?=\n|$)', schedule)
    
    if focus_blocks:
        print(f"\n📅 Found {len(focus_blocks)} focus blocks to add to calendar")
        print("Focus blocks found:", focus_blocks)
        
        # Write focus blocks to GCal
        calendar_service = GoogleCalendarService()
        for start_time, end_time, description in focus_blocks:
            # Convert times from AM/PM format to datetime
            start_dt = datetime.datetime.combine(
                date,
                datetime.datetime.strptime(start_time.strip().upper(), '%I:%M%p').time()
            )
            end_dt = datetime.datetime.combine(
                date,
                datetime.datetime.strptime(end_time.strip().upper(), '%I:%M%p').time()
            )
            
            print(f"Creating calendar event: {start_dt} - {end_dt}: {description}")
            calendar_service.create_event(
                summary=description,
                start_time=start_dt,
                end_time=end_dt,
                description="Deep work session generated by Day Planner"
            )
    else:
        print("❌ No focus blocks found in schedule")
    
    return schedule.strip()


def write_schedule_to_file(schedule, date):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    journal_dir = os.path.join(os.path.dirname(current_dir), 'journal')
    
    os.makedirs(journal_dir, exist_ok=True)
    
    file_path = os.path.join(journal_dir, f"{date.strftime('%Y-%m-%d')}.md")
    
    with open(file_path, 'w') as file:
        file.write(schedule)
    print(f"📝 Schedule written to {file_path}")


def generate_markdown():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    markdown_content = f"""# {tomorrow.strftime('%A, %B %d, %Y')}

# Schedule

# Scary/Hard things I Challenged Myself To Do Today

# Notes

"""
    return markdown_content


def should_run():
    # Check for a "pause file" in the same directory as the script
    pause_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.dayplanner_pause')
    return not os.path.exists(pause_file)


def main():
    try:
        logger.info("Starting day planner script...")
        
        if not should_run():
            logger.info("Day planner is paused. Skipping execution.")
            return
        
        # Add a small delay at startup to allow network to initialize
        time.sleep(30)  # Wait 30 seconds for network to be ready
            
        kanban_content = read_kanban_file('_kanban.md')
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        claude_schedule = call_claude(kanban_content)
        processed_schedule = preprocess_schedule(claude_schedule, tomorrow)
        write_schedule_to_file(processed_schedule, tomorrow)
        logger.info("✅ Schedule created successfully!")
        sys.exit(0)  
    except Exception as e:
        logger.error(f"❌ An error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 


if __name__ == "__main__":
    main()