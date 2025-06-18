# Product Context

## User Experience Goals
- Provide seamless AI-powered coding assistance in the terminal
- Enable safe file operations with confirmation UI (unless in yolo mode)
- Support multiple LLM providers with easy model switching
- Maintain context across sessions through memory management
- Offer intuitive commands and multiline input with syntax highlighting
- Encourage safe practices (git branches, no auto-commits)

## Target Audience
- Software developers who work primarily in the terminal
- Teams wanting to integrate AI assistance into their CLI workflow
- Developers who need multi-provider LLM support
- Users requiring persistent context across AI sessions

## Success Metrics
- ~80% code coverage with characterization tests
- All critical paths have golden-master tests
- Safe refactoring enabled through comprehensive test suite
- Memory workflow enables effective multi-session development
- Tool confirmations prevent accidental file modifications
