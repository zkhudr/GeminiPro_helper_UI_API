# Enhanced Gemini WebUI - Comprehensive Test Plan

## Phase 1: Ridiculous Verification Tests

### Basic Sanity Checks
1. **Server Launch Verification**
  - Batch file executes without errors
  - Server starts on port 8080
  - Browser opens automatically
  - No Python import errors in console

2. **UI Element Existence**
  - Enhanced Mode checkbox exists and is unchecked by default
  - All file upload buttons present with correct names
  - Exit Application button is red and visible
  - Token counters display "0" initially

3. **Mode Toggle Verification**
  - Legacy mode: Only basic file controls visible
  - Enhanced mode: Memory, Workflow, and Tools panels appear
  - Toggle works both directions without JavaScript errors
  - Status messages appear for mode switches

### File Upload Ridiculous Tests
4. **Upload by File Paths**
  - Modal opens with textarea
  - Accepts single file path
  - Accepts multiple newline-separated paths
  - Accepts comma-separated paths
  - Handles mixed newline and comma separation
  - Validates non-existent file paths gracefully
  - Windows path format handling (backslashes)
  - Very long file paths (250+ characters)

5. **Upload by File Picker**
  - File picker opens
  - Multiple file selection works
  - File size validation
  - Supported file types only (.py, .txt, .md, .html, .json, .yaml, .csv, .pdf)
  - Large file handling (10MB+ files)

6. **Upload PDF from URL**
  - Direct PDF URL handling
  - Redirected URLs (OneDrive, Google Drive)
  - Invalid URLs fail gracefully
  - Non-PDF URLs rejected
  - Network timeout handling

### Enhanced Features Ridiculous Tests
7. **Tool System Verification**
  - All 4 tools display: file_operations, bash_commands, git_operations, web_search
  - Tool help displays detailed information
  - Tool buttons clickable and responsive
  - Auto-approve checkbox functions

8. **Workflow Templates Verification**
  - All 5 workflows display: CODE REVIEW, FEATURE IMPLEMENTATION, DEBUG ASSISTANCE, REFACTORING, DOCUMENTATION
  - Each workflow button applies correctly
  - Auto-approve settings change per workflow
  - Custom instruction text box accepts input

9. **Memory System Verification**
  - Memory search box functional
  - Search button responds
  - Empty search handling
  - Special character handling in search
  - Memory scope recognition

## Phase 2: Functional Integration Tests

### Session Management
10. **Basic Session Operations**
   - Save session with valid name
   - Save session with special characters in name
   - Load existing session
   - Delete session confirmation dialog
   - Session list refresh after operations

11. **Enhanced Session Features**
   - Enhanced session save includes context
   - Enhanced session load restores tools
   - Project path persistence across sessions
   - Memory entries persist in sessions
   - File paths stored for re-upload capability

### File Operations Integration
12. **File Management Workflow**
   - Upload files via paths
   - List files shows uploaded content
   - Clear files removes all files
   - File operations trigger automatic list refresh
   - File metadata tracking accurate

13. **Context Integration**
   - Project context loads automatically
   - Context analysis provides meaningful suggestions
   - Set Project Path changes context scope
   - Show Context displays relevant information

## Phase 3: Enhanced Mode Stress Tests

### Tool Execution Verification
14. **File Operations Tool**
   - Read operation on existing files
   - Write operation creates new files
   - Directory listing works
   - File search with patterns
   - Error handling for invalid paths

15. **Git Operations Tool**
   - Git status in valid repository
   - Git log retrieval
   - Git diff display
   - Branch operations (if in git repo)
   - Graceful handling of non-git directories

16. **Bash Commands Tool**
   - Safe commands execute (ls, pwd, echo)
   - Dangerous commands blocked (rm -rf, sudo)
   - Command timeout enforcement
   - Working directory parameter
   - Error output capture

17. **Web Search Tool**
   - Search functionality (if implemented)
   - URL fetch operation
   - Network error handling
   - Content size limitations

### Workflow Execution Tests
18. **Code Review Workflow**
   - Applies appropriate prompt
   - Enables file_operations auto-approve
   - Integrates with project context
   - Produces actionable output

19. **Feature Implementation Workflow**
   - Planning phase execution
   - Multi-step process handling
   - Git integration for commits
   - Test creation suggestions

20. **Debug Assistance Workflow**
   - Log analysis capability
   - Git history integration
   - Error pattern recognition
   - Solution recommendations

## Phase 4: RAG Project Migration Test

### Pre-Migration Setup
21. **Workspace Preparation**
   - Create M:\CortexOS\workspace folder
   - Copy RAG project files to workspace
   - Verify all 10 .py files present
   - Confirm index.html and ragapp.js exist
   - Locate manifesto.md file

### Legacy Mode Migration Test
22. **Basic RAG Project Analysis**
   - Set project path to workspace folder
   - Upload all .py files via file paths
   - Upload manifesto.md
   - Upload index.html and ragapp.js
   - List files to verify all uploads
   - Basic chat about project structure

