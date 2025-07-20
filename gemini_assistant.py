import os
import io
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Optional, Union
from pathlib import Path
import google.generativeai as genai

load_dotenv()

class GeminiSession:
    def __init__(
        self,
        api_key=None,
        model_name="gemini-1.5-pro-latest",
        use_dynamic_tokens=True,
        max_total_tokens=1024,
        hard_cap=512,
        truncate_output=False,
        truncate_chars=1000,
        add_short_hint=True,
        enable_streaming=True,
    ):
        # Configure the API key - use provided key or get from environment
        if api_key:
            genai.configure(api_key=api_key)
        else:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            genai.configure(api_key=api_key)
        
        # Set configuration parameters
        self.model_name = model_name
        self.use_dynamic_tokens = use_dynamic_tokens
        self.max_total_tokens = max_total_tokens
        self.hard_cap = hard_cap
        self.truncate_output = truncate_output
        self.truncate_chars = truncate_chars
        self.add_short_hint = add_short_hint
        self.enable_streaming = enable_streaming
        
        # Initialize session state
        self.history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.uploaded_files = []
        self.file_metadata = {}  # Store file info for better tracking

    def estimate_input_tokens(self, text: str) -> int:
        """Improved token estimation for text."""
        return int(len(text.split()) / 0.75)

    def estimate_document_tokens(self, file_path: str) -> int:
        """Estimate tokens for document files based on Gemini documentation."""
        if file_path.lower().endswith('.pdf'):
            # For PDFs, we can't easily count pages without parsing
            # Using a rough estimate based on file size
            try:
                file_size = os.path.getsize(file_path)
                # Rough estimate: assume average PDF page ~50KB, 258 tokens per page
                estimated_pages = max(1, file_size // 50000)
                return min(estimated_pages * 258, 1000 * 258)  # Cap at 1000 pages
            except:
                return 1000  # Default estimate
        else:
            # For text files, use standard estimation
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return self.estimate_input_tokens(content)
            except:
                return 500  # Default estimate

    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate file before upload."""
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, f"File is empty: {file_path}"
        
        # Check file extension
        ext = Path(file_path).suffix.lower()
        supported_extensions = {'.pdf', '.txt', '.md', '.html', '.xml', '.py', '.json', '.yaml', '.yml', '.csv'}
        if ext not in supported_extensions:
            return False, f"Unsupported file type: {ext}. Supported: {supported_extensions}"
        
        # For PDFs, estimate page count (rough)
        if ext == '.pdf':
            estimated_pages = max(1, file_size // 50000)
            if estimated_pages > 1000:
                return False, f"PDF too large (estimated {estimated_pages} pages, max 1000)"
        
        return True, "Valid"

    def build_prompt(self, user_input: str) -> str:
        """Build prompt with conversation history."""
        self.history.append({"role": "user", "text": user_input})
        history_text = "\n\n".join([f"{m['role'].capitalize()}: {m['text']}" for m in self.history])
        return history_text

    def _stream_response(self, response_stream):
        """Handle streaming response and return complete text."""
        complete_text = ""
        print("Gemini > ", end="", flush=True)
        
        try:
            for chunk in response_stream:
                if hasattr(chunk, 'text') and chunk.text:
                    print(chunk.text, end="", flush=True)
                    complete_text += chunk.text
            print()  # New line after streaming is complete
        except Exception as e:
            print(f"\nERROR: Streaming error: {e}")
            return complete_text
        
        return complete_text

    def store_response(self, response_text: str, input_tokens: int, output_tokens: int):
        """Store assistant response in history."""
        self.history.append({"role": "assistant", "text": response_text})
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def _generate_usage_report(self, input_tokens: int, output_tokens: int) -> str:
        """Generate token usage report."""
        return (
            f"\n--- Token Usage ---\n"
            f"Input tokens (this turn): {input_tokens}\n"
            f"Output tokens (this turn): {output_tokens}\n"
            f"Cumulative input tokens: {self.total_input_tokens}\n"
            f"Cumulative output tokens: {self.total_output_tokens}\n"
            f"Total tokens used: {self.total_input_tokens + self.total_output_tokens}\n"
            f"Files loaded: {len(self.uploaded_files)}\n"
            f"-------------------"
        )
        
    def ask(self, user_input: str, return_usage_only=False, is_raw_prompt: bool = False) -> str:
            """Ask question without files. Supports a 'raw' mode for agentic prompts."""
            
            # In raw mode, use the input directly. Otherwise, build from history.
            if is_raw_prompt:
                prompt = user_input
            else:
                prompt = self.build_prompt(user_input)
                if self.add_short_hint:
                    prompt += "\n(Please answer concisely and focus on code or diagrams.)"

            input_tokens = self.estimate_input_tokens(prompt)

            if self.use_dynamic_tokens:
                max_output_tokens = max(128, min(self.max_total_tokens - input_tokens, self.hard_cap))
            else:
                max_output_tokens = self.hard_cap

            try:
                model = genai.GenerativeModel(self.model_name)
                
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=max_output_tokens,
                )
                
                # Streaming logic remains the same
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=True
                )
                reply = self._stream_response(response)
                
                output_tokens = self.estimate_input_tokens(reply)
                
                # Only store history for normal, conversational prompts
                if not is_raw_prompt:
                    self.store_response(reply, input_tokens, output_tokens)

                usage_report = self._generate_usage_report(input_tokens, output_tokens)

                if self.truncate_output:
                    reply = reply[:self.truncate_chars]

                # For raw prompts, we typically just want the direct reply
                if return_usage_only:
                    return usage_report
                if is_raw_prompt:
                    return reply

                return reply + usage_report

            except Exception as e:
                error_msg = f"ERROR: Error during request: {e}"
                print(error_msg)
                return error_msg

    def ask_with_files(self, user_input: str, return_usage_only=False) -> str:
        """Send a prompt along with uploaded files."""
        if not self.uploaded_files:
            return "ERROR: No files uploaded. Use upload_files(file_paths) first."

        input_tokens = self.estimate_input_tokens(user_input)
        
        # Add estimated tokens from files
        for file_info in self.file_metadata.values():
            input_tokens += file_info.get('estimated_tokens', 0)

        if self.use_dynamic_tokens:
            max_output_tokens = max(128, min(self.max_total_tokens - input_tokens, self.hard_cap))
        else:
            max_output_tokens = self.hard_cap

        try:
            model = genai.GenerativeModel(self.model_name)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_output_tokens,
            )
            
            # Build contents list with files and prompt
            contents = self.uploaded_files + [user_input]
            
            if self.enable_streaming:
                response = model.generate_content(
                    contents,
                    generation_config=generation_config,
                    stream=True
                )
                reply = self._stream_response(response)
            else:
                response = model.generate_content(
                    contents,
                    generation_config=generation_config
                )
                reply = response.text
                
            output_tokens = self.estimate_input_tokens(reply)
            
            # Store in history with file context
            file_context = f"[With files: {', '.join(self.file_metadata.keys())}]"
            self.history.append({"role": "user", "text": f"{file_context} {user_input}"})
            self.history.append({"role": "assistant", "text": reply})
            
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

            usage_report = self._generate_usage_report(input_tokens, output_tokens)

            if self.truncate_output:
                reply = reply[:self.truncate_chars]

            if return_usage_only:
                return usage_report

            return reply + usage_report

        except Exception as e:
            error_msg = f"ERROR: Error during request: {e}"
            print(error_msg)
            return error_msg

    def upload_files(self, file_paths: List[str]) -> List:
        """Upload multiple files (PDF or text) and store references for later use."""
        successful_uploads = []
        
        for path in file_paths:
            path = path.strip().strip('"').strip("'")
            if not path:
                continue
                
            # Validate file
            is_valid, message = self.validate_file(path)
            if not is_valid:
                print(f"ERROR: Skipping {path}: {message}")
                continue
            
            try:
                # Get original filename
                original_name = os.path.basename(path)
                mime_type = self._get_mime_type(path)
                
                # Upload file using genai.upload_file
                uploaded_file = genai.upload_file(path, display_name=original_name)
                
                # Store metadata with original name
                estimated_tokens = self.estimate_document_tokens(path)
                self.file_metadata[original_name] = {
                    'path': path,
                    'mime_type': mime_type,
                    'estimated_tokens': estimated_tokens,
                    'upload_name': uploaded_file.name,
                    'display_name': original_name
                }
                
                self.uploaded_files.append(uploaded_file)
                successful_uploads.append(uploaded_file)
                print(f"SUCCESS: Uploaded: {original_name} -> {uploaded_file.name}")
                print(f"   Estimated tokens: {estimated_tokens}")
                
            except Exception as e:
                print(f"ERROR: Failed to upload {path}: {e}")
        
        return successful_uploads  # ✅ FIXED: Now properly inside the method!

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type based on file extension."""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/plain',      # Markdown as plain text
            '.html': 'text/plain',    # HTML as plain text  
            '.xml': 'text/plain',     # XML as plain text
            '.py': 'text/plain',      # Python as plain text ✅
            '.json': 'text/plain',    # JSON as plain text
            '.yaml': 'text/plain',    # YAML as plain text
            '.yml': 'text/plain',     # YAML as plain text
            '.csv': 'text/plain',     # CSV as plain text
            '.js': 'text/plain',      # JavaScript as plain text
            '.ts': 'text/plain',      # TypeScript as plain text
            '.jsx': 'text/plain',     # React JSX as plain text
            '.tsx': 'text/plain',     # React TSX as plain text
            '.cpp': 'text/plain',     # C++ as plain text
            '.c': 'text/plain',       # C as plain text
            '.java': 'text/plain',    # Java as plain text
            '.rb': 'text/plain',      # Ruby as plain text
            '.php': 'text/plain',     # PHP as plain text
            '.go': 'text/plain',      # Go as plain text
            '.rs': 'text/plain',      # Rust as plain text
            '.sql': 'text/plain',     # SQL as plain text
        }
        return mime_types.get(ext, 'text/plain')

    def clear_conversation(self):
        """Clear conversation history but keep uploaded files."""
        self.history = []
        print("Conversation history cleared.")

    def toggle_streaming(self):
        """Toggle streaming mode on/off."""
        self.enable_streaming = not self.enable_streaming
        status = "enabled" if self.enable_streaming else "disabled"
        print(f"Streaming {status}.")
        return self.enable_streaming