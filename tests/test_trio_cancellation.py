"""
Unit tests for Trio-based cancellation behavior.

Tests the core cancellation functionality including:
- Esc key cancellation within 100ms
- Ctrl-C triggers same abort flow  
- Streaming output stops immediately on abort
- Prompt recovery after cancellation
"""

import pytest
import trio
from unittest.mock import Mock, AsyncMock

from src.tunacode.core.abort_controller import AbortController, AppContext
from src.tunacode.core.state import StateManager

# Use pytest-trio for Trio-based async tests
pytest_plugins = ['trio']


class TestAbortController:
    """Test the AbortController functionality."""

    def test_initial_state(self):
        """Test AbortController starts in correct state."""
        controller = AbortController()
        assert not controller.is_aborted()

    def test_abort_functionality(self):
        """Test basic abort functionality."""
        controller = AbortController()
        controller.abort()
        assert controller.is_aborted()

    def test_reset_functionality(self):
        """Test reset clears abort state."""
        controller = AbortController()
        controller.abort()
        controller.reset()
        assert not controller.is_aborted()

    async def test_cancel_scope_integration(self):
        """Test that AbortController cancels associated CancelScope."""
        controller = AbortController()
        
        with trio.CancelScope() as cancel_scope:
            controller.set_cancel_scope(cancel_scope)
            controller.abort()
            assert cancel_scope.cancel_called

    async def test_wait_for_abort(self):
        """Test waiting for abort signal."""
        controller = AbortController()
        
        async def abort_after_delay():
            await trio.sleep(0.1)
            controller.abort()
        
        async with trio.open_nursery() as nursery:
            nursery.start_soon(abort_after_delay)
            await controller.wait_for_abort()
            
        assert controller.is_aborted()

    async def test_check_abort_raises_cancelled(self):
        """Test that check_abort raises Cancelled when aborted."""
        controller = AbortController()
        controller.abort()
        
        with pytest.raises(trio.Cancelled):
            await controller.check_abort()


class TestAppContext:
    """Test the AppContext functionality."""

    async def test_app_context_creation(self):
        """Test AppContext creation and basic properties."""
        async with trio.open_nursery() as nursery:
            abort_controller = AbortController()
            app_context = AppContext(nursery, abort_controller)
            
            assert app_context.nursery is nursery
            assert app_context.abort_controller is abort_controller
            assert not app_context.is_shutdown_requested()

    async def test_shutdown_request(self):
        """Test shutdown request functionality."""
        async with trio.open_nursery() as nursery:
            abort_controller = AbortController()
            app_context = AppContext(nursery, abort_controller)
            
            app_context.request_shutdown()
            
            assert app_context.is_shutdown_requested()
            assert app_context.abort_controller.is_aborted()


class TestCancellationFlow:
    """Test end-to-end cancellation flows."""

    @pytest.mark.asyncio
    async def test_esc_cancellation_within_100ms(self):
        """Test that Esc key cancellation works within 100ms."""
        controller = AbortController()
        start_time = trio.current_time()
        cancelled = False
        
        async def long_running_task():
            nonlocal cancelled
            try:
                with trio.CancelScope() as cancel_scope:
                    controller.set_cancel_scope(cancel_scope)
                    await trio.sleep(10)  # This should be cancelled quickly
            except trio.Cancelled:
                cancelled = True
                raise

        async def simulate_esc_press():
            await trio.sleep(0.05)  # 50ms delay
            controller.abort()

        with pytest.raises(trio.Cancelled):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(long_running_task)
                nursery.start_soon(simulate_esc_press)

        end_time = trio.current_time()
        cancellation_time = (end_time - start_time) * 1000  # Convert to ms
        
        assert cancelled
        assert cancellation_time < 100  # Should cancel within 100ms

    @pytest.mark.asyncio
    async def test_ctrl_c_same_as_esc(self):
        """Test that Ctrl-C triggers the same abort flow as Esc."""
        controller = AbortController()
        
        # Test Esc behavior
        with trio.CancelScope() as esc_scope:
            controller.set_cancel_scope(esc_scope)
            controller.abort()  # Simulate Esc
            assert esc_scope.cancel_called
            
        # Reset and test Ctrl-C behavior (same mechanism)
        controller.reset()
        
        with trio.CancelScope() as ctrl_c_scope:
            controller.set_cancel_scope(ctrl_c_scope)
            controller.abort()  # Simulate Ctrl-C (same method)
            assert ctrl_c_scope.cancel_called

    @pytest.mark.asyncio 
    async def test_streaming_stops_immediately_on_abort(self):
        """Test that streaming output stops immediately when aborted."""
        controller = AbortController()
        stream_stopped = False
        
        class MockStreamingPanel:
            def __init__(self):
                self.active = True
                
            async def update(self, content):
                if controller.is_aborted():
                    nonlocal stream_stopped
                    stream_stopped = True
                    raise trio.Cancelled("Stream aborted")
                await trio.sleep(0.01)  # Simulate streaming delay
        
        async def streaming_task():
            panel = MockStreamingPanel()
            try:
                for i in range(100):
                    await panel.update(f"content {i}")
            except trio.Cancelled:
                raise

        async def abort_streaming():
            await trio.sleep(0.05)  # Let streaming start
            controller.abort()

        with pytest.raises(trio.Cancelled):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(streaming_task)
                nursery.start_soon(abort_streaming)

        assert stream_stopped

    @pytest.mark.asyncio
    async def test_prompt_recovery_after_cancellation(self):
        """Test that the system can recover and show prompt after cancellation."""
        controller = AbortController()
        recovered = False
        
        async def simulate_cancelled_operation():
            try:
                with trio.CancelScope() as cancel_scope:
                    controller.set_cancel_scope(cancel_scope)
                    await trio.sleep(1)  # Long operation
            except trio.Cancelled:
                # Simulate recovery
                nonlocal recovered
                recovered = True
                raise

        async def abort_and_recover():
            await trio.sleep(0.1)
            controller.abort()
            
            # After cancellation, system should be able to continue
            await trio.sleep(0.1)
            assert recovered

        with pytest.raises(trio.Cancelled):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(simulate_cancelled_operation)
                nursery.start_soon(abort_and_recover)

        # Verify we can create new operations after cancellation
        controller.reset()
        assert not controller.is_aborted()


class TestStateManagerIntegration:
    """Test StateManager integration with AbortController."""

    @pytest.mark.asyncio
    async def test_state_manager_holds_app_context(self):
        """Test that StateManager can hold and provide AppContext."""
        async with trio.open_nursery() as nursery:
            abort_controller = AbortController()
            app_context = AppContext(nursery, abort_controller)
            
            state_manager = StateManager()
            state_manager.app_context = app_context
            
            assert state_manager.app_context is app_context
            assert state_manager.app_context.abort_controller is abort_controller

    @pytest.mark.asyncio
    async def test_abort_through_state_manager(self):
        """Test aborting operations through StateManager."""
        async with trio.open_nursery() as nursery:
            abort_controller = AbortController()
            app_context = AppContext(nursery, abort_controller)
            
            state_manager = StateManager()
            state_manager.app_context = app_context
            
            # Simulate abort through state manager
            state_manager.app_context.abort_controller.abort()
            
            assert state_manager.app_context.abort_controller.is_aborted()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])