23. **Legacy Mode Tasks**
   - Ask for project overview
   - Request explanation of each .py file
   - Understand manifesto.md requirements
   - Identify main application entry points
   - Document current architecture

### Enhanced Mode Migration Test
24. **Enhanced Project Analysis**
   - Switch to Enhanced Mode
   - Click "Analyze Project" button
   - Review automatic suggestions
   - Use "Show Context" to see project understanding
   - Search memory for previous insights

25. **Code Review Workflow on RAG Project**
   - Apply CODE REVIEW workflow
   - Let AI analyze all .py files
   - Review suggestions for improvements
   - Check for security vulnerabilities
   - Identify code quality issues

26. **Feature Implementation Workflow**
   - Apply FEATURE IMPLEMENTATION workflow
   - Request manifesto.md compliance analysis
   - Ask for implementation plan for missing features
   - Execute step-by-step improvements
   - Verify git operations work

27. **Refactoring Workflow**
   - Apply REFACTORING workflow
   - Request code organization improvements
   - Modernize legacy patterns
   - Optimize performance bottlenecks
   - Update documentation

### Advanced Integration Tests
28. **Memory System with RAG Project**
   - Remember key project patterns: #remember rag_pattern=Uses vector embeddings for document search scope=project
   - Remember architecture decisions: #remember db_choice=ChromaDB for vector storage scope=project
   - Search memory for architecture info
   - Verify persistence across sessions

29. **Tool Integration for RAG Migration**
   - Use file_operations to read/write project files
   - Use git_operations to track changes
   - Use bash_commands to run tests/setup
   - Use web_search for latest RAG best practices

30. **End-to-End Migration Workflow**
   - Complete manifesto.md compliance check
   - Implement all missing features
   - Refactor legacy code
   - Add comprehensive documentation
   - Create deployment instructions
   - Generate final project report

## Phase 5: Edge Cases and Error Handling

### Stress Tests
31. **Large File Handling**
   - Upload 50+ files via file paths
   - Process large codebases (100+ files)
   - Handle deeply nested directory structures
   - Memory usage during heavy operations

32. **Network and System Stress**
   - Very slow network conditions
   - Large PDF downloads from URLs
   - Concurrent file operations
   - System resource exhaustion scenarios

33. **Error Recovery**
   - API key invalid/expired scenarios
   - Network disconnection during operations
   - File permission errors
   - Git repository corruption scenarios

### Boundary Tests
34. **Input Validation**
   - Very long file paths (500+ characters)
   - Special characters in filenames
   - Unicode characters in content
   - Extremely large prompts (10,000+ characters)

35. **Session Limits**
   - Maximum number of uploaded files
   - Memory system storage limits
   - Conversation history size limits
   - Token usage boundaries

## Phase 6: Performance and Reliability

### Performance Benchmarks
36. **Response Time Measurements**
   - File upload speed per file type
   - Workflow application response time
   - Tool execution performance
   - Context loading speed

37. **Resource Usage Monitoring**
   - Memory consumption during operations
   - CPU usage during heavy analysis
   - Browser performance with large projects
   - Server stability over extended use

### Reliability Tests
38. **Long-Running Session Tests**
   - 4+ hour continuous operation
   - Multiple workflow executions
   - Memory leak detection
   - Session state consistency

39. **Recovery and Persistence**
   - Server restart mid-operation
   - Browser refresh during processing
   - Session data integrity after crashes
   - Auto-save functionality verification

## Success Criteria

### Minimum Viable Product (MVP)
- All basic file operations work flawlessly
- Enhanced mode enables without errors
- At least 3 workflow templates functional
- RAG project can be uploaded and analyzed
- Basic tool operations execute successfully

### Full Feature Success
- All 5 workflows complete complex tasks
- All 4 tools integrate seamlessly
- RAG project fully migrated per manifesto.md
- Memory system provides intelligent assistance
- Performance remains responsive under load

### Excellence Criteria
- Zero JavaScript errors during operation
- Intuitive user experience
- Comprehensive error handling
- Professional-grade code analysis
- Production-ready project migration capability

## Test Execution Schedule

### Day 1: Ridiculous Verification (Phase 1-2)
- Basic sanity and UI tests
- File upload variations
- Session management

### Day 2: Enhanced Features (Phase 3)
- Tool execution tests
- Workflow verification
- Integration testing

### Day 3: RAG Migration (Phase 4)
- Legacy mode analysis
- Enhanced mode migration
- End-to-end workflow

### Day 4: Edge Cases (Phase 5)
- Stress testing
- Error scenarios
- Boundary conditions

### Day 5: Performance (Phase 6)
- Benchmarking
- Reliability testing
- Final validation

## Notes for RAG Project Test
- Manifesto.md compliance is primary success metric
- Each .py file should be individually analyzed
- Legacy to enhanced migration should show clear improvements
- Final deliverable: Fully modernized RAG application
- Documentation: Complete migration report with before/after analysis