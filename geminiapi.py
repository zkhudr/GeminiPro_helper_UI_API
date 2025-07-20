import os
import io
import json
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import google.generativeai as genai
from gemini_assistant import GeminiSession

class GeminiAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.session = None
        
    # ===== WEB UI INTERFACE METHODS =====
    # These are the methods called by the JavaScript in index.html
    
    def initialize_session(self):
        """Initialize the Gemini session - called by web UI"""
        try:
            print(f"🔧 Creating GeminiSession with API key: {self.api_key[:10]}...")
            self.session = GeminiSession(api_key=self.api_key)
            print("✅ GeminiSession created successfully!")
            
            return {
                "status": "success",
                "message": "Session initialized successfully"
            }
        except ValueError as ve:
            error_msg = f"API key error: {str(ve)}"
            print(f"❌ ValueError: {error_msg}")
            return {
                "status": "error", 
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Failed to initialize session: {str(e)}"
            print(f"❌ Exception: {error_msg}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return {
                "status": "error", 
                "message": error_msg
            }

    def send_message(self, message: str):
        """Send a message to Gemini"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Check if files are uploaded
            if self.session.uploaded_files:
                response = self.session.ask_with_files(message)
            else:
                response = self.session.ask(message)
            
            return {
                "status": "success",
                "response": response,
                "tokens": {
                    "input": self.session.total_input_tokens,
                    "output": self.session.total_output_tokens
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error sending message: {str(e)}"
            }
    
    def upload_files(self, file_paths: List[str]):
        """Upload files to the session"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            uploaded = self.session.upload_files(file_paths)
            
            # Handle case where upload_files returns None
            if uploaded is None:
                uploaded = []
                
            return {
                "status": "success",
                "count": len(uploaded),
                "message": f"Uploaded {len(uploaded)} files successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error uploading files: {str(e)}"
            }

    def list_uploaded_files(self):
        """List files from session metadata that still exist on Gemini servers."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Get all files currently on Gemini servers
            server_files = list(genai.list_files())
            server_file_names = {f.name for f in server_files}
            
            file_list = []
            expired_files = []
   
   # Check session metadata against server files
            for display_name, metadata in self.session.file_metadata.items():
                upload_name = metadata.get('upload_name')
                if upload_name and upload_name in server_file_names:
                    # File exists on server
                    server_file = next((f for f in server_files if f.name == upload_name), None)
                    if server_file:
                        file_info = {
                            "name": server_file.name,
                            "display_name": display_name,
                            "mime_type": metadata.get('mime_type', 'unknown'),
                            "size_bytes": getattr(server_file, 'size_bytes', 0),
                            "state": getattr(server_file, 'state', 'unknown')
                        }
                        file_list.append(file_info)
                else:
                    # File exists in metadata but not on server (expired)
                    expired_files.append(display_name)
            
            # Create appropriate message
            if len(file_list) == 0 and len(expired_files) == 0:
                message = "No files in this session"
            elif len(file_list) == 0 and len(expired_files) > 0:
                message = f"No files currently loaded. Session had {len(expired_files)} file(s) that have expired: {', '.join(expired_files)}"
            else:
                message = f"{len(file_list)} file(s) loaded"
            
            return {
                "status": "success",
                "files": file_list,
                "count": len(file_list),
                "expired_files": expired_files,
                "message": message
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error listing files: {str(e)}"
            }

    def delete_file(self, file_name: str):
        """Delete a file by its full name (e.g., 'files/abc-123')."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
                
            genai.delete_file(name=file_name)
            
            # Remove from local tracking
            for local_name, metadata in list(self.session.file_metadata.items()):
                if metadata['upload_name'] == file_name:
                    del self.session.file_metadata[local_name]
                    break
            
            # Remove from uploaded_files list
            self.session.uploaded_files = [f for f in self.session.uploaded_files if f.name != file_name]
            
            return {
                "status": "success",
                "message": f"Deleted: {file_name}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete {file_name}: {str(e)}"
            }

    def clear_files(self):
        """Delete all files owned by the user/project."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
                
            files = list(genai.list_files())
            if not files:
                return {
                    "status": "success",
                    "message": "No files to delete."
                }
            
            for f in files:
                genai.delete_file(f.name)
            
            # Clear local tracking
            self.session.uploaded_files = []
            self.session.file_metadata = {}
            
            return {
                "status": "success",
                "message": f"Deleted {len(files)} files"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error deleting all files: {str(e)}"
            }

    def clear_conversation(self):
        """Clear conversation history but keep uploaded files."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
                
            self.session.history = []
            return {
                "status": "success",
                "message": "Conversation history cleared."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error clearing conversation: {str(e)}"
            }

    def get_session_info(self):
        """Get information about the current session"""
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
            return {
                "status": "error",
                "message": f"Error getting session info: {str(e)}"
            }

    # ===== ORIGINAL METHODS FROM YOUR FILE =====
    # These preserve all your original functionality
    
    @property
    def uploaded_files(self):
        """Property to access uploaded files"""
        return self.session.uploaded_files if self.session else []
    
    @property 
    def file_metadata(self):
        """Property to access file metadata"""
        return self.session.file_metadata if self.session else {}

    def upload_pdf_from_url(self, url: str, display_name: Optional[str] = None) -> Optional[object]:
        """Upload a PDF directly from a URL using the Gemini File API."""
        try:
            print(f"📥 Downloading PDF from: {url}")
            
            # Follow redirects to handle OneDrive, Google Drive, etc.
            response = httpx.get(url, follow_redirects=True, timeout=30.0)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower():
                print(f"⚠️ Warning: Content-Type is not PDF: {content_type}")

            # Generate display name if not provided
            if not display_name:
                display_name = os.path.basename(url).split("?")[0]
                if not display_name.endswith(".pdf"):
                    display_name = f"downloaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            # Use in-memory bytes for upload
            pdf_bytes = io.BytesIO(response.content)

            # Upload using Gemini File API - Keep PDF MIME type only
            uploaded_file = genai.upload_file(
                pdf_bytes,
                mime_type="application/pdf",
                display_name=display_name
            )

            # Store metadata
            estimated_tokens = min(len(response.content) // 200, 1000 * 258)
            
            if self.session:
                self.session.file_metadata[display_name] = {
                    'path': url,
                    'mime_type': 'application/pdf',
                    'estimated_tokens': estimated_tokens,
                    'upload_name': uploaded_file.name,
                    'display_name': display_name
                }
                self.session.uploaded_files.append(uploaded_file)

            print(f"✅ SUCCESS: Uploaded PDF from URL: {display_name}")
            print(f"   Saved as: {uploaded_file.name}")
            print(f"   Estimated tokens: {estimated_tokens}")

            # Return format for web UI
            if hasattr(self, 'session') and self.session:
                return {
                    "status": "success",
                    "file": {
                        "name": uploaded_file.name,
                        "display_name": display_name
                    },
                    "message": f"Successfully uploaded PDF: {display_name}"
                }
            else:
                return uploaded_file

        except Exception as e:
            error_msg = f"❌ ERROR: Failed to upload PDF from URL {url}: {e}"
            print(error_msg)
            if hasattr(self, 'session') and self.session:
                return {"status": "error", "message": error_msg}
            return None

    def upload_multiple_pdfs_from_urls(self, urls: List[str]) -> List[object]:
        """Upload multiple PDFs from a list of URLs."""
        uploaded_files = []
        for i, url in enumerate(urls):
            display_name = f"url_pdf_{i+1}.pdf"
            uploaded = self.upload_pdf_from_url(url, display_name)
            if uploaded:
                uploaded_files.append(uploaded)
            else:
                print(f"⚠️ Skipped file {display_name} due to upload error.")
        return uploaded_files

    def _generate_usage_report(self, input_tokens: int, output_tokens: int) -> str:
        """Generate token usage report."""
        if not self.session:
            return ""
            
        return (
            f"\n--- Token Usage ---\n"
            f"Input tokens (this turn): {input_tokens}\n"
            f"Output tokens (this turn): {output_tokens}\n"
            f"Cumulative input tokens: {self.session.total_input_tokens}\n"
            f"Cumulative output tokens: {self.session.total_output_tokens}\n"
            f"Total tokens used: {self.session.total_input_tokens + self.session.total_output_tokens}\n"
            f"Files loaded: {len(self.session.uploaded_files)}\n"
            f"-------------------"
        )

    def delete_all_files(self):
        """Delete all files owned by the user/project."""
        try:
            files = list(genai.list_files())
            if not files:
                print("No files to delete.")
                return
            
            for f in files:
                self.delete_file(f.name)
            
            # Clear local tracking
            if self.session:
                self.session.uploaded_files = []
                self.session.file_metadata = {}
            
        except Exception as e:
            print(f"ERROR: Error deleting all files: {e}")

    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        if not self.session or not self.session.history:
            return "No conversation history."
        
        summary = f"Conversation Summary:\n"
        summary += f"- Total exchanges: {len(self.session.history) // 2}\n"
        summary += f"- Total tokens used: {self.session.total_input_tokens + self.session.total_output_tokens}\n"
        summary += f"- Files loaded: {len(self.session.uploaded_files)}\n"
        
        if self.session.file_metadata:
            summary += f"- File details:\n"
            for name, info in self.session.file_metadata.items():
                summary += f"  • {name} ({info['mime_type']}, ~{info['estimated_tokens']} tokens)\n"
        
        return summary

    def save_session(self, session_name: Optional[str] = None) -> str:
        """Save current session to a JSON file."""
        if not self.session:
            return "ERROR: No session to save"
            
        if not session_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"gemini_session_{timestamp}"
        
        # Create sessions directory if it doesn't exist
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        session_file = sessions_dir / f"{session_name}.json"
        
        # Prepare session data
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "model_name": self.session.model_name,
            "config": {
                "use_dynamic_tokens": self.session.use_dynamic_tokens,
                "max_total_tokens": self.session.max_total_tokens,
                "hard_cap": self.session.hard_cap,
                "truncate_output": self.session.truncate_output,
                "truncate_chars": self.session.truncate_chars,
                "add_short_hint": self.session.add_short_hint,
                "enable_streaming": self.session.enable_streaming
            },
            "history": self.session.history,
            "total_input_tokens": self.session.total_input_tokens,
            "total_output_tokens": self.session.total_output_tokens,
            "file_metadata": self.session.file_metadata,
            "file_paths": [],  # Store full paths separately
            "gemini_files": []  # We'll store Gemini file references
        }
        
        # Extract and store full file paths
        for name, metadata in self.session.file_metadata.items():
            original_path = metadata.get('path', '')
            if original_path and os.path.exists(original_path):
                session_data["file_paths"].append({
                    "display_name": name,
                    "path": original_path,
                    "mime_type": metadata.get('mime_type', 'text/plain')
                })
        
        # Add Gemini file information (but files themselves stay on Gemini servers)
        for uploaded_file in self.session.uploaded_files:
            session_data["gemini_files"].append({
                "name": uploaded_file.name,
                "display_name": getattr(uploaded_file, 'display_name', 'Unknown'),
                "mime_type": getattr(uploaded_file, 'mime_type', 'unknown')
            })
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            print(f"SUCCESS: Session saved as {session_file}")
            print(f"   Conversation turns: {len(self.session.history) // 2}")
            print(f"   Total tokens: {self.session.total_input_tokens + self.session.total_output_tokens}")
            print(f"   Files tracked: {len(self.session.file_metadata)}")
            print(f"   File paths saved: {len(session_data['file_paths'])}")
            return str(session_file)
            
        except Exception as e:
            error_message = f"ERROR: Failed to save session: {e}"
            print(error_message)
            return error_message

    def list_saved_sessions(self) -> List[str]:
        """List all saved session files."""
        sessions_dir = Path("sessions")
        if not sessions_dir.exists():
            print("No sessions directory found.")
            return []
        
        session_files = list(sessions_dir.glob("*.json"))
        if not session_files:
            print("No saved sessions found.")
            return []
        
        print("\nSaved Sessions:")
        sessions = []
        for session_file in sorted(session_files):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                timestamp = session_data.get('timestamp', 'Unknown')
                turns = len(session_data.get('history', [])) // 2
                tokens = session_data.get('total_input_tokens', 0) + session_data.get('total_output_tokens', 0)
                files = len(session_data.get('file_metadata', {}))
                
                print(f"- {session_file.stem}")
                print(f"  Created: {timestamp}")
                print(f"  Turns: {turns}, Tokens: {tokens}, Files: {files}")
                print()
                
                sessions.append(session_file.stem)
                
            except Exception as e:
                print(f"- {session_file.stem} (Error reading: {e})")
        
        return sessions

    def load_session(self, session_file: str) -> bool:
        """Load a previously saved session."""
        try:
            session_path = Path(session_file)
            if not session_path.exists():
                # Try looking in sessions directory
                sessions_path = Path("sessions") / f"{session_file}.json"
                if sessions_path.exists():
                    session_path = sessions_path
                else:
                    print(f"ERROR: Session file not found: {session_file}")
                    return False
            
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Initialize session if not exists
            if not self.session:
                self.session = GeminiSession()
            
            # Restore configuration
            config = session_data.get("config", {})
            self.session.model_name = session_data.get("model_name", self.session.model_name)
            self.session.use_dynamic_tokens = config.get("use_dynamic_tokens", self.session.use_dynamic_tokens)
            self.session.max_total_tokens = config.get("max_total_tokens", self.session.max_total_tokens)
            self.session.hard_cap = config.get("hard_cap", self.session.hard_cap)
            self.session.truncate_output = config.get("truncate_output", self.session.truncate_output)
            self.session.truncate_chars = config.get("truncate_chars", self.session.truncate_chars)
            self.session.add_short_hint = config.get("add_short_hint", self.session.add_short_hint)
            self.session.enable_streaming = config.get("enable_streaming", self.session.enable_streaming)
            
            # Restore conversation history and tokens
            self.session.history = session_data.get("history", [])
            self.session.total_input_tokens = session_data.get("total_input_tokens", 0)
            self.session.total_output_tokens = session_data.get("total_output_tokens", 0)
            self.session.file_metadata = session_data.get("file_metadata", {})
            
            # Note: Gemini files are NOT automatically restored since they may have expired
            # User will need to re-upload files if they want to continue with file-based conversations
            self.session.uploaded_files = []
            
            print(f"SUCCESS: Session loaded from {session_path}")
            print(f"   Session from: {session_data.get('timestamp', 'Unknown')}")
            print(f"   Conversation turns: {len(self.session.history) // 2}")
            print(f"   Total tokens: {self.session.total_input_tokens + self.session.total_output_tokens}")
            print(f"   File metadata restored: {len(self.session.file_metadata)}")
            
            if session_data.get("gemini_files"):
                print("   NOTE: Files were tracked in this session but need to be re-uploaded.")
                print("   Previous files:")
                for file_info in session_data["gemini_files"]:
                    print(f"     - {file_info.get('display_name', 'Unknown')} ({file_info.get('mime_type', 'unknown')})")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to load session: {e}")
            return False

    def toggle_streaming(self):
        """Toggle streaming mode on/off."""
        if not self.session:
            return False
            
        self.session.enable_streaming = not self.session.enable_streaming
        status = "enabled" if self.session.enable_streaming else "disabled"
        print(f"Streaming {status}.")
        return self.session.enable_streaming

    def analyze_code_files(self, analysis_prompt: str) -> str:
        """Specialized method for analyzing code files (.py, .json, etc.)."""
        if not self.session or not self.session.uploaded_files:
            return "ERROR: No files uploaded. Upload code files first."
        
        code_analysis_prompt = f"""
        Analyze the uploaded code and configuration files. {analysis_prompt}
        
        Please provide:
        1. Code review and analysis
        2. Potential improvements
        3. Best practices recommendations
        4. Any issues or bugs found
        5. Suggested refactoring if needed
        
        Focus on code quality, efficiency, and maintainability.
        """
        
        return self.session.ask_with_files(code_analysis_prompt)

    def compare_documents(self, prompt: str) -> str:
        """Specialized method for comparing multiple documents."""
        if not self.session or len(self.session.uploaded_files) < 2:
            return "ERROR: Need at least 2 files uploaded to compare documents."
        
        comparison_prompt = f"""
        Compare the uploaded documents and {prompt}
        
        Please provide a structured comparison focusing on:
        1. Key differences between the documents
        2. Common themes or elements
        3. Specific details requested in the prompt
        
        Format your response clearly with headings and bullet points where appropriate.
        """
        
        return self.session.ask_with_files(comparison_prompt)

    def update_session_settings(self, settings):
        """Update session configuration settings"""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Update session settings
            self.session.model_name = settings.get('model_name', self.session.model_name)
            self.session.use_dynamic_tokens = settings.get('use_dynamic_tokens', self.session.use_dynamic_tokens)
            self.session.max_total_tokens = settings.get('max_total_tokens', self.session.max_total_tokens)
            self.session.hard_cap = settings.get('hard_cap', self.session.hard_cap)
            self.session.truncate_output = settings.get('truncate_output', self.session.truncate_output)
            self.session.truncate_chars = settings.get('truncate_chars', self.session.truncate_chars)
            self.session.add_short_hint = settings.get('add_short_hint', self.session.add_short_hint)
            self.session.enable_streaming = settings.get('enable_streaming', self.session.enable_streaming)
            
            return {"status": "success", "message": "Settings updated successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Error updating settings: {str(e)}"}

    def delete_saved_session(self, session_name: str) -> bool:
        """Delete a saved session file."""
        try:
            session_path = Path("sessions") / f"{session_name}.json"
            if not session_path.exists():
                print(f"ERROR: Session file not found: {session_name}")
                return False
            
            session_path.unlink()  # Delete the file
            print(f"SUCCESS: Deleted session: {session_name}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to delete session {session_name}: {e}")
            return False

    def get_session_file_paths(self):
        """Get file paths from current session for re-upload."""
        if not self.session:
            return []
        
        file_paths = []
        for name, metadata in self.session.file_metadata.items():
            original_path = metadata.get('path', '')
            if original_path:
                exists = os.path.exists(original_path)
                file_paths.append({
                    "display_name": name,
                    "path": original_path,
                    "exists": exists,
                    "mime_type": metadata.get('mime_type', 'text/plain')
                })
        
        return file_paths

    def reupload_files_from_paths(self, selected_paths):
        """Re-upload files from their original paths."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            uploaded = self.session.upload_files(selected_paths)
            
            return {
                "status": "success",
                "count": len(uploaded),
                "message": f"Re-uploaded {len(uploaded)} files successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error re-uploading files: {str(e)}"
            }

    def upload_file_content(self, filename, content, size):
        """Upload file content directly to Gemini."""
        try:
            if not self.session:
                return {"status": "error", "message": "Session not initialized"}
            
            # Create a temporary file-like object
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