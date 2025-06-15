# Architect Mode Prompts

This directory contains optimized prompts for the architect mode components, following research-based prompt engineering principles.

## Files

- `architect_planner.md` - Task planning prompt for ConstrainedPlanner
- `architect_feedback.md` - Feedback analysis prompt for FeedbackLoop
- `system.md` - Main system prompt (existing)

## Prompt Engineering Principles Applied

### 1. Structure and Clarity
- **Delimiters** (#17): Using `###Instruction###`, `###Examples###`, etc.
- **Leading phrases** (#12): "Think step by step"
- **Output primers** (#20): Ending with `[` to start JSON array

### 2. Direct Communication
- **No politeness** (#1): Removed "please", "thank you", etc.
- **Affirmative directives** (#4): Using "Do" instead of "Don't"
- **Expert audience** (#2): "You are an expert software architect"

### 3. Motivation and Constraints
- **Task requirements** (#9): "Your task is", "You MUST"
- **Penalties** (#10): "You will be penalized for..."
- **Incentives** (#6): "I'm going to tip $500 for..."

### 4. Examples and Specificity
- **Few-shot examples** (#7, #19): Multiple realistic examples
- **Clear requirements** (#25): Explicit JSON format specifications
- **Role assignment** (#16): Specific expert roles

### 5. Reasoning Enhancement
- **Chain of thought** (#12): "Think step by step"
- **Bias prevention** (#13): "Ensure your answer is unbiased"
- **Natural responses** (#11): "Answer in natural JSON array format"

## Benefits

1. **Higher Success Rate**: Structured prompts reduce parsing errors
2. **Better Task Quality**: Examples guide proper task generation
3. **Fewer Retries**: Clear constraints prevent invalid outputs
4. **Consistent Results**: Standardized format across runs

## Usage

The prompts are automatically loaded by:
- `ConstrainedPlanner` uses `architect_planner.md`
- `FeedbackLoop` uses `architect_feedback.md`

Both components include fallback prompts if files are not found.

## Future Improvements

1. A/B test different prompt variations
2. Add domain-specific examples
3. Optimize token usage while maintaining effectiveness
4. Create prompts for other architect components