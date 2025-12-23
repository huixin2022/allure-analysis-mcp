"""
Jira Client Module for MCP Server
Provides token-based authentication and common Jira operations.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import base64


@dataclass
class JiraConfig:
    """Jira configuration from environment variables."""
    base_url: str
    email: str
    api_token: str
    
    @classmethod
    def from_env(cls) -> 'JiraConfig':
        """Create config from environment variables."""
        base_url = os.environ.get('JIRA_BASE_URL', '').rstrip('/')
        email = os.environ.get('JIRA_EMAIL', '')
        api_token = os.environ.get('JIRA_API_TOKEN', '')
        
        if not all([base_url, email, api_token]):
            missing = []
            if not base_url:
                missing.append('JIRA_BASE_URL')
            if not email:
                missing.append('JIRA_EMAIL')
            if not api_token:
                missing.append('JIRA_API_TOKEN')
            raise ValueError(f"Missing Jira environment variables: {', '.join(missing)}")
        
        return cls(base_url=base_url, email=email, api_token=api_token)


class JiraClient:
    """Jira REST API client with token authentication."""
    
    def __init__(self, config: Optional[JiraConfig] = None):
        """Initialize Jira client with config or environment variables."""
        self.config = config or JiraConfig.from_env()
        self._session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup Basic authentication with API token."""
        # Jira Cloud uses Basic Auth with email:api_token
        auth_string = f"{self.config.email}:{self.config.api_token}"
        auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        self._session.headers.update({
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Jira API."""
        url = f"{self.config.base_url}/rest/api/3/{endpoint.lstrip('/')}"
        response = self._session.request(method, url, **kwargs)
        
        if not response.ok:
            error_msg = response.text
            try:
                error_data = response.json()
                if 'errorMessages' in error_data:
                    error_msg = '; '.join(error_data['errorMessages'])
                elif 'errors' in error_data:
                    error_msg = str(error_data['errors'])
            except:
                pass
            raise JiraAPIError(
                f"Jira API error ({response.status_code}): {error_msg}",
                status_code=response.status_code
            )
        
        if response.status_code == 204:
            return {}
        return response.json()
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request to Jira API."""
        return self._request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """POST request to Jira API."""
        return self._request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """PUT request to Jira API."""
        return self._request('PUT', endpoint, json=data)
    
    # ==================== High-Level Operations ====================
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and return current user info."""
        return self.get('myself')
    
    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get issue details by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Optional list of fields to return
        """
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        return self.get(f'issue/{issue_key}', params=params)
    
    def search_issues(self, jql: str, max_results: int = 50, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results (default 50)
            fields: Optional list of fields to return
        """
        # Use the new /search/jql endpoint (migrated from deprecated /search)
        # See: https://developer.atlassian.com/changelog/#CHANGE-2046
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': ','.join(fields or ['summary', 'status', 'priority', 'assignee', 'created', 'updated'])
        }
        return self.get('search/jql', params=params)
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = 'Bug',
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue.
        
        Args:
            project_key: Project key (e.g., 'PROJ')
            summary: Issue summary/title
            description: Issue description (supports Atlassian Document Format or plain text)
            issue_type: Issue type name (default 'Bug')
            priority: Priority name (e.g., 'High', 'Medium', 'Low')
            labels: List of labels
            components: List of component names
            custom_fields: Additional custom fields
        
        Returns:
            Created issue data including key
        """
        # Build description in Atlassian Document Format (ADF)
        description_content = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description
                        }
                    ]
                }
            ]
        }
        
        fields = {
            'project': {'key': project_key},
            'summary': summary,
            'description': description_content,
            'issuetype': {'name': issue_type}
        }
        
        if priority:
            fields['priority'] = {'name': priority}
        
        if labels:
            fields['labels'] = labels
        
        if components:
            fields['components'] = [{'name': c} for c in components]
        
        if custom_fields:
            fields.update(custom_fields)
        
        return self.post('issue', {'fields': fields})
    
    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment: Comment text
        """
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        return self.post(f'issue/{issue_key}/comment', body)
    
    def get_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for an issue."""
        return self.get(f'issue/{issue_key}/transitions')
    
    def transition_issue(self, issue_key: str, transition_id: str, comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Transition an issue to a new status.
        
        Args:
            issue_key: Issue key
            transition_id: Transition ID (get from get_transitions)
            comment: Optional comment to add
        """
        data = {
            'transition': {'id': transition_id}
        }
        if comment:
            data['update'] = {
                'comment': [{
                    'add': {
                        'body': {
                            "type": "doc",
                            "version": 1,
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": comment}]
                            }]
                        }
                    }
                }]
            }
        return self._request('POST', f'issue/{issue_key}/transitions', json=data)
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of accessible projects."""
        return self.get('project')
    
    def get_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get available issue types for a project."""
        project = self.get(f'project/{project_key}')
        return project.get('issueTypes', [])


class JiraAPIError(Exception):
    """Jira API error with status code."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


# Singleton instance for easy access
_client: Optional[JiraClient] = None


def get_jira_client() -> JiraClient:
    """Get or create Jira client singleton."""
    global _client
    if _client is None:
        _client = JiraClient()
    return _client


def is_jira_configured() -> bool:
    """Check if Jira environment variables are configured."""
    return all([
        os.environ.get('JIRA_BASE_URL'),
        os.environ.get('JIRA_EMAIL'),
        os.environ.get('JIRA_API_TOKEN')
    ])

