# enhanced_ui_web.py - Enhanced Web Handler with Agentic Features

import os
import webbrowser
import threading
import traceback
import tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
from dotenv import load_dotenv
from enhanced_gemini_api import EnhancedGeminiAPI

class EnhancedGeminiWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, api=None, **kwargs):
        self.api = api
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Handle API GET requests
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # Handle static files (HTML, CSS, JS)
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404)
    
    def handle_api_request(self):
        try:
            print(f"🔍 API Request: {self.command} {self.path}")
            
            # Enhanced session initialization
            if self.path == '/api/initialize_enhanced_session':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    project_path = data.get('project_path')
                    print(f"Initializing enhanced session with project: {project_path}")
                    response = self.api.initialize_session(project_path)
                else:
                    response = self.api.initialize_session()
                print(f"Enhanced session response: {response}")
                self.send_json_response(response)
                
            # Enhanced message sending
            elif self.path == '/api/send_message_enhanced':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    message = data['message']
                    use_tools = data.get('use_tools', True)
                    workflow_template = data.get('workflow_template')
                    print(f"Sending enhanced message (tools: {use_tools}): {message[:50]}...")
                    response = self.api.send_message(message, use_tools, workflow_template)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Tool execution
            elif self.path == '/api/execute_tool':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    tool_name = data['tool_name']
                    parameters = data['parameters']
                    print(f"🔧 Executing tool: {tool_name} with {parameters}")
                    response = self.api.execute_tool_directly(tool_name, parameters)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Get tool help
            elif self.path == '/api/get_tool_help':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    tool_name = data['tool_name']
                    
                    if self.api.tool_system and tool_name in self.api.tool_system.tools:
                        help_text = self.api.tool_system.tools[tool_name].get_help()
                        response = {"status": "success", "help": help_text}
                    else:
                        response = {"status": "error", "message": f"Tool not found: {tool_name}"}
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Memory operations
            elif self.path == '/api/search_memory':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    query = data['query']
                    print(f"Searching memory for: {query}")
                    
                    if self.api.memory_system:
                        results = self.api.memory_system.search_memory(query)
                        response = {"status": "success", "results": results}
                    else:
                        response = {"status": "error", "message": "Memory system not initialized"}
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Context operations
            elif self.path == '/api/get_project_analysis':
                print("🔍 Getting project analysis...")
                response = self.api.get_project_analysis()
                self.send_json_response(response)
            
            # Workflow operations
            elif self.path == '/api/apply_workflow':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    template_name = data['template_name']
                    custom_prompt = data.get('custom_prompt', '')
                    print(f"Applying workflow: {template_name}")
                    response = self.api.apply_workflow(template_name, custom_prompt)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Project path operations
            elif self.path == '/api/set_project_path':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    project_path = data['project_path']
                    print(f"Setting project path: {project_path}")
                    response = self.api.set_project_path(project_path)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Auto-approve settings
            elif self.path == '/api/set_auto_approve':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    enabled = data['enabled']
                    
                    if self.api.tool_system:
                        if enabled:
                            safe_tools = [name for name, tool in self.api.tool_system.tools.items() 
                                        if tool.safety_level == "safe"]
                            self.api.tool_system.set_auto_approve(safe_tools)
                        else:
                            self.api.tool_system.auto_approve_tools.clear()
                        
                        self.api.auto_approve_mode = enabled
                        response = {"status": "success", "message": f"Auto-approve {'enabled' if enabled else 'disabled'}"}
                    else:
                        response = {"status": "error", "message": "Tool system not initialized"}
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Enhanced file uploads
            elif self.path == '/api/upload_files_enhanced':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    files = data['files']
                    
                    print(f"📁 Enhanced file upload: {len(files)} files")
                    
                    # Create temporary files and upload
                    temp_paths = []
                    try:
                        for file_data in files:
                            # Create temp file
                            with tempfile.NamedTemporaryFile(mode='w', suffix=f"_{file_data['name']}", 
                                                           delete=False, encoding='utf-8') as temp_file:
                                temp_file.write(file_data['content'])
                                temp_paths.append(temp_file.name)
                        
                        # Upload files
                        response = self.api.upload_files(temp_paths)
                        
                        # Update file metadata with original names
                        if response['status'] == 'success' and self.api.session:
                            for i, file_data in enumerate(files):
                                if i < len(temp_paths):
                                    # Update metadata to use original filename
                                    original_name = file_data['name']
                                    temp_path = temp_paths[i]
                                    
                                    # Find and update metadata
                                    for name, metadata in list(self.api.session.file_metadata.items()):
                                        if metadata.get('path') == temp_path:
                                            new_metadata = metadata.copy()
                                            new_metadata['display_name'] = original_name
                                            new_metadata['path'] = f"browser_upload_{original_name}"
                                            
                                            del self.api.session.file_metadata[name]
                                            self.api.session.file_metadata[original_name] = new_metadata
                                            break
                        
                        self.send_json_response(response)
                        
                    finally:
                        # Clean up temp files
                        for temp_path in temp_paths:
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                else:
                    self.send_error(405)
            
            # Enhanced session management
            elif self.path == '/api/save_enhanced_session':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    session_name = data.get('session_name')
                    print(f"Saving enhanced session: {session_name}")
                    response = self.api.save_enhanced_session(session_name)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            elif self.path == '/api/load_enhanced_session':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    session_file = data.get('session_file')
                    print(f"Loading enhanced session: {session_file}")
                    response = self.api.load_enhanced_session(session_file)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Enhanced session info
            elif self.path == '/api/get_enhanced_session_info':
                print("Getting enhanced session info...")
                response = self.api.get_enhanced_session_info()
                self.send_json_response(response)
            elif self.path == '/api/upload_files':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"📁 Uploading files by path: {data['file_paths']}")
                    response = self.api.upload_files(data['file_paths'])
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            elif self.path == '/api/upload_pdf_from_url':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"🔗 Uploading PDF from URL: {data['url']}")
                    response = self.api.upload_pdf_from_url(
                        data['url'], 
                        data.get('display_name')
                    )
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            elif self.path == '/api/list_uploaded_files':
                print("📋 Listing uploaded files...")
                response = self.api.list_uploaded_files()
                self.send_json_response(response)
            
            elif self.path == '/api/delete_file':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"🗑️ Deleting file: {data['file_name']}")
                    response = self.api.delete_file(data['file_name'])
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            elif self.path == '/api/clear_files':
                if self.command == 'POST': # Should be POST for a destructive action
                    print("🧹 Clearing all files...")
                    response = self.api.clear_files()
                    self.send_json_response(response)
                else:
                    self.send_error(405)

            elif self.path == '/api/clear_conversation':
                if self.command == 'POST': # Should be POST for a state-changing action
                    print("💭 Clearing conversation...")
                    response = self.api.clear_conversation()
                    self.send_json_response(response)
                else:
                    self.send_error(405)

            elif self.path == '/api/list_sessions':
                print("📋 Listing saved sessions...")
                sessions = self.api.list_saved_sessions()
                response = {"status": "success", "sessions": sessions}
                self.send_json_response(response)
            
            elif self.path == '/api/update_settings':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"⚙️ Updating settings: {data}")
                    response = self.api.update_session_settings(data)
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            elif self.path == '/api/delete_session':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    session_name = data.get('session_name')
                    print(f"🗑️ Deleting session: {session_name}")
                    success = self.api.delete_saved_session(session_name)
                    if success:
                        response = {"status": "success", "message": f"Session '{session_name}' deleted successfully"}
                    else:
                        response = {"status": "error", "message": f"Failed to delete session '{session_name}'"}
                    self.send_json_response(response)
                else:
                    self.send_error(405)

            elif self.path == '/api/get_session_files':
                # Can be GET or POST depending on preference, but should be consistent
                print("📄 Getting session file paths...")
                file_paths = self.api.get_session_file_paths()
                response = {"status": "success", "file_paths": file_paths}
                self.send_json_response(response)
            
            elif self.path == '/api/reupload_session_files':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    selected_paths = data.get('selected_paths', [])
                    print(f"🔄 Re-uploading session files: {selected_paths}")
                    response = self.api.reupload_files_from_paths(selected_paths)
                    self.send_json_response(response)
                else:
                    self.send_error(405)

            elif self.path == '/api/shutdown':
                if self.command == 'POST':
                    print("🚪 Shutdown requested by user...")
                    self.send_json_response({"status": "success", "message": "Shutting down"})
                    
                    # Shutdown server after responding
                    import threading
                    def shutdown():
                        import time
                        time.sleep(1)
                        self.server.shutdown()
                    
                    threading.Thread(target=shutdown).start()
                else:
                    self.send_error(405)
            
            elif self.path == '/api/upload_file_content':
                if self.command == 'POST':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"📄 Uploading file content: {data['filename']}")
                    response = self.api.upload_file_content(
                        data['filename'], 
                        data['content'], 
                        data.get('size', 0)
                    )
                    self.send_json_response(response)
                else:
                    self.send_error(405)
            
            # Fallback to original API endpoints for backward compatibility
            else:
                print(f"Unknown API endpoint or method not allowed: {self.command} {self.path}")
                self.send_error(404, "API endpoint not found")
            
               
                
        except Exception as e:
            print(f"Error handling API request {self.path}:")
            print(traceback.format_exc())
            error_response = {
                "status": "error",
                "message": f"Server error: {str(e)}"
            }
            self.send_json_response(error_response)
    
    
    
    def send_json_response(self, data):
        try:
            json_data = json.dumps(data)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json_data.encode('utf-8'))
        except Exception as e:
            print(f"Error sending JSON response: {e}")
            self.send_error(500, "Internal server error")
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging to show API calls
        if self.path.startswith('/api/'):
            print(f"API: {self.command} {self.path}")
        else:
            super().log_message(format, *args)
   

