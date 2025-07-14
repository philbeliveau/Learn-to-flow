#!/usr/bin/env python3
"""
EZBI Analytics - Jira User Stories Import Script
Pushes comprehensive user stories to Jira project
"""

import json
import os
from jira import JIRA
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Jira configuration
JIRA_URL = os.getenv('JIRA_URL', 'https://learn-to-flow.atlassian.net')
JIRA_USERNAME = os.getenv('JIRA_USERNAME', 'philippebeliveau@ezbi.ca')
JIRA_API_KEY = os.getenv('JIRA_API_KEY')
PROJECT_KEY = 'CPG'  # Learn-to-flow project key

def connect_to_jira():
    """Connect to Jira using API key"""
    try:
        jira = JIRA(
            server=JIRA_URL,
            basic_auth=(JIRA_USERNAME, JIRA_API_KEY)
        )
        print(f"✅ Connected to Jira: {JIRA_URL}")
        return jira
    except Exception as e:
        print(f"❌ Failed to connect to Jira: {e}")
        return None

def create_epic(jira, epic_data):
    """Create an epic in Jira"""
    try:
        issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': epic_data['summary'],
            'description': epic_data['description'],
            'issuetype': {'name': 'Epic'},
            'customfield_10011': epic_data['key'],  # Epic Name field
            'priority': {'name': epic_data['priority']},
            'labels': epic_data['labels']
        }
        
        epic = jira.create_issue(fields=issue_dict)
        print(f"✅ Created Epic: {epic.key} - {epic_data['summary']}")
        return epic
    except Exception as e:
        print(f"❌ Failed to create epic {epic_data['key']}: {e}")
        return None

def create_story(jira, story_data, epic_key):
    """Create a story in Jira"""
    try:
        # Format description with acceptance criteria and technical requirements
        description = f"{story_data['description']}\n\n"
        description += "h3. Acceptance Criteria\n"
        for criteria in story_data['acceptance_criteria']:
            description += f"* {criteria}\n"
        
        description += "\nh3. Technical Requirements\n"
        for req in story_data['technical_requirements']:
            description += f"* {req}\n"
        
        issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': story_data['summary'],
            'description': description,
            'issuetype': {'name': 'Story'},
            'priority': {'name': story_data['priority']},
            'labels': story_data['labels'],
            'customfield_10014': epic_key,  # Epic Link field
        }
        
        # Add story points if available
        if 'story_points' in story_data:
            issue_dict['customfield_10016'] = story_data['story_points']  # Story Points field
        
        story = jira.create_issue(fields=issue_dict)
        print(f"✅ Created Story: {story.key} - {story_data['summary']}")
        return story
    except Exception as e:
        print(f"❌ Failed to create story {story_data['summary']}: {e}")
        return None

def main():
    """Main function to import user stories to Jira"""
    print("🚀 Starting EZBI Analytics User Stories Import to Jira")
    print(f"📊 Project: {PROJECT_KEY}")
    print(f"🔗 Jira URL: {JIRA_URL}")
    
    # Connect to Jira
    jira = connect_to_jira()
    if not jira:
        sys.exit(1)
    
    # Load user stories
    try:
        with open('jira_user_stories.json', 'r') as f:
            data = json.load(f)
        print(f"📋 Loaded {len(data['epics'])} epics from file")
    except Exception as e:
        print(f"❌ Failed to load user stories: {e}")
        sys.exit(1)
    
    # Create epics and stories
    created_epics = 0
    created_stories = 0
    
    for epic_data in data['epics']:
        print(f"\n🎯 Processing Epic: {epic_data['summary']}")
        
        # Create epic
        epic = create_epic(jira, epic_data)
        if epic:
            created_epics += 1
            
            # Create stories for this epic
            for story_data in epic_data['stories']:
                story = create_story(jira, story_data, epic.key)
                if story:
                    created_stories += 1
    
    print(f"\n🎉 Import Complete!")
    print(f"✅ Created {created_epics} epics")
    print(f"✅ Created {created_stories} stories")
    print(f"🔗 View project: {JIRA_URL}/projects/{PROJECT_KEY}")

if __name__ == "__main__":
    main()