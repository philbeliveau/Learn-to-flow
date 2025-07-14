#!/usr/bin/env node

/**
 * Test Jira Connection Script
 * Tests the connection to Jira using the configured credentials
 */

const https = require('https');
const url = require('url');

// Load environment variables
require('dotenv').config();

const JIRA_URL = process.env.JIRA_URL;
const JIRA_USERNAME = process.env.JIRA_USERNAME;
const JIRA_API_KEY = process.env.JIRA_API_KEY;

if (!JIRA_URL || !JIRA_USERNAME || !JIRA_API_KEY) {
  console.error('❌ Missing Jira configuration. Please check .env file');
  process.exit(1);
}

console.log('🔧 Testing Jira Connection...');
console.log(`📍 URL: ${JIRA_URL}`);
console.log(`👤 Username: ${JIRA_USERNAME}`);
console.log('');

// Test connection to Jira
async function testJiraConnection() {
  const auth = Buffer.from(`${JIRA_USERNAME}:${JIRA_API_KEY}`).toString('base64');
  
  const options = {
    hostname: url.parse(JIRA_URL).hostname,
    port: 443,
    path: '/rest/api/3/myself',
    method: 'GET',
    headers: {
      'Authorization': `Basic ${auth}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const user = JSON.parse(data);
            console.log('✅ Jira connection successful!');
            console.log(`👋 Logged in as: ${user.displayName} (${user.emailAddress})`);
            console.log(`🆔 Account ID: ${user.accountId}`);
            resolve(user);
          } catch (error) {
            reject(new Error('Failed to parse response'));
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
}

// Test getting projects
async function testGetProjects() {
  const auth = Buffer.from(`${JIRA_USERNAME}:${JIRA_API_KEY}`).toString('base64');
  
  const options = {
    hostname: url.parse(JIRA_URL).hostname,
    port: 443,
    path: '/rest/api/3/project',
    method: 'GET',
    headers: {
      'Authorization': `Basic ${auth}`,
      'Accept': 'application/json'
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const projects = JSON.parse(data);
            console.log(`📊 Found ${projects.length} projects`);
            
            if (projects.length > 0) {
              console.log('📋 Available projects:');
              projects.forEach(project => {
                console.log(`  - ${project.name} (${project.key})`);
              });
            } else {
              console.log('⚠️  No projects found. You may need to create one first.');
            }
            resolve(projects);
          } catch (error) {
            reject(new Error('Failed to parse projects response'));
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
}

// Create EZBI project if it doesn't exist
async function createEzbiProject() {
  const auth = Buffer.from(`${JIRA_USERNAME}:${JIRA_API_KEY}`).toString('base64');
  
  const projectData = {
    key: 'EZBI',
    name: 'EZBI Analytics',
    projectTypeKey: 'software',
    description: 'AI-Powered Cash Flow Prediction Platform for French Manufacturing SMEs',
    leadAccountId: null, // Will be set to current user
    projectTemplateKey: 'com.pyxis.greenhopper.jira:gh-simplified-agility-kanban'
  };

  const options = {
    hostname: url.parse(JIRA_URL).hostname,
    port: 443,
    path: '/rest/api/3/project',
    method: 'POST',
    headers: {
      'Authorization': `Basic ${auth}`,
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 201) {
          try {
            const project = JSON.parse(data);
            console.log('🎉 EZBI project created successfully!');
            console.log(`📋 Project: ${project.name} (${project.key})`);
            resolve(project);
          } catch (error) {
            reject(new Error('Failed to parse create project response'));
          }
        } else {
          console.log(`⚠️  Could not create project (HTTP ${res.statusCode})`);
          console.log('Response:', data);
          resolve(null);
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(JSON.stringify(projectData));
    req.end();
  });
}

// Main execution
async function main() {
  try {
    // Test connection
    const user = await testJiraConnection();
    console.log('');

    // Get projects
    const projects = await testGetProjects();
    console.log('');

    // Check if EZBI project exists
    const ezbiProject = projects.find(p => p.key === 'EZBI');
    
    if (!ezbiProject && projects.length === 0) {
      console.log('🚀 Creating EZBI Analytics project...');
      await createEzbiProject();
    }

    console.log('');
    console.log('✅ Jira integration is ready for EZBI Analytics!');
    console.log('');
    console.log('Next steps:');
    console.log('  1. Restart Claude Code to load Jira MCP server');
    console.log('  2. Use Jira MCP tools to create epics and stories');
    console.log('  3. Link GitHub commits to Jira issues');
    
  } catch (error) {
    console.error('❌ Jira connection failed:', error.message);
    process.exit(1);
  }
}

main();