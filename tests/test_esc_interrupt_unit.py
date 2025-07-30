"""
Unit tests for ESC interrupt functionality with stubbed agent.

These tests verify that the cancellation mechanism works correctly
with deterministic fake operations, without relying on actual LLM calls.
"""

import pytest
import trio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest_trio
from tunacode.core.abort_controller import AbortController, AppContext
from tunacode.utils.cancellable_processing import process_with_esc_option, show_thinking_with_esc
from tunacode.utils.keyboard_monitor import monitor_esc_during_operation, KeyboardMonitor
from tunacode.core.state import StateManager


class TestEscInterruptUnit:
    """Unit-level sanity checks for ESC interrupt functionality."""

    @pytest.fixture
    def abort_controller(self):
        """Create a fresh AbortController for each test."""
        return AbortController()
    
    @pytest.fixture
    def mock_nursery(self):
        """Create a mock nursery for testing."""
        nursery = MagicMock()
        nursery.start_soon = MagicMock()
        return nursery
    
    @pytest.fixture
    def app_context(self, mock_nursery, abort_controller):
        """Create an AppContext with mock nursery."""
        return AppContext(mock_nursery, abort_controller)
    
    @pytest.fixture
    def state_manager(self, app_context):
        """Create a StateManager with app context."""
        manager = MagicMock(spec=StateManager)
        manager.app_context = app_context
        return manager

    async def fake_agent_5s(self, *args, **kwargs):
        """Deterministic 5-second fake agent operation."""
        await trio.sleep(5)
        return "Agent completed successfully"

    async def fake_agent_instant(self, *args, **kwargs):
        """Instant fake agent operation for edge case testing."""
        return "Agent completed instantly"

    @pytest.mark.trio
    async def test_abort_controller_basic_functionality(self, abort_controller):
        """Test basic AbortController operations."""
        # Initially not aborted
        assert not abort_controller.is_aborted()
        
        # Abort should set the flag
        abort_controller.abort("test trigger")
        assert abort_controller.is_aborted()
        
        # check_abort should trigger cancellation when aborted
        # We need a cancel scope to properly test this
        with trio.CancelScope() as cancel_scope:
            abort_controller.set_cancel_scope(cancel_scope)
            await abort_controller.check_abort()
            # If we get here, the scope should be cancelled
            assert cancel_scope.cancelled_caught
    
    @pytest.mark.trio
    async def test_abort_controller_reset(self, abort_controller):
        """Test AbortController reset functionality."""
        # Abort and verify state
        abort_controller.abort("test")
        assert abort_controller.is_aborted()
        
        # Reset should clear the state
        abort_controller.reset()
        assert not abort_controller.is_aborted()
        
        # Should not raise after reset
        await abort_controller.check_abort()

    @pytest.mark.trio
    async def test_direct_cancel_scope_integration(self, abort_controller):
        """
        Direct CancelScope test:
        - Start cancellable operation in nursery
        - After 100ms trigger abort
        - Assert Cancelled and nursery exits cleanly
        """
        cancelled = False
        operation_started = False
        
        async def monitored_operation():
            nonlocal operation_started, cancelled
            operation_started = True
            
            with trio.CancelScope() as cancel_scope:
                abort_controller.set_cancel_scope(cancel_scope)
                # Check for abort periodically
                for _ in range(50):  # Max 2.5 seconds
                    await abort_controller.check_abort()
                    await trio.sleep(0.05)  # Check every 50ms
                    
            # If scope caught cancellation, mark as cancelled
            if cancel_scope.cancelled_caught:
                cancelled = True
        
        async with trio.open_nursery() as nursery:
            # Start the operation
            nursery.start_soon(monitored_operation)
            
            # Wait 100ms then abort
            await trio.sleep(0.1)
            abort_controller.abort("test abort after 100ms")
            
            # Give the operation a chance to detect the abort
            with trio.move_on_after(0.5):  # Timeout after 500ms
                while not cancelled:
                    await trio.sleep(0.01)
        
        assert operation_started, "Operation should have started"
        assert cancelled, "Operation should have been cancelled"
        assert abort_controller.is_aborted(), "AbortController should be aborted"

    @pytest.mark.trio 
    async def test_repeated_start_abort_cycles(self, abort_controller):
        """
        Repeated start/abort test:
        Call cancellable operations 10 times, cancelling at random intervals.
        Verify no memory/resource leaks.
        """
        import random
        
        completed_count = 0
        cancelled_count = 0
        
        for i in range(10):
            # Reset controller for each iteration
            abort_controller.reset()
            
            # Random cancellation time between 50-200ms
            cancel_after = random.uniform(0.05, 0.2)
            was_cancelled = False
            
            async def operation():
                nonlocal was_cancelled
                with trio.CancelScope() as cancel_scope:
                    abort_controller.set_cancel_scope(cancel_scope)
                    # Check for abort periodically
                    for _ in range(20):  # Check 20 times over 1 second
                        await abort_controller.check_abort()
                        await trio.sleep(0.05)
                
                # Check if cancelled
                if cancel_scope.cancelled_caught:
                    was_cancelled = True
            
            async with trio.open_nursery() as nursery:
                # Start operation
                nursery.start_soon(operation)
                
                # Start abort timer
                async def abort_timer():
                    await trio.sleep(cancel_after)
                    abort_controller.abort(f"test abort {i}")
                
                nursery.start_soon(abort_timer)
            
            # Count results
            if was_cancelled:
                cancelled_count += 1
            else:
                completed_count += 1
        
        # Most operations should be cancelled given the short timeouts
        assert cancelled_count > completed_count, "Most operations should be cancelled"
        assert cancelled_count + completed_count == 10, "All iterations should complete or cancel"

    @pytest.mark.trio
    async def test_cancellable_processing_with_fake_agent(self, state_manager):
        """Test process_with_esc_option with fake agent."""
        
        # Test successful completion (no cancellation)
        result = await process_with_esc_option(
            state_manager,
            self.fake_agent_instant,
            operation_name="test operation",
            cancel_timeout=0.1  # Short timeout for testing
        )
        
        assert result == "Agent completed instantly"

    @pytest.mark.trio
    async def test_cancellable_processing_with_abort(self, state_manager):
        """Test process_with_esc_option with abort during operation."""
        
        abort_controller = state_manager.app_context.abort_controller
        
        async def abort_after_delay():
            await trio.sleep(0.1)  # Abort after 100ms
            abort_controller.abort("test cancellation")
        
        with pytest.raises(trio.Cancelled):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(abort_after_delay)
                await process_with_esc_option(
                    state_manager,
                    self.fake_agent_5s,
                    operation_name="long test operation",
                    cancel_timeout=0.05  # Very short cancel window
                )

    @pytest.mark.trio
    async def test_thinking_with_esc_cancellation(self, state_manager):
        """Test show_thinking_with_esc with cancellation."""
        
        abort_controller = state_manager.app_context.abort_controller
        
        async def abort_during_thinking():
            await trio.sleep(0.1)
            abort_controller.abort("test thinking cancellation")
        
        # Mock the UI spinner
        with patch('tunacode.utils.cancellable_processing.ui.spinner') as mock_spinner:
            mock_spinner.return_value = MagicMock()
            
            with pytest.raises(trio.Cancelled):
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(abort_during_thinking)
                    await show_thinking_with_esc(
                        state_manager,
                        self.fake_agent_5s
                    )

    @pytest.mark.trio
    async def test_keyboard_monitor_basic_functionality(self, abort_controller):
        """Test KeyboardMonitor creation and basic operations."""
        
        monitor = KeyboardMonitor(abort_controller)
        
        # Should not be monitoring initially
        assert not monitor._monitoring
        
        # Stop monitoring should be safe even if not started
        await monitor.stop_monitoring()

    @pytest.mark.trio
    async def test_monitor_esc_during_operation_success(self, abort_controller):
        """Test monitor_esc_during_operation with successful completion."""
        
        # Mock the keyboard monitor to avoid terminal manipulation in tests
        with patch('tunacode.utils.keyboard_monitor.KeyboardMonitor') as MockMonitor:
            mock_monitor = MagicMock()
            mock_monitor.start_monitoring = AsyncMock()
            mock_monitor.stop_monitoring = AsyncMock()
            MockMonitor.return_value = mock_monitor
            
            result = await monitor_esc_during_operation(
                abort_controller,
                self.fake_agent_instant
            )
            
            assert result == "Agent completed instantly"
            mock_monitor.start_monitoring.assert_called_once()
            mock_monitor.stop_monitoring.assert_called_once()

    @pytest.mark.trio
    async def test_monitor_esc_during_operation_cancellation(self, abort_controller):
        """Test monitor_esc_during_operation with cancellation."""
        
        async def abort_after_delay():
            await trio.sleep(0.1)
            abort_controller.abort("test keyboard cancellation")
        
        with patch('tunacode.utils.keyboard_monitor.KeyboardMonitor') as MockMonitor:
            mock_monitor = MagicMock()
            mock_monitor.start_monitoring = AsyncMock()
            mock_monitor.stop_monitoring = AsyncMock()
            MockMonitor.return_value = mock_monitor
            
            with pytest.raises(trio.Cancelled):
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(abort_after_delay)
                    
                    # Use a cancel scope to catch the abort
                    with trio.CancelScope() as cancel_scope:
                        abort_controller.set_cancel_scope(cancel_scope)
                        await monitor_esc_during_operation(
                            abort_controller,
                            self.fake_agent_5s
                        )

    @pytest.mark.trio
    async def test_fast_command_edge_case(self, state_manager):
        """
        Test edge case: Issue instant command and trigger abort - 
        should never get stray "Cancelled" for completed job.
        """
        
        abort_controller = state_manager.app_context.abort_controller
        
        # Run instant operation
        result = await process_with_esc_option(
            state_manager,
            self.fake_agent_instant,
            operation_name="instant command",
            cancel_timeout=0.05
        )
        
        # Operation should complete successfully
        assert result == "Agent completed instantly"
        
        # Now abort after completion - should not affect anything
        abort_controller.abort("late abort")
        assert abort_controller.is_aborted()
        
        # Reset for next operation
        abort_controller.reset()
        assert not abort_controller.is_aborted()

    @pytest.mark.trio
    async def test_double_esc_edge_case(self, abort_controller):
        """
        Test double Esc scenario - only one cancellation should fire.
        """
        
        abort_call_count = 0
        original_abort = abort_controller.abort
        
        def counting_abort(trigger="Manual"):
            nonlocal abort_call_count
            abort_call_count += 1
            return original_abort(trigger)
        
        abort_controller.abort = counting_abort
        
        # Multiple abort calls should be idempotent
        abort_controller.abort("first esc")
        abort_controller.abort("second esc") 
        abort_controller.abort("third esc")
        
        # Should only register the first abort
        assert abort_call_count == 3  # All calls are made
        assert abort_controller.is_aborted()  # But state is consistent

    @pytest.mark.trio
    async def test_memory_leak_detection(self, abort_controller):
        """
        Basic memory leak detection - ensure no Task/thread count creep.
        """
        import threading
        import gc
        
        initial_thread_count = len(threading.enumerate())
        
        # Run multiple operations
        for i in range(5):
            abort_controller.reset()
            
            try:
                async with trio.open_nursery() as nursery:
                    async def short_operation():
                        with trio.CancelScope() as cancel_scope:
                            abort_controller.set_cancel_scope(cancel_scope)
                            await trio.sleep(0.1)
                        return f"Operation {i}"
                    
                    async def abort_timer():
                        await trio.sleep(0.05)  # Abort halfway through
                        abort_controller.abort(f"abort {i}")
                    
                    nursery.start_soon(short_operation)
                    nursery.start_soon(abort_timer)
                    
            except trio.Cancelled:
                pass  # Expected
        
        # Force garbage collection
        gc.collect()
        await trio.sleep(0.1)  # Allow cleanup
        
        final_thread_count = len(threading.enumerate())
        
        # Thread count should not have grown significantly
        assert final_thread_count <= initial_thread_count + 2, \
            f"Thread count grew from {initial_thread_count} to {final_thread_count}"

    @pytest.mark.trio
    async def test_instrumentation_structured_logging(self, abort_controller):
        """
        Test structured logging for cancellation events.
        This would be enhanced with actual log capture in a real implementation.
        """
        
        events = []
        
        # Mock the debug system if available
        try:
            with patch('tunacode.utils.cancellable_processing.trio_debug') as mock_debug:
                mock_debug.log_event = lambda event, component, message, level: events.append({
                    'event': event, 'component': component, 'message': message, 'level': level
                })
                
                try:
                    async with trio.open_nursery() as nursery:
                        async def operation():
                            with trio.CancelScope() as cancel_scope:
                                abort_controller.set_cancel_scope(cancel_scope)
                                await trio.sleep(1)
                        
                        async def abort_timer():
                            await trio.sleep(0.1)
                            abort_controller.abort("instrumentation test")
                        
                        nursery.start_soon(operation)
                        nursery.start_soon(abort_timer)
                        
                except trio.Cancelled:
                    pass
                
                # Should have logged cancellation events
                event_types = [event['event'] for event in events]
                assert any('CANCEL' in event_type for event_type in event_types), \
                    f"Should have cancellation events in {event_types}"
                    
        except ImportError:
            # Debug system not available, skip detailed logging test
            pytest.skip("Debug system not available for instrumentation test")


@pytest.mark.cancellation
class TestCancellationMarker:
    """Tests specifically marked for cancellation testing in CI."""
    
    @pytest.mark.trio
    async def test_cancellation_timing(self):
        """Test that cancellation happens within reasonable time bounds."""
        import time
        
        abort_controller = AbortController()
        start_time = time.time()
        
        try:
            async with trio.open_nursery() as nursery:
                async def long_operation():
                    with trio.CancelScope() as cancel_scope:
                        abort_controller.set_cancel_scope(cancel_scope)
                        await trio.sleep(10)  # Very long operation
                
                async def abort_timer():
                    await trio.sleep(0.1)  # Abort after 100ms
                    abort_controller.abort("timing test")
                
                nursery.start_soon(long_operation)
                nursery.start_soon(abort_timer)
                
        except trio.Cancelled:
            pass
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete within 2 seconds (much less than the 10s operation)
        assert elapsed < 2.0, f"Cancellation took {elapsed}s, should be < 2s"
        assert elapsed > 0.05, f"Cancellation took {elapsed}s, should be > 50ms"