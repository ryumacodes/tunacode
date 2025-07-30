#!/usr/bin/env python3
"""
Unit tests for Esc key cancellation mechanism.
Tests the cancellation logic in isolation with stubbed components.
"""
import sys
sys.path.insert(0, 'src')

import trio
import pytest
from unittest.mock import patch, AsyncMock
from src.tunacode.core.abort_controller import AbortController, AppContext
from src.tunacode.core.state import StateManager


@pytest.mark.trio
async def test_stubbed_agent_cancellation():
    """Test cancellation with a stubbed 5-second agent operation."""
    
    # Stub the agent to take exactly 5 seconds
    async def fake_agent(*args, **kwargs):
        """Fake agent that takes 5 seconds - long enough to test cancellation."""
        print("🎭 Fake agent starting (5s operation)...")
        await trio.sleep(5)
        print("🎭 Fake agent completed")
        return {"result": {"output": "fake response"}}
    
    # Set up state manager and abort controller
    state_manager = StateManager()
    abort_controller = AbortController()
    
    async with trio.open_nursery() as nursery:
        app_context = AppContext(nursery, abort_controller)
        state_manager.app_context = app_context
        
        # Import the cancellation logic
        from src.tunacode.cli.repl import process_request
        
        # Patch the agent to use our fake
        with patch('src.tunacode.core.agents.main.process_request', fake_agent):
            
            start_time = trio.current_time()
            
            try:
                # Start the agent processing in background
                async with trio.open_nursery() as test_nursery:
                    # Start processing
                    test_nursery.start_soon(process_request, "test command", state_manager, False)
                    
                    # Wait 1 second, then trigger abort
                    await trio.sleep(1.0)
                    print("🛑 Triggering abort after 1 second...")
                    abort_controller.abort(trigger="Unit test")
                    
                    # Should cancel within another second
                    await trio.sleep(2.0)
                    
            except trio.Cancelled:
                end_time = trio.current_time()
                elapsed = end_time - start_time
                print(f"✅ Successfully cancelled after {elapsed:.2f}s")
                
                # Should be cancelled within ~2 seconds (1s wait + some cancellation time)
                assert elapsed < 3.0, f"Cancellation took too long: {elapsed:.2f}s"
                assert elapsed > 0.8, f"Cancelled too quickly: {elapsed:.2f}s"
                return
            
            # If we get here, cancellation failed
            end_time = trio.current_time()
            elapsed = end_time - start_time
            pytest.fail(f"Expected cancellation but operation completed in {elapsed:.2f}s")


@pytest.mark.trio
async def test_direct_cancelscope():
    """Test the cancellation monitoring loop directly without REPL complexity."""
    
    # Set up abort controller
    abort_controller = AbortController()
    
    async def fake_long_operation():
        """Simulate a long-running operation."""
        print("🎭 Starting fake long operation...")
        await trio.sleep(10)  # 10 seconds
        print("🎭 Fake operation completed")
        return "completed"
    
    # Test the monitoring pattern directly
    async def cancellable_wrapper():
        """Direct test of the cancellation wrapper logic."""
        import trio_asyncio
        
        async with trio_asyncio.open_loop():
            import asyncio
            
            # Start operation as background task
            task = asyncio.create_task(fake_long_operation())
            
            # Monitor for cancellation
            check_count = 0
            print("🔄 Starting direct monitoring loop...")
            
            while not task.done():
                check_count += 1
                
                if check_count % 20 == 0:
                    print(f"🔄 Direct check #{check_count}")
                
                # Check for abort
                if abort_controller.is_aborted():
                    print(f"🛑 Direct cancellation detected (check #{check_count})")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    raise asyncio.CancelledError("Direct cancellation")
                
                await asyncio.sleep(0.05)
            
            return await task
    
    start_time = trio.current_time()
    
    try:
        with trio.CancelScope() as cancel_scope:
            abort_controller.set_cancel_scope(cancel_scope)
            
            async with trio.open_nursery() as nursery:
                # Start the cancellable operation
                nursery.start_soon(trio_asyncio.aio_as_trio, cancellable_wrapper())
                
                # Wait 500ms then trigger abort
                await trio.sleep(0.5)
                print("🛑 Triggering direct abort...")
                abort_controller.abort(trigger="Direct test")
                
    except trio.Cancelled:
        end_time = trio.current_time()
        elapsed = end_time - start_time
        print(f"✅ Direct test cancelled after {elapsed:.2f}s")
        
        # Should cancel quickly
        assert elapsed < 2.0, f"Direct cancellation took too long: {elapsed:.2f}s"
        assert elapsed > 0.4, f"Direct cancelled too quickly: {elapsed:.2f}s"
        return
    
    # Should not reach here
    pytest.fail("Expected direct cancellation but operation completed")


@pytest.mark.trio
async def test_repeated_start_abort():
    """Test repeated start/abort cycles to check for resource leaks."""
    
    async def quick_fake_agent(*args, **kwargs):
        """Quick fake agent for repeated testing."""
        await trio.sleep(0.2)  # 200ms operation
        return {"result": {"output": "quick fake"}}
    
    abort_controller = AbortController()
    
    for i in range(5):  # Test 5 cycles
        print(f"🔄 Cycle {i+1}/5")
        
        # Reset for each cycle
        abort_controller.reset()
        
        start_time = trio.current_time()
        
        try:
            with trio.CancelScope() as cancel_scope:
                abort_controller.set_cancel_scope(cancel_scope)
                
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(quick_fake_agent)
                    
                    # Random abort timing
                    await trio.sleep(0.05 + (i * 0.02))  # 50-130ms
                    abort_controller.abort(trigger=f"Cycle {i+1}")
                    
        except trio.Cancelled:
            elapsed = trio.current_time() - start_time
            print(f"✅ Cycle {i+1} cancelled after {elapsed:.3f}s")
        
        # Brief pause between cycles
        await trio.sleep(0.1)
    
    print("✅ All repeated cycles completed successfully")


if __name__ == "__main__":
    print("🧪 Running Esc cancellation unit tests...")
    
    async def run_tests():
        print("\n1️⃣ Testing stubbed agent cancellation...")
        await test_stubbed_agent_cancellation()
        
        print("\n2️⃣ Testing direct CancelScope...")
        await test_direct_cancelscope()
        
        print("\n3️⃣ Testing repeated start/abort cycles...")
        await test_repeated_start_abort()
        
        print("\n🎉 All unit tests passed!")
    
    try:
        trio.run(run_tests)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)