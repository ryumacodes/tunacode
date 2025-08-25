Tutorial skipped. Use /quickstart anytime to start it!
ERROR:ui:Set the `OPENROUTER_API_KEY` environment variable or pass it via `OpenRouterProvider(api_key=...)`to use the OpenRouter provider.

Traceback:
Traceback (most recent call last):
  File "/root/.tunacode-venv/lib/python3.12/site-packages/tunacode/cli/main.py", line 72, in async_main
    await repl(state_manager)
  File "/root/.tunacode-venv/lib/python3.12/site-packages/tunacode/cli/repl.py", line 452, in repl
    instance = agent.get_or_create_agent(state_manager.session.current_model, state_manager)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/tunacode/core/agents/agent_components/agent_config.py", line 281, in get_or_create_agent
    agent = Agent(
            ^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/pydantic_ai/agent.py", line 282, in __init__
    self.model = models.infer_model(model)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/pydantic_ai/models/__init__.py", line 497, in infer_model
    return OpenAIModel(model_name, provider=provider)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/pydantic_ai/models/openai.py", line 188, in __init__
    provider = infer_provider(provider)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/pydantic_ai/providers/__init__.py", line 58, in infer_provider
    return OpenRouterProvider()
           ^^^^^^^^^^^^^^^^^^^^
  File "/root/.tunacode-venv/lib/python3.12/site-packages/pydantic_ai/providers/openrouter.py", line 58, in __init__
    raise UserError(
pydantic_ai.exceptions.UserError: Set the `OPENROUTER_API_KEY` environment variable or pass it
via `OpenRouterProvider(api_key=...)`to use the OpenRouter provider.
