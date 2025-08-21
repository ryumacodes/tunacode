# Onboarding Improvements (PR #88)

## Key Enhancements

### Wizard Setup
- Fixed branch safety interference during setup
- GitSafetySetup now skips prompts in wizard mode
- Better error messaging and retry guidance
- Improved API key validation flow

### First-Time User Experience
- Clear post-install instructions via UV
- References to `tunacode --setup` wizard
- Default OpenRouter configuration
- Streamlined initial setup flow

### Technical Details
- `wizard_mode` parameter passed to setup steps
- Coordinator handles mode propagation
- Non-intrusive safety checks during wizard
