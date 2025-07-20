# enhanced_gemini_api.py - Enhanced Gemini API with Agentic Features

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import google.generativeai as genai
from gemini_assistant import GeminiSession
from gemini_tools import GeminiToolSystem, ToolExecutionResult
from gemini_context import GeminiContextManager, GeminiMemorySystem, WorkflowTemplates
from geminiapi import GeminiAPI
import datetime


class EnhancedGeminiAPI(GeminiAPI):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.session = None
        self.tool_system = None
        self.context_manager = None
        self.memory_system = None
        self.workflow_templates = None
        self.auto_approve_mode = False
        self.current_project_path = os.getcwd()
        
    def initialize_session(self, project_path: str = None):
        """Initialize enhanced session with agentic capabilities"""
        try:
            print("DEBUG: Starting enhanced session initialization...")
            
            if project_path:
                self.current_project_path = project_path
                os.chdir(project_path)
            print(f"DEBUG: Project path set to: {self.current_project_path}")
            
            # Initialize core session
            print("DEBUG: Creating GeminiSession...")
            self.session = GeminiSession(api_key=self.api_key)
            print("DEBUG: GeminiSession created successfully")
            
            # Initialize tool system
            print("DEBUG: Creating GeminiToolSystem...")
            self.tool_system = GeminiToolSystem(self.session)
            print("DEBUG: GeminiToolSystem created successfully")
            
            # Initialize context management
            print("DEBUG: Creating GeminiContextManager...")
            self.context_manager = GeminiContextManager(self.current_project_path)
            print("DEBUG: GeminiContextManager created successfully")
            
            self.memory_system = self.context_manager.memory_system
            
            # Initialize workflow templates
            print("DEBUG: Creating WorkflowTemplates...")
            self.workflow_templates = WorkflowTemplates(self.context_manager)
            print("DEBUG: WorkflowTemplates created successfully")
            
            # Load project context
            print("DEBUG: Loading project context...")
            project_context = self.context_manager.load_project_context()
            print(f"DEBUG: Project context loaded, size: {len(project_context) if project_context else 0}")
            
            if project_context:
                self.session.system_context = project_context
            
            print("DEBUG: Enhanced session initialization completed successfully")
            
            return {
                "status": "success",
                "message": "Enhanced session initialized successfully",
                "features": {
                    "tools_available": list(self.tool_system.tools.keys()),
                    "context_loaded": bool(project_context),
                    "project_path": self.current_project_path,
                    "workflow_templates": self.workflow_templates.list_templates()
                }
            }
        except Exception as e:
            print(f"DEBUG: Error in enhanced session initialization: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Failed to initialize enhanced session: {str(e)}"
            }
            
    def upload_file_content(self, filename, content, size):
        """Upload file content directly to Gemini"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            import tempfile
            import os
            
            # Create temp file with original extension
            file_ext = os.path.splitext(filename)[1]
            with tempfile.NamedTemporaryFile(mode='w', suffix=file_ext, delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                # Upload the temp file
                uploaded = self.session.upload_files([temp_path])
                
                if uploaded and len(uploaded) > 0:
                    # Update metadata with original filename
                    for name, metadata in self.session.file_metadata.items():
                        if metadata.get('path') == temp_path:
                            # Update to use original filename
                            new_metadata = metadata.copy()
                            new_metadata['display_name'] = filename
                            new_metadata['path'] = f"browser_upload_{filename}"
                            
                            # Remove old entry and add new one
                            del self.session.file_metadata[name]
                            self.session.file_metadata[filename] = new_metadata
                            break
                    
                    return {
                        "status": "success",
                        "message": f"Successfully uploaded {filename}"
                    }
                else:
                    return {
                        "status": "error", 
                        "message": f"Failed to upload {filename}"
                    }
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error uploading {filename}: {str(e)}"
            }
    
     
    def get_session_info(self):
        """Get basic session info for backward compatibility"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            return {
                "status": "success", 
                "info": {
                    "model_name": self.session.model_name,
                    "conversation_turns": len(self.session.history) // 2,
                    "total_input_tokens": self.session.total_input_tokens,
                    "total_output_tokens": self.session.total_output_tokens,
                    "files_count": len(self.session.uploaded_files)
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"Error getting session info: {str(e)}"}
    

    
    def clear_conversation(self):
        """Enhanced conversation clearing that preserves context and memory"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            self.session.history = []
            
            # Preserve context and memory (unlike basic clear)
            return {
                "status": "success",
                "message": "Conversation history cleared (context and memory preserved)"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing conversation: {str(e)}"
            }
        
    
    def send_message(self, message: str, use_tools: bool = True, workflow_template: str = None):
        """Enhanced message sending using a two-step, multi-example tool router."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}

            if message.startswith(('#', '/')):
                return self._handle_slash_command(message) if message.startswith('/') else self._handle_remember_command(message)

            if workflow_template:
                template_result = self.workflow_templates.apply_template(workflow_template, message)
                if "error" in template_result:
                    return {"status": "error", "message": template_result["error"]}
                message = template_result["prompt"]
                self.tool_system.set_auto_approve(template_result.get("auto_approve", []))

            final_response = ""
            tool_results = []

            if use_tools:
                # Get current time to help the model with time-related queries.
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # A more readable, multi-example, f-string prompt.
                router_prompt = f"""You are a router agent. Your only function is to determine if a user's request can be handled by the available tools.
You MUST respond in one of two ways:
1. A `TOOL_USE:` JSON block containing ONLY valid, syntactically correct JSON.
2. The single word `PASS` if no tool can be used.
DO NOT provide ANY other text, explanations, conversational filler, or separators like '---'. Your entire response must be ONLY the JSON object or the word PASS.

The current date and time is: {current_time}

---
## Good Example 1 (Listing Files):
USER REQUEST: what are the files in my directory
TOOL_USE: {{
    "tool": "file_operations",
    "parameters": {{ "operation": "list_directory", "path": "." }}
}}
---
## Good Example 2 (Writing a File):
USER REQUEST: Create a file named 'report.txt' with the content 'Final report.'
TOOL_USE: {{
    "tool": "file_operations",
    "parameters": {{ "operation": "write", "path": "report.txt", "content": "Final report." }}
}}
---
## AVAILABLE TOOLS ##
{self.tool_system.get_tool_usage_prompt()}
---
## USER REQUEST ##
{self._enhance_message_with_context(message)}
"""
                router_response = self.session.ask(router_prompt, is_raw_prompt=True).strip()

                if "TOOL_USE" in router_response:
                    final_response, tool_results = self._process_tool_usage(router_response)
                elif router_response.upper() == "PASS":
                    final_response = self.session.ask(message)
                else:
                    final_response = router_response
                    self.session.history.append({"role": "user", "text": message})
                    self.session.history.append({"role": "assistant", "text": final_response})
            else:
                final_response = self.session.ask(message)

            return {
                "status": "success", "response": final_response, "tool_results": tool_results,
                "tokens": { "input": self.session.total_input_tokens, "output": self.session.total_output_tokens }
            }
        except Exception as e:
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": f"Error sending message: {str(e)}"}
        
    def _enhance_message_with_context(self, message: str) -> str:
        """Enhance message with a note about project context if applicable."""
        enhanced_parts = [message]
        
        project_keywords = ["file", "code", "project", "implement", "fix", "bug", "feature", "test"]

        # 1. Check if the context manager exists BEFORE using it to prevent errors.
        if self.context_manager and any(keyword in message.lower() for keyword in project_keywords):
            context_summary = self.context_manager.get_context_summary()
            
            # Use .get() for safer dictionary access
            if context_summary.get("has_gemini_md") or context_summary.get("has_readme"):
                # 2. Provide a more descriptive note for the AI and user.
                enhanced_parts.append("\n[System Note: Project context from files like README.md has been loaded automatically.]")
        
        return "\n".join(enhanced_parts)
        
    def _process_tool_usage(self, response: str) -> Tuple[str, List[Dict]]:
        tool_results = []
        processed_response = response
        
        # --- THE FINAL FIX: A greedy regex to capture the entire JSON object ---
        tool_pattern = r'TOOL_USE:\s*(?:```(?:json)?\s*)?(\{.*\})(?:\s*```)?'
        match = re.search(tool_pattern, response, re.MULTILINE | re.DOTALL)
        
        if match:
            json_content = next((g for g in match.groups() if g), None)
            
            if json_content:
                try:
                    # Clean the string of any invalid whitespace characters
                    cleaned_json = json_content.replace('\u00A0', ' ')
                    
                    tool_request = json.loads(cleaned_json)
                    tool_name = tool_request.get("tool")
                    parameters = tool_request.get("parameters", {})
                    
                    result = self.tool_system.execute_tool(tool_name, parameters)
                    tool_results.append({
                        "tool": tool_name, "parameters": parameters,
                        "result": { "success": result.success, "output": result.output, "error": result.error, "metadata": result.metadata }
                    })
                    
                    result_text = f"\n[Tool: {tool_name}]\n"
                    output_preview = (result.output[:500] + '...') if len(result.output) > 500 else result.output
                    result_text += f"✅ Success:\n```\n{output_preview}\n```" if result.success else f"❌ Error: {result.error}"
                    
                    processed_response = processed_response.replace(match.group(0), result_text)

                except json.JSONDecodeError as e:
                    # This block should no longer be hit for this error
                    error_text = f"\n[Tool Error: Malformed JSON]\n<b>Error:</b> {str(e)}"
                    processed_response = processed_response.replace(match.group(0), error_text)
                
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    error_text = f"\n[Tool Error: Failed to execute tool. Reason: {str(e)}]"
                    processed_response = processed_response.replace(match.group(0), error_text)
        
        return processed_response, tool_results
        
    def _handle_remember_command(self, message: str) -> Dict:
        """Handle #remember commands"""
        try:
            # Parse remember command: #remember key=value scope=session
            content = message[9:].strip()  # Remove '#remember '
            
            # Extract key and content
            if '=' in content:
                key, value = content.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Check for scope specification
                scope = "session"
                if ' scope=' in value:
                    value, scope_part = value.rsplit(' scope=', 1)
                    scope = scope_part.strip()
                
                self.memory_system.remember(key, value, scope)
                return {
                    "status": "success",
                    "response": f"✅ Remembered '{key}' in {scope} scope",
                    "tokens": {"input": 0, "output": 0}
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid remember format. Use: #remember key=content"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in remember command: {str(e)}"
            }
    
    def _handle_slash_command(self, message: str) -> Dict:
        """Handle slash commands"""
        try:
            command_parts = message[1:].split()
            command = command_parts[0].lower()
            args = command_parts[1:] if len(command_parts) > 1 else []
            
            if command == "tools":
                tools_info = self.tool_system.get_available_tools()
                return {
                    "status": "success",
                    "response": f"Available tools:\n{json.dumps(tools_info, indent=2)}",
                    "tokens": {"input": 0, "output": 0}
                }
            
            elif command == "memory":
                if args and args[0] == "search":
                    query = " ".join(args[1:]) if len(args) > 1 else ""
                    results = self.memory_system.search_memory(query)
                    return {
                        "status": "success",
                        "response": f"Memory search results:\n{json.dumps(results, indent=2)}",
                        "tokens": {"input": 0, "output": 0}
                    }
                else:
                    all_memory = self.memory_system.get_all_memory()
                    return {
                        "status": "success",
                        "response": f"All memory:\n{json.dumps(all_memory, indent=2)}",
                        "tokens": {"input": 0, "output": 0}
                    }
            
            elif command == "context":
                summary = self.context_manager.get_context_summary()
                return {
                    "status": "success",
                    "response": f"Context summary:\n{json.dumps(summary, indent=2)}",
                    "tokens": {"input": 0, "output": 0}
                }
            
            elif command == "workflows":
                templates = self.workflow_templates.list_templates()
                return {
                    "status": "success",
                    "response": f"Available workflow templates:\n{', '.join(templates)}",
                    "tokens": {"input": 0, "output": 0}
                }
            
            elif command == "auto":
                if args and args[0] == "on":
                    self.auto_approve_mode = True
                    return {
                        "status": "success",
                        "response": "✅ Auto-approve mode enabled for safe tools",
                        "tokens": {"input": 0, "output": 0}
                    }
                elif args and args[0] == "off":
                    self.auto_approve_mode = False
                    return {
                        "status": "success",
                        "response": "✅ Auto-approve mode disabled",
                        "tokens": {"input": 0, "output": 0}
                    }
                else:
                    status = "enabled" if self.auto_approve_mode else "disabled"
                    return {
                        "status": "success",
                        "response": f"Auto-approve mode is {status}",
                        "tokens": {"input": 0, "output": 0}
                    }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown command: {command}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in slash command: {str(e)}"
            }
    
    def execute_tool_directly(self, tool_name: str, parameters: Dict[str, Any]) -> Dict:
        """Execute a tool directly via API"""
        try:
            if not self.tool_system:
                return {"status": "error", "message": "Tool system not initialized"}
            
            result = self.tool_system.execute_tool(tool_name, parameters)
            return {
                "status": "success" if result.success else "error",
                "result": {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "metadata": result.metadata
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing tool: {str(e)}"
            }
    
    def get_project_analysis(self) -> Dict:
        """Get comprehensive project analysis"""
        try:
            if not self.context_manager:
                return {"status": "error", "message": "Context manager not initialized"}
            
            # Get project structure analysis
            analysis = {
                "project_summary": self.context_manager.get_context_summary(),
                "available_tools": list(self.tool_system.tools.keys()),
                "memory_entries": len(self.memory_system.get_all_memory()),
                "workflow_templates": self.workflow_templates.list_templates()
            }
            
            # Analyze project type and suggest workflows
            project_context = self.context_manager.load_project_context()
            suggestions = self._analyze_project_and_suggest_workflows(project_context)
            analysis["suggestions"] = suggestions
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing project: {str(e)}"
            }
    
    def _analyze_project_and_suggest_workflows(self, context: str) -> Dict[str, List[str]]:
        """Analyze project context and suggest relevant workflows"""
        suggestions = {
            "immediate_actions": [],
            "recommended_workflows": [],
            "tools_to_configure": []
        }
        
        context_lower = context.lower()
        
        # Suggest immediate actions based on project state
        if "todo" in context_lower or "fixme" in context_lower:
            suggestions["immediate_actions"].append("Review TODO/FIXME comments")
        
        if "test" not in context_lower and any(ext in context_lower for ext in [".py", ".js", ".ts"]):
            suggestions["immediate_actions"].append("Consider adding tests")
        
        if "readme" not in context_lower:
            suggestions["immediate_actions"].append("Create or improve README documentation")
        
        # Recommend workflows based on project type
        if any(lang in context_lower for lang in ["python", ".py", "requirements.txt"]):
            suggestions["recommended_workflows"].extend(["code_review", "refactoring"])
        
        if any(js in context_lower for js in ["javascript", ".js", ".ts", "package.json"]):
            suggestions["recommended_workflows"].extend(["feature_implementation", "debug_assistance"])
        
        if "bug" in context_lower or "error" in context_lower:
            suggestions["recommended_workflows"].append("debug_assistance")
        
        # Suggest tools to configure
        if "git" in context_lower:
            suggestions["tools_to_configure"].append("git_operations")
        
        if any(web in context_lower for web in ["http", "api", "web"]):
            suggestions["tools_to_configure"].append("web_search")
        
        return suggestions
    
    def apply_workflow(self, template_name: str, custom_prompt: str = "") -> Dict:
        """Apply a workflow template"""
        try:
            if not self.workflow_templates:
                return {"status": "error", "message": "Workflow templates not initialized"}
            
            template_result = self.workflow_templates.apply_template(template_name, custom_prompt)
            if "error" in template_result:
                return {"status": "error", "message": template_result["error"]}
            
            return {
                "status": "success",
                "workflow": template_result,
                "message": f"Applied workflow template: {template_name}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error applying workflow: {str(e)}"
            }
    
    def set_project_path(self, project_path: str) -> Dict:
        """Change project path and reload context"""
        try:
            if not os.path.exists(project_path):
                return {"status": "error", "message": f"Path does not exist: {project_path}"}
            
            self.current_project_path = project_path
            os.chdir(project_path)
            
            # Reinitialize context manager
            self.context_manager = GeminiContextManager(self.current_project_path)
            self.memory_system = self.context_manager.memory_system
            self.workflow_templates = WorkflowTemplates(self.context_manager)
            
            # Reload project context
            project_context = self.context_manager.load_project_context()
            if self.session:
                self.session.system_context = project_context
            
            return {
                "status": "success",
                "message": f"Project path changed to: {project_path}",
                "context_summary": self.context_manager.get_context_summary()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error changing project path: {str(e)}"
            }
    
    def get_enhanced_session_info(self) -> Dict:
        """Get comprehensive session information"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            base_info = {
                "model_name": self.session.model_name,
                "conversation_turns": len(self.session.history) // 2,
                "total_input_tokens": self.session.total_input_tokens,
                "total_output_tokens": self.session.total_output_tokens,
                "files_count": len(self.session.uploaded_files)
            }
            
            # Add enhanced information
            enhanced_info = {
                **base_info,
                "project_path": self.current_project_path,
                "tools_available": list(self.tool_system.tools.keys()) if self.tool_system else [],
                "auto_approve_mode": self.auto_approve_mode,
                "context_loaded": bool(self.context_manager and self.context_manager.get_context_summary()["context_size"] > 0),
                "memory_entries": len(self.memory_system.get_all_memory()) if self.memory_system else 0,
                "workflow_templates": self.workflow_templates.list_templates() if self.workflow_templates else []
            }
            
            return {
                "status": "success",
                "info": enhanced_info
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting session info: {str(e)}"
            }
    
    # Inherit and enhance original methods
    def upload_files(self, file_paths: List[str]):
        """Enhanced file upload with automatic context integration"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Upload files using original method
            uploaded = self.session.upload_files(file_paths)
            
            # Add uploaded files to context automatically
            if self.context_manager and uploaded:
                for file_path in file_paths:
                    self.context_manager.add_context_file(file_path)
            
            return {
                "status": "success",
                "count": len(uploaded) if uploaded else 0,
                "message": f"Uploaded {len(uploaded) if uploaded else 0} files successfully",
                "context_updated": bool(self.context_manager)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error uploading files: {str(e)}"
            }

    
    def save_enhanced_session(self, session_name: str = None) -> Dict:
        """Save session with enhanced features"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Save using original method
            result = self.save_session(session_name)
            
            # Additionally save enhanced state
            if session_name:
                enhanced_state = {
                    "auto_approve_mode": self.auto_approve_mode,
                    "project_path": self.current_project_path,
                    "tool_permissions": {
                        "auto_approve": list(self.tool_system.auto_approve_tools) if self.tool_system else [],
                        "blocked": list(self.tool_system.blocked_tools) if self.tool_system else []
                    }
                }
                
                # Save enhanced state
                enhanced_file = Path("sessions") / f"{session_name}_enhanced.json"
                with open(enhanced_file, 'w') as f:
                    json.dump(enhanced_state, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Enhanced session saved: {result}",
                "features_saved": ["context", "memory", "tool_permissions", "project_settings"]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error saving enhanced session: {str(e)}"
            }
    
    def load_enhanced_session(self, session_file: str) -> Dict:
        """Load session with enhanced features"""
        try:
            # Load using original method
            success = self.load_session(session_file)
            if not success:
                return {"status": "error", "message": "Failed to load base session"}
            
            # Load enhanced state if available
            session_name = Path(session_file).stem
            enhanced_file = Path("sessions") / f"{session_name}_enhanced.json"
            
            if enhanced_file.exists():
                with open(enhanced_file, 'r') as f:
                    enhanced_state = json.load(f)
                
                # Restore enhanced settings
                self.auto_approve_mode = enhanced_state.get("auto_approve_mode", False)
                project_path = enhanced_state.get("project_path")
                
                if project_path and os.path.exists(project_path):
                    self.set_project_path(project_path)
                
                # Restore tool permissions
                tool_permissions = enhanced_state.get("tool_permissions", {})
                if self.tool_system:
                    self.tool_system.set_auto_approve(tool_permissions.get("auto_approve", []))
                    self.tool_system.block_tools(tool_permissions.get("blocked", []))
            
            return {
                "status": "success",
                "message": f"Enhanced session loaded: {session_file}",
                "features_restored": ["context", "memory", "tool_permissions", "project_settings"]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error loading enhanced session: {str(e)}"
            }
