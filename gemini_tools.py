# gemini_tools.py - Agentic Tool System for Gemini WebUI

import os
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
import git
from datetime import datetime
import requests
import base64
import ipaddress
import socket
from typing import Dict, Any


class ToolExecutionResult:
    def __init__(self, success: bool, output: str, error: str = "", metadata: Dict = None):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class BaseTool(ABC):
    def __init__(self, name: str):
        self.name = name
        self.safety_level = "safe"  # safe, moderate, dangerous
        
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        pass

class FileOperationsTool(BaseTool):
    def __init__(self):
        super().__init__("file_operations")
        self.safety_level = "moderate"
        
    def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        operation = parameters.get("operation")
        path = parameters.get("path")
        content = parameters.get("content", "")
        
        try:
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                return self._write_file(path, content)
            elif operation == "create_directory":
                return self._create_directory(path)
            elif operation == "list_directory":
                return self._list_directory(path)
            elif operation == "search":
                pattern = parameters.get("pattern", "")
                return self._search_files(path, pattern)
            else:
                return ToolExecutionResult(False, "", f"Unknown operation: {operation}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _read_file(self, path: str) -> ToolExecutionResult:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolExecutionResult(True, content, metadata={"file_size": len(content)})
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _write_file(self, path: str, content: str) -> ToolExecutionResult:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolExecutionResult(True, f"Successfully wrote {len(content)} characters to {path}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _create_directory(self, path: str) -> ToolExecutionResult:
        try:
            os.makedirs(path, exist_ok=True)
            return ToolExecutionResult(True, f"Directory created: {path}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _list_directory(self, path: str) -> ToolExecutionResult:
        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                items.append({
                    "name": item,
                    "type": "directory" if is_dir else "file",
                    "size": size,
                    "path": item_path
                })
            return ToolExecutionResult(True, json.dumps(items, indent=2))
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _search_files(self, path: str, pattern: str) -> ToolExecutionResult:
        try:
            import glob
            matches = glob.glob(os.path.join(path, "**", pattern), recursive=True)
            return ToolExecutionResult(True, json.dumps(matches, indent=2))
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def get_help(self) -> str:
        return """
File Operations Tool:
- read: Read file content
- write: Write content to file
- create_directory: Create directory
- list_directory: List directory contents
- search: Search for files matching pattern

Parameters:
- operation: The operation to perform
- path: File or directory path
- content: Content to write (for write operation)
- pattern: Search pattern (for search operation)
"""

class BashCommandsTool(BaseTool):
    def __init__(self):
        super().__init__("bash_commands")
        self.safety_level = "dangerous"
        self.safe_commands = {
            "ls", "pwd", "echo", "cat", "head", "tail", "wc", "grep", "find",
            "git status", "git log", "git diff", "npm list", "pip list"
        }
        self.blocked_commands = {
            "rm -rf", "sudo", "chmod 777", "dd", "mkfs", "fdisk", "kill -9"
        }
    
    def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        command = parameters.get("command", "").strip()
        working_dir = parameters.get("working_dir", os.getcwd())
        timeout = parameters.get("timeout", 30)
        
        if not command:
            return ToolExecutionResult(False, "", "No command provided")
        
        # Safety check
        safety_check = self._check_command_safety(command)
        if not safety_check[0]:
            return ToolExecutionResult(False, "", f"Command blocked for safety: {safety_check[1]}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return ToolExecutionResult(
                success, 
                output, 
                "" if success else f"Command exited with code {result.returncode}",
                metadata={"return_code": result.returncode, "working_dir": working_dir}
            )
        except subprocess.TimeoutExpired:
            return ToolExecutionResult(False, "", f"Command timed out after {timeout} seconds")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _check_command_safety(self, command: str) -> Tuple[bool, str]:
        # Check if command contains blocked patterns
        for blocked in self.blocked_commands:
            if blocked in command.lower():
                return False, f"Contains blocked pattern: {blocked}"
        
        # Check if it's a known safe command
        command_base = command.split()[0] if command.split() else ""
        if command_base in self.safe_commands or command in self.safe_commands:
            return True, "Safe command"
        
        # For other commands, require explicit approval
        return True, "Requires approval"
    
    def get_help(self) -> str:
        return """
Bash Commands Tool:
Execute bash commands with safety checks.

Parameters:
- command: The bash command to execute
- working_dir: Working directory (optional)
- timeout: Command timeout in seconds (default: 30)

Safety Features:
- Blocked dangerous commands
- Safe command whitelist
- Timeout protection
"""

class GitOperationsTool(BaseTool):
    def __init__(self):
        super().__init__("git_operations")
        self.safety_level = "moderate"
    
    def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        operation = parameters.get("operation")
        repo_path = parameters.get("repo_path", os.getcwd())
        
        try:
            repo = git.Repo(repo_path)
            
            if operation == "status":
                return self._get_status(repo)
            elif operation == "log":
                limit = parameters.get("limit", 10)
                return self._get_log(repo, limit)
            elif operation == "diff":
                return self._get_diff(repo)
            elif operation == "commit":
                message = parameters.get("message", "")
                files = parameters.get("files", [])
                return self._commit_changes(repo, message, files)
            elif operation == "create_branch":
                branch_name = parameters.get("branch_name", "")
                return self._create_branch(repo, branch_name)
            elif operation == "switch_branch":
                branch_name = parameters.get("branch_name", "")
                return self._switch_branch(repo, branch_name)
            else:
                return ToolExecutionResult(False, "", f"Unknown operation: {operation}")
        except git.exc.InvalidGitRepositoryError:
            return ToolExecutionResult(False, "", "Not a valid Git repository")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _get_status(self, repo: git.Repo) -> ToolExecutionResult:
        status_info = {
            "current_branch": repo.active_branch.name,
            "untracked_files": repo.untracked_files,
            "modified_files": [item.a_path for item in repo.index.diff(None)],
            "staged_files": [item.a_path for item in repo.index.diff("HEAD")]
        }
        return ToolExecutionResult(True, json.dumps(status_info, indent=2))
    
    def _get_log(self, repo: git.Repo, limit: int) -> ToolExecutionResult:
        commits = []
        for commit in repo.iter_commits(max_count=limit):
            commits.append({
                "hash": commit.hexsha[:8],
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip()
            })
        return ToolExecutionResult(True, json.dumps(commits, indent=2))
    
    def _get_diff(self, repo: git.Repo) -> ToolExecutionResult:
        diff = repo.git.diff()
        return ToolExecutionResult(True, diff)
    
    def _commit_changes(self, repo: git.Repo, message: str, files: List[str]) -> ToolExecutionResult:
        if not message:
            return ToolExecutionResult(False, "", "Commit message is required")
        
        try:
            if files:
                repo.index.add(files)
            else:
                repo.git.add(A=True)  # Add all files
            
            commit = repo.index.commit(message)
            return ToolExecutionResult(True, f"Committed: {commit.hexsha[:8]} - {message}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _create_branch(self, repo: git.Repo, branch_name: str) -> ToolExecutionResult:
        try:
            new_branch = repo.create_head(branch_name)
            return ToolExecutionResult(True, f"Created branch: {branch_name}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def _switch_branch(self, repo: git.Repo, branch_name: str) -> ToolExecutionResult:
        try:
            repo.git.checkout(branch_name)
            return ToolExecutionResult(True, f"Switched to branch: {branch_name}")
        except Exception as e:
            return ToolExecutionResult(False, "", str(e))
    
    def get_help(self) -> str:
        return """
Git Operations Tool:
- status: Get repository status
- log: Get commit history
- diff: Get current diff
- commit: Commit changes
- create_branch: Create new branch
- switch_branch: Switch to branch

Parameters:
- operation: The git operation to perform
- repo_path: Repository path (optional, defaults to current directory)
- message: Commit message (for commit operation)
- files: List of files to commit (optional, defaults to all)
- branch_name: Branch name (for branch operations)
- limit: Number of commits to show (for log operation)
"""


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__("web_search")
        self.safety_level = "safe"
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")

    def execute(self, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """
        Executes either a web search or a URL fetch operation.
        """
        operation = parameters.get("operation", "search")

        if operation == "search":
            query = parameters.get("query", "")
            if not query:
                return ToolExecutionResult(False, "", "Missing 'query' parameter for search.")
            return self._search_web(query)

        elif operation == "fetch":
            url = parameters.get("url", "")
            if not url:
                return ToolExecutionResult(False, "", "Missing 'url' parameter for fetch.")
            return self._fetch_url(url)

        else:
            return ToolExecutionResult(False, "", f"Unknown operation: {operation}")

    def _is_safe_url(self, url: str) -> bool:
        """
        Prevents requests to private, local, or reserved IP addresses (SSRF protection).
        """
        try:
            # Get hostname from URL
            hostname = url.split('//')[-1].split('/')[0].split(':')[0]
            
            # Resolve hostname to IP address
            ip_addr = socket.gethostbyname(hostname)
            
            # Check if the IP address is private
            return not ipaddress.ip_address(ip_addr).is_private
        except (socket.gaierror, ValueError):
            # If hostname can't be resolved or IP is invalid, block it.
            return False

    def _fetch_url(self, url: str) -> ToolExecutionResult:
        """
        Safely fetches content from a public URL.
        """
        if not self._is_safe_url(url):
            return ToolExecutionResult(False, "", "Security Error: URL resolves to a private or local network address.")

        try:
            headers = {'User-Agent': 'GeminiAgent/1.0'}
            response = requests.get(url, timeout=10, stream=True, headers=headers)
            response.raise_for_status()

            # Check content type to avoid fetching large binary files
            content_type = response.headers.get('content-type', '').lower()
            if not ('text/html' in content_type or 'text/plain' in content_type or 'application/json' in content_type):
                return ToolExecutionResult(False, "", f"Unsupported content type: {content_type}. Only text-based content is allowed.")

            # Read a maximum of ~1MB to avoid memory issues
            max_size = 1024 * 1024
            content = response.raw.read(max_size, decode_content=True)
            
            # Note: For production, parsing HTML with BeautifulSoup to extract clean text is recommended.
            # For this tool, we return the raw content snippet.
            return ToolExecutionResult(True, content.decode('utf-8', errors='ignore'))

        except requests.RequestException as e:
            return ToolExecutionResult(False, "", f"Error fetching URL: {str(e)}")

    def _search_web(self, query: str) -> ToolExecutionResult:
        """
        Performs a web search using the Google Custom Search JSON API.
        """
        if not self.google_api_key or not self.google_cse_id:
            return ToolExecutionResult(False, "", "Configuration Error: GOOGLE_API_KEY and GOOGLE_CSE_ID must be set as environment variables.")

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cse_id,
            'q': query,
            'num': 5  # Request top 5 results
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            search_results = response.json()

            # Format the output for the AI
            output = f"Search results for '{query}':\n\n"
            if "items" in search_results:
                for item in search_results["items"]:
                    output += f"Title: {item.get('title', 'N/A')}\n"
                    output += f"Link: {item.get('link', 'N/A')}\n"
                    output += f"Snippet: {item.get('snippet', 'N/A')}\n---\n"
                return ToolExecutionResult(True, output)
            else:
                return ToolExecutionResult(True, f"No search results found for '{query}'.")

        except requests.RequestException as e:
            return ToolExecutionResult(False, "", f"Error during web search: {str(e)}")
        except Exception as e:
            return ToolExecutionResult(False, "", f"An unexpected error occurred during search: {str(e)}")

    def get_help(self) -> str:
        return """
Web Search Tool: Provides tools to search the web and fetch content from URLs.
- operation: "search" or "fetch"
  - "search": Searches the web using a query.
    - query: The string to search for.
  - "fetch": Retrieves the text-based content of a public URL.
    - url: The public URL to fetch.
NOTE: The 'search' operation requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.
"""
  

    


class GeminiToolSystem:
    def __init__(self, gemini_session):
        self.session = gemini_session
        self.tools = {
            "file_operations": FileOperationsTool(),
            "bash_commands": BashCommandsTool(),
            "git_operations": GitOperationsTool(),
            "web_search": WebSearchTool()
        }
        self.auto_approve_tools = set()
        self.blocked_tools = set()
        
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool with the given parameters"""
        if tool_name not in self.tools:
            return ToolExecutionResult(False, "", f"Tool not found: {tool_name}")
        
        if tool_name in self.blocked_tools:
            return ToolExecutionResult(False, "", f"Tool is blocked: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Check if tool requires approval
        if (tool.safety_level in ["dangerous", "moderate"] and 
            tool_name not in self.auto_approve_tools):
            # In a real implementation, this would prompt the user for approval
            print(f"⚠️  Tool {tool_name} requires approval (safety level: {tool.safety_level})")
        
        return tool.execute(parameters)
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools with their descriptions"""
        return {name: tool.get_help() for name, tool in self.tools.items()}
    
    def set_auto_approve(self, tool_names: List[str]):
        """Set tools to auto-approve"""
        self.auto_approve_tools.update(tool_names)
    
    def block_tools(self, tool_names: List[str]):
        """Block specific tools"""
        self.blocked_tools.update(tool_names)
    
    def get_tool_usage_prompt(self) -> str:
        """Generate a prompt that explains available tools to the AI"""
        tools_description = "Available tools:\n"
        for name, tool in self.tools.items():
            tools_description += f"\n{name}: {tool.get_help()}\n"
        
        tools_description += """
To use a tool, format your request as:
TOOL_USE: {
  "tool": "tool_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}

Multiple tools can be used in sequence to accomplish complex tasks.
"""
        return tools_description