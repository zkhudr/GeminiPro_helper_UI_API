# gemini_context.py - Advanced Context Management System

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import fnmatch

@dataclass
class ContextEntry:
    content: str
    source: str
    priority: int = 1  # 1-10, higher = more important
    scope: str = "session"  # session, project, user, global
    tags: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.timestamp is None:
            self.timestamp = datetime.now()

class GeminiMemorySystem:
    def __init__(self, base_path: str = ".gemini"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        self.memory_files = {
            "session": self.base_path / "session_memory.json",
            "project": self.base_path / "project_memory.json", 
            "user": Path.home() / ".gemini" / "user_memory.json",
            "global": Path.home() / ".gemini" / "global_memory.json"
        }
        
        # Ensure user directory exists
        (Path.home() / ".gemini").mkdir(exist_ok=True)
    
    def remember(self, key: str, content: str, scope: str = "session", tags: List[str] = None):
        """Add content to memory"""
        memory_file = self.memory_files.get(scope)
        if not memory_file:
            raise ValueError(f"Invalid scope: {scope}")
        
        # Load existing memory
        memory = self._load_memory(memory_file)
        
        # Add new entry
        entry = ContextEntry(
            content=content,
            source=f"user_memory_{scope}",
            scope=scope,
            tags=tags or []
        )
        
        memory[key] = asdict(entry)
        
        # Save memory
        self._save_memory(memory_file, memory)
    
    def recall(self, key: str, scope: str = None) -> Optional[str]:
        """Recall content from memory"""
        if scope:
            scopes = [scope]
        else:
            scopes = ["session", "project", "user", "global"]
        
        for scope in scopes:
            memory_file = self.memory_files.get(scope)
            if memory_file and memory_file.exists():
                memory = self._load_memory(memory_file)
                if key in memory:
                    return memory[key]["content"]
        
        return None
    
    def search_memory(self, query: str, scope: str = None) -> List[Dict]:
        """Search memory by content or tags"""
        results = []
        
        if scope:
            scopes = [scope]
        else:
            scopes = ["session", "project", "user", "global"]
        
        for scope in scopes:
            memory_file = self.memory_files.get(scope)
            if memory_file and memory_file.exists():
                memory = self._load_memory(memory_file)
                for key, entry in memory.items():
                    if (query.lower() in entry["content"].lower() or 
                        any(query.lower() in tag.lower() for tag in entry["tags"])):
                        results.append({
                            "key": key,
                            "scope": scope,
                            "content": entry["content"][:200] + "..." if len(entry["content"]) > 200 else entry["content"],
                            "tags": entry["tags"]
                        })
        
        return results
    
    def get_all_memory(self, scope: str = None) -> Dict[str, Any]:
        """Get all memory entries"""
        all_memory = {}
        
        if scope:
            scopes = [scope]
        else:
            scopes = ["session", "project", "user", "global"]
        
        for scope in scopes:
            memory_file = self.memory_files.get(scope)
            if memory_file and memory_file.exists():
                memory = self._load_memory(memory_file)
                all_memory[scope] = memory
        
        return all_memory
    
    def clear_memory(self, scope: str = "session"):
        """Clear memory for a specific scope"""
        memory_file = self.memory_files.get(scope)
        if memory_file and memory_file.exists():
            self._save_memory(memory_file, {})
    
    def _load_memory(self, file_path: Path) -> Dict:
        """Load memory from file"""
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_memory(self, file_path: Path, memory: Dict):
        """Save memory to file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, default=str)

class GeminiContextManager:
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.memory_system = GeminiMemorySystem()
        self.context_cache = {}
        
        # Context file patterns
        self.context_files = {
            "gemini_md": ["gemini.md", ".gemini/context.md"],
            "project_config": [".gemini/config.yaml", ".gemini/project.yaml"],
            "user_config": [str(Path.home() / ".gemini" / "config.yaml")],
            "readme": ["README.md", "readme.md", "README.txt"],
            "docs": ["docs/**/*.md", "documentation/**/*.md"],
            "package_info": ["package.json", "requirements.txt", "Pipfile", "pyproject.toml", "Cargo.toml"],
            "git_info": [".gitignore", ".git/config"]
        }
    
    def load_project_context(self) -> str:
        """Load all relevant project context"""
        print("DEBUG: Starting load_project_context...")
        context_parts = []
        
        # Load gemini.md files (highest priority)
        print("DEBUG: Loading gemini.md files...")
        gemini_context = self._load_gemini_md_files()
        print(f"DEBUG: Gemini.md loaded, size: {len(gemini_context) if gemini_context else 0}")
        if gemini_context:
            context_parts.append("=== PROJECT CONTEXT (gemini.md) ===\n" + gemini_context)
        
        # Load project configuration
        print("DEBUG: Loading project config...")
        project_config = self._load_project_config()
        print(f"DEBUG: Project config loaded, size: {len(project_config) if project_config else 0}")
        if project_config:
            context_parts.append("=== PROJECT CONFIGURATION ===\n" + project_config)
        
        # Load project structure overview
        print("DEBUG: Getting project structure...")
        structure = self._get_project_structure()
        print(f"DEBUG: Project structure loaded, size: {len(structure) if structure else 0}")
        if structure:
            context_parts.append("=== PROJECT STRUCTURE ===\n" + structure)
        
        # Load README and documentation
        print("DEBUG: Loading documentation...")
        docs_context = self._load_documentation()
        print(f"DEBUG: Documentation loaded, size: {len(docs_context) if docs_context else 0}")
        if docs_context:
            context_parts.append("=== DOCUMENTATION ===\n" + docs_context)
        
        # Load package/dependency information
        print("DEBUG: Loading package info...")
        package_info = self._load_package_info()
        print(f"DEBUG: Package info loaded, size: {len(package_info) if package_info else 0}")
        if package_info:
            context_parts.append("=== DEPENDENCIES & CONFIGURATION ===\n" + package_info)
        
        # Load git context
        print("DEBUG: Loading git context...")
        git_context = self._load_git_context()
        print(f"DEBUG: Git context loaded, size: {len(git_context) if git_context else 0}")
        if git_context:
            context_parts.append("=== GIT CONTEXT ===\n" + git_context)
        
        # Load memory
        print("DEBUG: Loading memory context...")
        memory_context = self._load_memory_context()
        print(f"DEBUG: Memory context loaded, size: {len(memory_context) if memory_context else 0}")
        if memory_context:
            context_parts.append("=== MEMORY ===\n" + memory_context)
        
        print("DEBUG: Context loading completed successfully")
        return "\n\n".join(context_parts)
    
    def _load_gemini_md_files(self) -> str:
        """Load gemini.md files from project hierarchy"""
        gemini_content = []
        
        # Look for gemini.md files from current directory up to project root
        current_path = Path.cwd()
        project_root = self.project_path
        
        while current_path >= project_root:
            for pattern in self.context_files["gemini_md"]:
                gemini_file = current_path / pattern
                if gemini_file.exists():
                    try:
                        with open(gemini_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                gemini_content.append(f"--- {gemini_file.relative_to(project_root)} ---\n{content}")
                    except IOError:
                        pass
            
            if current_path == project_root:
                break
            current_path = current_path.parent
        
        return "\n\n".join(gemini_content)
    
    def _load_project_config(self) -> str:
        """Load project configuration files"""
        config_content = []
        
        for pattern in self.context_files["project_config"]:
            config_file = self.project_path / pattern
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            config_content.append(f"--- {config_file.name} ---\n{content}")
                except IOError:
                    pass
        
        return "\n\n".join(config_content)
    
    def _get_project_structure(self) -> str:
        """Generate project structure overview"""
        structure_lines = []
        
        # Get important directories and files
        important_patterns = [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.go", "*.rs", "*.java",
            "*.md", "*.yml", "*.yaml", "*.json", "*.toml", "*.ini",
            "Dockerfile", "docker-compose.yml", "Makefile", "CMakeLists.txt"
        ]
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env', 'target']]
                
                level = root.replace(str(self.project_path), '').count(os.sep)
                if level > 3:  # Limit depth
                    continue
                
                indent = ' ' * 2 * level
                rel_path = Path(root).relative_to(self.project_path)
                structure_lines.append(f"{indent}{rel_path}/")
                
                # Add important files
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    if any(fnmatch.fnmatch(file, pattern) for pattern in important_patterns):
                        structure_lines.append(f"{subindent}{file}")
                
                if len(structure_lines) > 50:  # Limit output size
                    structure_lines.append("... (truncated)")
                    break
            
            return "\n".join(structure_lines)
        except Exception:
            return "Unable to generate project structure"
    
    def _load_documentation(self) -> str:
        """Load README and key documentation"""
        docs_content = []
        
        # Load README
        for pattern in self.context_files["readme"]:
            readme_file = self.project_path / pattern
            if readme_file.exists():
                try:
                    with open(readme_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # Truncate if too long
                            if len(content) > 3000:
                                content = content[:3000] + "\n... (truncated)"
                            docs_content.append(f"--- {readme_file.name} ---\n{content}")
                    break  # Only load first README found
                except IOError:
                    pass
        
        return "\n\n".join(docs_content)
    
    def _load_package_info(self) -> str:
        """Load package and dependency information"""
        package_content = []
        
        for pattern in self.context_files["package_info"]:
            package_file = self.project_path / pattern
            if package_file.exists():
                try:
                    with open(package_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            # For large files, extract key sections
                            if package_file.name == "package.json":
                                try:
                                    pkg_data = json.loads(content)
                                    key_sections = {
                                        "name": pkg_data.get("name"),
                                        "version": pkg_data.get("version"),
                                        "scripts": pkg_data.get("scripts", {}),
                                        "dependencies": pkg_data.get("dependencies", {}),
                                        "devDependencies": pkg_data.get("devDependencies", {})
                                    }
                                    content = json.dumps(key_sections, indent=2)
                                except json.JSONDecodeError:
                                    pass
                            
                            package_content.append(f"--- {package_file.name} ---\n{content}")
                except IOError:
                    pass
        
        return "\n\n".join(package_content)
    
    def _load_git_context(self) -> str:
        """Load git-related context"""
        git_content = []
        
        # Load .gitignore
        gitignore_file = self.project_path / ".gitignore"
        if gitignore_file.exists():
            try:
                with open(gitignore_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        git_content.append(f"--- .gitignore ---\n{content}")
            except IOError:
                pass
        
        # Add git status if available
        try:
            import git
            repo = git.Repo(self.project_path)
            
            # Get current branch and status
            current_branch = repo.active_branch.name
            untracked = repo.untracked_files[:10]  # Limit to 10 files
            modified = [item.a_path for item in repo.index.diff(None)][:10]
            
            status_info = f"Current branch: {current_branch}\n"
            if untracked:
                status_info += f"Untracked files: {', '.join(untracked)}\n"
            if modified:
                status_info += f"Modified files: {', '.join(modified)}\n"
            
            git_content.append(f"--- Git Status ---\n{status_info}")
        except:
            pass
        
        return "\n\n".join(git_content)
    
    def _load_memory_context(self) -> str:
        """Load relevant memory entries"""
        memory_content = []
        
        # Get project and user memory
        for scope in ["project", "user"]:
            memory = self.memory_system.get_all_memory(scope)
            if scope in memory and memory[scope]:
                scope_content = []
                for key, entry in memory[scope].items():
                    scope_content.append(f"{key}: {entry['content']}")
                
                if scope_content:
                    memory_content.append(f"--- {scope.title()} Memory ---\n" + "\n".join(scope_content))
        
        return "\n\n".join(memory_content)
    
    def add_context_file(self, file_path: str, priority: int = 1):
        """Add a specific file to context"""
        file_path = Path(file_path)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                entry = ContextEntry(
                    content=content,
                    source=str(file_path),
                    priority=priority,
                    scope="session"
                )
                
                self.context_cache[str(file_path)] = entry
            except IOError:
                pass
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of loaded context"""
        context = self.load_project_context()
        
        return {
            "project_path": str(self.project_path),
            "context_size": len(context),
            "memory_entries": len(self.memory_system.get_all_memory()),
            "cached_files": len(self.context_cache),
            "has_gemini_md": bool(self._load_gemini_md_files()),
            "has_readme": bool(self._load_documentation()),
            "has_package_info": bool(self._load_package_info())
        }
    
    def search_context(self, query: str) -> List[Dict]:
        """Search through all available context"""
        results = []
        
        # Search memory
        memory_results = self.memory_system.search_memory(query)
        results.extend([{**r, "source": "memory"} for r in memory_results])
        
        # Search project files
        context = self.load_project_context()
        if query.lower() in context.lower():
            results.append({
                "source": "project_context",
                "content": "Found in project context files",
                "match_preview": self._extract_context_preview(context, query)
            })
        
        return results
    
    def _extract_context_preview(self, content: str, query: str, context_size: int = 200) -> str:
        """Extract a preview around the search query"""
        query_pos = content.lower().find(query.lower())
        if query_pos == -1:
            return ""
        
        start = max(0, query_pos - context_size // 2)
        end = min(len(content), query_pos + context_size // 2)
        
        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        
        return preview

class WorkflowTemplates:
    """Pre-defined workflow templates for common development tasks"""
    
    def __init__(self, context_manager: GeminiContextManager):
        self.context_manager = context_manager
        
        self.templates = {
            "code_review": {
                "prompt": """Please review this code for:
1. Bugs and potential issues
2. Code quality and best practices
3. Performance optimizations
4. Security concerns
5. Maintainability improvements

First, understand the codebase structure and purpose, then provide detailed feedback.""",
                "tools": ["file_operations", "git_operations"],
                "auto_approve": ["file_operations"],
                "context_priority": ["current_files", "git_history", "project_structure"]
            },
            
            "feature_implementation": {
    "prompt": """I need to implement a new feature. Please:
1. Analyze the existing codebase to understand the architecture
2. Create a detailed implementation plan
3. Break down the work into manageable steps
4. Implement the feature following project conventions
5. Add appropriate tests
6. Update documentation if needed

Always ask for confirmation before making significant changes.""",
    "tools": ["file_operations", "bash_commands", "git_operations"],
    "auto_approve": ["file_operations"],  # ← CHANGED: Added file_operations
    "context_priority": ["project_structure", "dependencies", "existing_patterns"]
},
            
            "debug_assistance": {
                "prompt": """Help me debug this issue. Please:
1. Understand the problem by examining error logs and symptoms
2. Analyze the relevant code and recent changes
3. Check git history for related changes
4. Identify the root cause
5. Propose and implement fixes
6. Suggest preventive measures

Use all available tools to investigate thoroughly.""",
                "tools": ["file_operations", "bash_commands", "git_operations", "web_search"],
                "auto_approve": ["file_operations", "git_operations"],
                "context_priority": ["error_logs", "git_history", "related_files"]
            },
            
            "refactoring": {
    "prompt": """Help me refactor this code to improve:
1. Code organization and structure
2. Performance and efficiency
3. Readability and maintainability
4. Adherence to best practices
5. Test coverage

Please analyze the current state, propose improvements, and implement them carefully.""",
    "tools": ["file_operations", "bash_commands"],
    "auto_approve": ["file_operations"],  # ← CHANGED: Added file_operations
    "context_priority": ["target_code", "tests", "dependencies"]
},
            
            "documentation": {
                "prompt": """Help me improve the documentation for this project:
1. Review existing documentation for completeness and accuracy
2. Identify missing documentation
3. Create or update README, API docs, and code comments
4. Ensure documentation follows project standards
5. Add examples and usage instructions

Focus on making the project accessible to new contributors.""",
                "tools": ["file_operations", "web_search"],
                "auto_approve": ["file_operations"],
                "context_priority": ["existing_docs", "code_structure", "api_interfaces"]
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get a workflow template"""
        return self.templates.get(template_name, {})
    
    def list_templates(self) -> List[str]:
        """List available workflow templates"""
        return list(self.templates.keys())
    
    def apply_template(self, template_name: str, custom_prompt: str = "") -> Dict[str, Any]:
        """Apply a workflow template with optional custom prompt"""
        template = self.get_template(template_name)
        if not template:
            return {"error": f"Template not found: {template_name}"}
        
        # Combine template prompt with custom prompt
        full_prompt = template["prompt"]
        if custom_prompt:
            full_prompt += f"\n\nSpecific requirements:\n{custom_prompt}"
        
        # Load context based on template priorities
        context = self.context_manager.load_project_context()
        
        return {
            "prompt": full_prompt,
            "context": context,
            "tools": template["tools"],
            "auto_approve": template.get("auto_approve", []),
            "template_name": template_name
        }