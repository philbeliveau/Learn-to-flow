#!/usr/bin/env python3
"""
EZBI Analytics - Simplified Jira Stories Import
Creates stories without epics for basic Jira setup
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
PROJECT_KEY = 'CPG'

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

def get_project_metadata(jira):
    """Get project metadata to understand available fields"""
    try:
        project = jira.project(PROJECT_KEY)
        print(f"📊 Project: {project.name}")
        
        # Get create meta for issue types
        create_meta = jira.createmeta(projectKeys=PROJECT_KEY)
        print(f"📋 Available issue types:")
        for issue_type in create_meta['projects'][0]['issuetypes']:
            print(f"  - {issue_type['name']}")
        
        return create_meta
    except Exception as e:
        print(f"❌ Failed to get project metadata: {e}")
        return None

def create_story(jira, epic_name, story_data):
    """Create a story in Jira with basic fields"""
    try:
        # Format description with epic info, acceptance criteria and technical requirements
        description = f"*Epic: {epic_name}*\n\n"
        description += f"{story_data['description']}\n\n"
        description += "h3. Acceptance Criteria\n"
        for criteria in story_data['acceptance_criteria']:
            description += f"* {criteria}\n"
        
        description += "\nh3. Technical Requirements\n"
        for req in story_data['technical_requirements']:
            description += f"* {req}\n"
        
        # Basic issue creation with minimal fields
        issue_dict = {
            'project': {'key': PROJECT_KEY},
            'summary': f"[{epic_name}] {story_data['summary']}",
            'description': description,
            'issuetype': {'name': 'Story'},
            'labels': story_data['labels']
        }
        
        story = jira.create_issue(fields=issue_dict)
        print(f"✅ Created Story: {story.key} - {story_data['summary']}")
        return story
    except Exception as e:
        print(f"❌ Failed to create story {story_data['summary']}: {e}")
        return None

def main():
    """Main function to import user stories to Jira"""
    print("🚀 Starting EZBI Analytics User Stories Import (Simplified)")
    print(f"📊 Project: {PROJECT_KEY}")
    print(f"🔗 Jira URL: {JIRA_URL}")
    
    # Connect to Jira
    jira = connect_to_jira()
    if not jira:
        sys.exit(1)
    
    # Get project metadata
    meta = get_project_metadata(jira)
    if not meta:
        sys.exit(1)
    
    # Load user stories
    try:
        with open('jira_user_stories.json', 'r') as f:
            data = json.load(f)
        print(f"📋 Loaded {len(data['epics'])} epics from file")
    except Exception as e:
        print(f"❌ Failed to load user stories: {e}")
        sys.exit(1)
    
    # Create stories without epics
    created_stories = 0
    
    for epic_data in data['epics']:
        epic_name = epic_data['summary']
        print(f"\n🎯 Processing Epic: {epic_name}")
        
        # Create stories for this epic
        for story_data in epic_data['stories']:
            story = create_story(jira, epic_name, story_data)
            if story:
                created_stories += 1
    
    print(f"\n🎉 Import Complete!")
    print(f"✅ Created {created_stories} stories")
    print(f"🔗 View project: {JIRA_URL}/projects/{PROJECT_KEY}")

if __name__ == "__main__":
    main()