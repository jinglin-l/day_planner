# Claude Day Planner

Are you utilizing your time in a way that's congruent with your value system & what you want to achieve? If not, a personzlized day planner can help you get there. 

## Philosophy & Motivation
I built this tool because I needed a better way to project-manage my life and address the ever-expanding backlog of things I intend to do, but somehow never get to. 

### Core Workflow
Throughout my day, I maintain a Kanban board in Obsidian to capture and prioritize tasks. It's simple easy to set up - just install a kanban board from the community plugins. I use [this one](https://github.com/mgmeyers/obsidian-kanban)

Each night at 10 PM, my planner:

- Analyzes my Kanban board to understand my task landscape
- Checks my Google Calendar for existing commitments
- Consults with Claude to create a schedule for the next day
- Automatically blocks out focused work sessions and writes them back to my Google Calendar


### Design Philosophy

- **Deep Work Focus** 🧠  
I structure my day around four 2-hour focus blocks. This maximizes my potential for concentrated effort - it's when I get my best work done.

- **Managing My Human Limitations** 🤖  
I unfortunately suffer from being human, which means to be productive, I actually need built-in breaks for fun, exercise, sleep, and seeing friends! My energy management is critical - I've learned the hard way what drains me (like low blood sugar or boring trapped conversations) and what energizes me (like good conversations with interesting people or building something cool).

- **Minimizing Decision Making** 🧩  
I realized my decision-making in the moment tends to be very poor (gahhh depleted willpower, emotional state, or immediate pressures). By automating my schedule creation, I'm preserving my mental energy for actual work instead of deciding "what should I do next?"

- **Building Sustainable Systems** 🔄  
Systems help me create a foundation for building good habits by removing reliance on willpower or motivation. When the right action becomes the default action, I no longer need to convince myself to do it each time. It's about making the good choices the easy choices.

### Prerequisites

1. Python 3.x installed on your system
2. Google Calendar access and API credentials
3. Anthropic API key for Claude
4. Obsidian with the Kanban plugin installed

### Installation Steps

// todo! 



### Setting up Automated Scheduling

This tool uses macOS Launch Agents to run a cron job automatically every night at 10 PM. The Launch Agent configuration:

- Ensures the script only runs when network is available, and automatically retries on failure
- Logs output to `dayplanner/dayplanner_logs/`

To set up automated scheduling:

1. Create a Launch Agent plist file at `~/Library/LaunchAgents/com.dayplanner.plist`
2. Copy the following configuration (update paths for your system):

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dayplanner.schedule</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/your/venv/bin/python3</string>
        <string>/path/to/your/day_planner/dayplanner.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>/Users/yourusername</string>
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/your/day_planner</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>22</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/Library/Logs/dayplanner.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/Library/Logs/dayplanner.error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>NetworkState</key>
        <true/>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>300</integer>
</dict>
</plist>
```

To load the Launch Agent:

```
launchctl load ~/Library/LaunchAgents/com.dayplanner.plist
```

To temporarily pause the script, create a file at `.dayplanner_pause` in the same directory as the script. When this file exists, the script will not run.

```
touch .dayplanner_pause
```

To resume the script, delete the file:

```
rm .dayplanner_pause
```


