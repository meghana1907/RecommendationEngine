import requests
import base64
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logger import debug_logger
from app.models.schemas import JiraCredentials, JiraUserStory, JiraProject

class JiraService:
    """Service for integrating with Jira API to import user stories"""
    
    def __init__(self):
        self.base_url = None
        self.auth_header = None
        self.session = requests.Session()
    
    def authenticate(self, credentials: JiraCredentials) -> bool:
        """Authenticate with Jira using provided credentials"""
        try:
            self.base_url = credentials.base_url.rstrip('/')
            
            # Create basic auth header
            auth_string = f"{credentials.username}:{credentials.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            self.auth_header = f"Basic {auth_b64}"
            self.session.headers.update({
                'Authorization': self.auth_header,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            # Test connection
            response = self.session.get(f"{self.base_url}/rest/api/3/myself")
            if response.status_code == 200:
                user_info = response.json()
                debug_logger.log_user_action(
                    user_info.get('emailAddress', 'unknown'),
                    "jira_authentication_success"
                )
                return True
            else:
                debug_logger.log_error("jira_authentication", 
                                     Exception(f"Authentication failed: {response.status_code}"))
                return False
                
        except Exception as e:
            debug_logger.log_error("jira_authentication", e)
            return False
    
    def get_projects(self) -> List[JiraProject]:
        """Get list of accessible Jira projects"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/project")
            if response.status_code == 200:
                projects_data = response.json()
                projects = []
                
                for project in projects_data:
                    projects.append(JiraProject(
                        key=project['key'],
                        name=project['name'],
                        id=project['id']
                    ))
                
                debug_logger.log_user_action("system", "jira_projects_fetched", 
                                           {"count": len(projects)})
                return projects
            else:
                debug_logger.log_error("jira_get_projects", 
                                     Exception(f"Failed to fetch projects: {response.status_code}"))
                return []
                
        except Exception as e:
            debug_logger.log_error("jira_get_projects", e)
            return []
    
    def search_user_stories(self, project_key: str, jql_query: Optional[str] = None, 
                           include_subtasks: bool = False) -> List[JiraUserStory]:
        """Search for user stories in a specific project"""
        try:
            # Build JQL query
            if jql_query:
                jql = jql_query
            else:
                # Default query for user stories
                issue_types = "Story"
                if include_subtasks:
                    issue_types += ",Sub-task"
                
                jql = f'project = "{project_key}" AND issuetype in ({issue_types}) ORDER BY created DESC'
            
            # Search issues
            search_url = f"{self.base_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'maxResults': 100,  # Adjust as needed
                'fields': 'summary,description,customfield_10016,priority,status,assignee'  # customfield_10016 is typically story points
            }
            
            response = self.session.get(search_url, params=params)
            
            if response.status_code == 200:
                search_results = response.json()
                user_stories = []
                
                for issue in search_results.get('issues', []):
                    # Extract story points (may vary by Jira setup)
                    story_points = None
                    if 'customfield_10016' in issue['fields'] and issue['fields']['customfield_10016']:
                        story_points = int(issue['fields']['customfield_10016'])
                    
                    # Extract assignee
                    assignee = None
                    if issue['fields'].get('assignee'):
                        assignee = issue['fields']['assignee'].get('displayName', 'Unassigned')
                    
                    user_story = JiraUserStory(
                        key=issue['key'],
                        summary=issue['fields']['summary'],
                        description=issue['fields'].get('description', '') or '',
                        story_points=story_points,
                        priority=issue['fields']['priority']['name'] if issue['fields'].get('priority') else 'Medium',
                        status=issue['fields']['status']['name'] if issue['fields'].get('status') else 'To Do',
                        assignee=assignee
                    )
                    user_stories.append(user_story)
                
                debug_logger.log_jira_import(project_key, len(user_stories))
                return user_stories
            else:
                debug_logger.log_error("jira_search_stories", 
                                     Exception(f"Search failed: {response.status_code} - {response.text}"))
                return []
                
        except Exception as e:
            debug_logger.log_error("jira_search_stories", e)
            return []
    
    def format_stories_as_document(self, user_stories: List[JiraUserStory], 
                                 project_key: str) -> str:
        """Format user stories as a structured document for processing"""
        try:
            document_content = f"# User Stories from Jira Project: {project_key}\n\n"
            document_content += f"Total Stories: {len(user_stories)}\n"
            document_content += f"Import Date: {debug_logger.logger.handlers[0].formatter.formatTime(debug_logger.logger.makeRecord('', 0, '', 0, '', (), None))}\n\n"
            
            for i, story in enumerate(user_stories, 1):
                document_content += f"## User Story {i}: {story.key}\n\n"
                document_content += f"**Summary:** {story.summary}\n\n"
                
                if story.description:
                    document_content += f"**Description:**\n{story.description}\n\n"
                
                document_content += f"**Priority:** {story.priority}\n"
                document_content += f"**Status:** {story.status}\n"
                
                if story.story_points:
                    document_content += f"**Story Points:** {story.story_points}\n"
                
                if story.assignee:
                    document_content += f"**Assignee:** {story.assignee}\n"
                
                document_content += "\n---\n\n"
            
            debug_logger.log_user_action("system", "jira_document_formatted", 
                                       {"stories_count": len(user_stories), 
                                        "document_length": len(document_content)})
            
            return document_content
            
        except Exception as e:
            debug_logger.log_error("jira_format_document", e)
            return f"Error formatting Jira stories: {str(e)}"
    
    def test_connection(self, credentials: JiraCredentials) -> Dict[str, Any]:
        """Test Jira connection and return connection details"""
        try:
            if not self.authenticate(credentials):
                return {"success": False, "error": "Authentication failed"}
            
            # Get user info
            user_response = self.session.get(f"{self.base_url}/rest/api/3/myself")
            user_info = user_response.json() if user_response.status_code == 200 else {}
            
            # Get accessible projects count
            projects = self.get_projects()
            
            return {
                "success": True,
                "user": {
                    "name": user_info.get('displayName', 'Unknown'),
                    "email": user_info.get('emailAddress', 'Unknown')
                },
                "accessible_projects": len(projects),
                "jira_version": user_info.get('expand', 'Unknown')
            }
            
        except Exception as e:
            debug_logger.log_error("jira_test_connection", e)
            return {"success": False, "error": str(e)}

# Global Jira service instance
jira_service = JiraService()