def run_enhanced_server():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        return
    
    # Check if index.html exists
    if not os.path.exists("index.html"):
        print("❌ index.html not found in current directory")
        return
    
    # Initialize enhanced API
    api = EnhancedGeminiAPI(api_key)
    
    # Create handler with API
    handler = lambda *args, **kwargs: EnhancedGeminiWebHandler(*args, api=api, **kwargs)
    
    # Start server
    port = 8080
    server_address = ('localhost', port)
    
    print(f"🚀 Starting Enhanced Gemini Web UI on http://localhost:{port}")
    print("📂 Serving files from current directory")
    print("🌐 Opening in your default browser...")
    print("\n🔧 Enhanced Features Available:")
    print("   • Agentic tool execution")
    print("   • Smart context management")
    print("   • Workflow templates")
    print("   • Memory system")
    print("   • Project analysis")
    print("   • Advanced file operations")
    
    # Open in default browser
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        httpd = HTTPServer(server_address, handler)
        print(f"✅ Enhanced server running. Press Ctrl+C to stop.")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down enhanced server...")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ Server error: {e}")

# Compatibility function to maintain backward compatibility
def run_server():
    """Legacy function name for backward compatibility"""
    run_enhanced_server()

if __name__ == "__main__":
    run_enhanced_server()
                