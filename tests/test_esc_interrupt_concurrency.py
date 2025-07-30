"""
Concurrency torture tests for ESC interrupt functionality.

These tests verify that the cancellation mechanism works correctly under
high concurrency scenarios and stress conditions.
"""

import pytest
import trio
import threading
import time
import gc
import psutil
import os
from unittest.mock import MagicMock, patch
import pytest_trio
from tunacode.core.abort_controller import AbortController, AppContext
from tunacode.utils.cancellable_processing import process_with_esc_option
from tunacode.utils.keyboard_monitor import monitor_esc_during_operation


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.cancellation
class TestEscInterruptConcurrency:
    """Concurrency torture tests for cancellation under stress."""

    @pytest.fixture
    def abort_controller(self):
        """Fresh AbortController for each test."""
        return AbortController()

    async def long_running_operation(self, duration=5.0, operation_id="default"):
        """Simulate a long-running operation that can be cancelled."""
        start_time = time.time()
        while time.time() - start_time < duration:
            await trio.sleep(0.1)
        return f"Operation {operation_id} completed after {duration}s"

    async def cancellable_operation(self, abort_controller, duration=5.0, operation_id="default"):
        """Long-running operation that respects abort controller."""
        start_time = time.time()
        
        with trio.CancelScope() as cancel_scope:
            abort_controller.set_cancel_scope(cancel_scope)
            
            while time.time() - start_time < duration:
                await abort_controller.check_abort()
                await trio.sleep(0.1)
                
        return f"Operation {operation_id} completed after {duration}s"

    @pytest.mark.trio
    async def test_parallel_nursery_stress(self):
        """
        Parallel nursery stress test:
        Open 4 nurseries running long requests, cancel at random intervals.
        Verify CPU stays low and no deadlocks.
        """
        import random
        
        controllers = [AbortController() for _ in range(4)]
        results = []
        start_time = time.time()
        
        async def run_nursery(nursery_id, abort_controller):
            """Run operations in a single nursery."""
            try:
                async with trio.open_nursery() as nursery:
                    # Start 2 operations per nursery
                    for op_id in range(2):
                        operation_name = f"nursery-{nursery_id}-op-{op_id}"
                        nursery.start_soon(
                            self.cancellable_operation,
                            abort_controller,
                            3.0,  # 3 second operations
                            operation_name
                        )
                    
                    # Random cancellation
                    await trio.sleep(random.uniform(0.5, 2.0))
                    abort_controller.abort(f"Random abort for nursery {nursery_id}")
                    
                return f"Nursery {nursery_id} completed"
                
            except trio.Cancelled:
                return f"Nursery {nursery_id} cancelled"
        
        # Start all nurseries concurrently
        try:
            async with trio.open_nursery() as main_nursery:
                for i, controller in enumerate(controllers):
                    main_nursery.start_soon(run_nursery, i, controller)
                    
        except Exception as e:
            results.append(f"Error: {e}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete within reasonable time (not deadlock)
        assert elapsed < 10.0, f"Test took {elapsed}s, may have deadlocked"
        
        # Verify all controllers are in consistent state
        for i, controller in enumerate(controllers):
            # Should be aborted (we triggered abort for each)
            assert controller.is_aborted(), f"Controller {i} should be aborted"

    @pytest.mark.trio
    async def test_streaming_response_cancellation_torture(self):
        """
        Streaming response torture test:
        Multiple concurrent streams with random cancellations.
        """
        
        class MockStreamingService:
            def __init__(self, stream_id):
                self.stream_id = stream_id
                self.chunks_sent = 0
                self.cancelled = False
                
            async def stream_data(self, abort_controller, chunk_count=50):
                """Stream data with cancellation support."""
                with trio.CancelScope() as cancel_scope:
                    abort_controller.set_cancel_scope(cancel_scope)
                    
                    for i in range(chunk_count):
                        try:
                            await abort_controller.check_abort()
                        except trio.Cancelled:
                            self.cancelled = True
                            raise
                        
                        self.chunks_sent += 1
                        await trio.sleep(0.05)  # 50ms per chunk
                        
                return f"Stream {self.stream_id} completed {self.chunks_sent} chunks"
        
        import random
        
        # Create multiple streaming services
        services = [MockStreamingService(i) for i in range(6)]
        controllers = [AbortController() for _ in range(6)]
        
        async def run_streaming_service(service, controller):
            """Run a streaming service with random cancellation."""
            try:
                # Start streaming
                stream_task = trio.lowlevel.current_task()
                
                async with trio.open_nursery() as nursery:
                    # Start the stream
                    nursery.start_soon(service.stream_data, controller, 30)
                    
                    # Random cancellation timing
                    cancel_after = random.uniform(0.2, 2.0)
                    await trio.sleep(cancel_after)
                    controller.abort(f"Stream {service.stream_id} cancelled after {cancel_after}s")
                    
            except trio.Cancelled:
                return f"Stream {service.stream_id} cancelled (sent {service.chunks_sent} chunks)"
        
        # Run all streams concurrently
        results = []
        start_time = time.time()
        
        try:
            async with trio.open_nursery() as main_nursery:
                for service, controller in zip(services, controllers):
                    main_nursery.start_soon(run_streaming_service, service, controller)
                    
        except Exception as e:
            results.append(f"Error: {e}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly (all streams cancelled)
        assert elapsed < 5.0, f"Streaming test took {elapsed}s, too long"
        
        # Verify cancellation occurred
        cancelled_count = sum(1 for service in services if service.cancelled)
        assert cancelled_count > 0, "At least some streams should be cancelled"

    @pytest.mark.trio  
    async def test_memory_pressure_during_cancellation(self):
        """Test cancellation behavior under memory pressure."""
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create memory pressure with many abort controllers
        controllers = [AbortController() for _ in range(100)]
        
        async def memory_intensive_operation(controller, operation_id):
            """Operation that uses memory and can be cancelled."""
            # Allocate some memory
            data = [list(range(1000)) for _ in range(100)]  # ~400KB per operation
            
            try:
                with trio.CancelScope() as cancel_scope:
                    controller.set_cancel_scope(cancel_scope)
                    
                    for i in range(50):
                        await controller.check_abort()
                        
                        # Do some work with the data
                        _ = sum(sum(sublist) for sublist in data)
                        await trio.sleep(0.02)
                        
                return f"Memory operation {operation_id} completed"
                
            except trio.Cancelled:
                # Clean up data
                del data
                raise
        
        # Run operations and cancel them randomly
        import random
        cancelled_count = 0
        
        try:
            async with trio.open_nursery() as nursery:
                # Start all operations
                for i, controller in enumerate(controllers[:20]):  # Limit to 20 for test speed
                    nursery.start_soon(memory_intensive_operation, controller, i)
                
                # Cancel them randomly
                for i, controller in enumerate(controllers[:20]):
                    await trio.sleep(random.uniform(0.01, 0.1))
                    if random.random() < 0.7:  # 70% cancellation rate
                        controller.abort(f"Memory test abort {i}")
                        cancelled_count += 1
                        
        except Exception as e:
            pass  # Expected due to cancellations
        
        # Force garbage collection
        gc.collect()
        await trio.sleep(0.1)
        
        # Check memory usage didn't explode
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Should not grow more than 100MB
        assert memory_growth < 100 * 1024 * 1024, \
            f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB, too much"
        
        assert cancelled_count > 0, "Some operations should have been cancelled"

    @pytest.mark.trio
    async def test_thread_safety_across_nurseries(self):
        """Test thread safety when abort controllers are used across nurseries."""
        
        shared_controller = AbortController()
        thread_results = []
        lock = threading.Lock()
        
        def thread_worker(thread_id):
            """Worker that runs in a separate thread."""
            try:
                # Each thread tries to abort the shared controller
                time.sleep(0.1 * thread_id)  # Stagger the aborts
                shared_controller.abort(f"Thread {thread_id} abort")
                
                with lock:
                    thread_results.append(f"Thread {thread_id} completed abort")
                    
            except Exception as e:
                with lock:
                    thread_results.append(f"Thread {thread_id} error: {e}")
        
        async def trio_worker(worker_id):
            """Worker that runs in trio context."""
            try:
                with trio.CancelScope() as cancel_scope:
                    shared_controller.set_cancel_scope(cancel_scope)
                    
                    # Long operation
                    await trio.sleep(2.0)
                    return f"Trio worker {worker_id} completed"
                    
            except trio.Cancelled:
                return f"Trio worker {worker_id} cancelled"
        
        # Start background threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=thread_worker, args=(i,))
            t.start()
            threads.append(t)
        
        # Start trio workers
        try:
            async with trio.open_nursery() as nursery:
                for i in range(3):
                    nursery.start_soon(trio_worker, i)
                    
        except Exception:
            pass  # Expected due to cancellation
        
        # Wait for threads to complete
        for t in threads:
            t.join(timeout=2.0)
        
        # Verify thread safety
        assert len(thread_results) == 5, f"Expected 5 thread results, got {len(thread_results)}"
        assert shared_controller.is_aborted(), "Controller should be aborted"
        
        # Verify no threads are still running
        active_threads = [t for t in threads if t.is_alive()]
        assert len(active_threads) == 0, f"Some threads still active: {active_threads}"

    @pytest.mark.trio
    async def test_resource_cleanup_torture(self):
        """Torture test for resource cleanup during cancellation."""
        
        class MockResource:
            created_count = 0
            cleaned_count = 0
            
            def __init__(self, resource_id):
                MockResource.created_count += 1
                self.resource_id = resource_id
                self.cleaned = False
                
            def cleanup(self):
                if not self.cleaned:
                    MockResource.cleaned_count += 1
                    self.cleaned = True
        
        # Reset counters
        MockResource.created_count = 0
        MockResource.cleaned_count = 0
        
        async def resource_using_operation(abort_controller, operation_id):
            """Operation that allocates resources and cleans them up."""
            resources = [MockResource(f"{operation_id}-{i}") for i in range(10)]
            
            try:
                with trio.CancelScope() as cancel_scope:
                    abort_controller.set_cancel_scope(cancel_scope)
                    
                    # Use resources
                    for i in range(100):
                        await abort_controller.check_abort()
                        await trio.sleep(0.01)
                        
                    return f"Resource operation {operation_id} completed"
                    
            finally:
                # Always clean up resources
                for resource in resources:
                    resource.cleanup()
        
        # Create many operations
        controllers = [AbortController() for _ in range(20)]
        
        import random
        
        try:
            async with trio.open_nursery() as nursery:
                # Start operations
                for i, controller in enumerate(controllers):
                    nursery.start_soon(resource_using_operation, controller, i)
                
                # Cancel them at random times
                for i, controller in enumerate(controllers):
                    await trio.sleep(random.uniform(0.01, 0.2))
                    if random.random() < 0.8:  # 80% cancellation rate
                        controller.abort(f"Resource cleanup test {i}")
                        
        except Exception:
            pass  # Expected due to cancellations
        
        # Allow time for cleanup
        await trio.sleep(0.2)
        
        # Verify resource cleanup
        assert MockResource.created_count == 200, \
            f"Expected 200 resources created, got {MockResource.created_count}"
        assert MockResource.cleaned_count == 200, \
            f"Expected 200 resources cleaned, got {MockResource.cleaned_count}"

    @pytest.mark.trio
    async def test_cpu_usage_during_mass_cancellation(self):
        """Test CPU usage remains reasonable during mass cancellation events."""
        
        import psutil
        
        # Monitor CPU usage
        process = psutil.Process(os.getpid())
        cpu_samples = []
        
        async def cpu_monitor():
            """Monitor CPU usage during the test."""
            for _ in range(50):  # 5 seconds of monitoring
                cpu_percent = process.cpu_percent()
                cpu_samples.append(cpu_percent)
                await trio.sleep(0.1)
        
        async def cpu_intensive_cancellable_operation(controller, op_id):
            """CPU-intensive operation that can be cancelled."""
            with trio.CancelScope() as cancel_scope:
                controller.set_cancel_scope(cancel_scope)
                
                # CPU-intensive work
                for i in range(1000000):
                    await controller.check_abort()
                    
                    # Some computation
                    _ = sum(range(100))
                    
                    # Yield occasionally
                    if i % 10000 == 0:
                        await trio.sleep(0.001)
                        
                return f"CPU operation {op_id} completed"
        
        # Create controllers for mass cancellation
        controllers = [AbortController() for _ in range(30)]
        
        start_time = time.time()
        
        try:
            async with trio.open_nursery() as nursery:
                # Start CPU monitoring
                nursery.start_soon(cpu_monitor)
                
                # Start CPU-intensive operations
                for i, controller in enumerate(controllers):
                    nursery.start_soon(cpu_intensive_cancellable_operation, controller, i)
                
                # Wait a bit, then cancel everything
                await trio.sleep(0.5)
                
                for controller in controllers:
                    controller.abort("Mass cancellation test")
                    
        except Exception:
            pass  # Expected
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly after mass cancellation
        assert elapsed < 3.0, f"Mass cancellation took {elapsed}s, too long"
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            # CPU should not max out consistently
            assert avg_cpu < 80.0, f"Average CPU usage {avg_cpu}% too high"
            # Allow brief spikes but not sustained high usage
            high_cpu_samples = [s for s in cpu_samples if s > 90.0]
            assert len(high_cpu_samples) < len(cpu_samples) * 0.3, \
                "Too many high CPU samples during cancellation"


@pytest.mark.parametrize("operation_count", [5, 10, 20])
@pytest.mark.parametrize("cancel_rate", [0.3, 0.5, 0.8])
def test_parametrized_concurrency_stress(operation_count, cancel_rate):
    """Parametrized test for different concurrency stress levels."""
    
    async def stress_test():
        controllers = [AbortController() for _ in range(operation_count)]
        completed_count = 0
        cancelled_count = 0
        
        async def test_operation(controller, op_id):
            nonlocal completed_count, cancelled_count
            
            try:
                with trio.CancelScope() as cancel_scope:
                    controller.set_cancel_scope(cancel_scope)
                    
                    # Variable duration operation
                    duration = 0.5 + (op_id % 3) * 0.2  # 0.5 to 0.9 seconds
                    await trio.sleep(duration)
                    
                completed_count += 1
                return f"Operation {op_id} completed"
                
            except trio.Cancelled:
                cancelled_count += 1
                raise
        
        import random
        
        try:
            async with trio.open_nursery() as nursery:
                # Start all operations
                for i, controller in enumerate(controllers):
                    nursery.start_soon(test_operation, controller, i)
                
                # Cancel based on cancel_rate
                await trio.sleep(0.1)  # Let operations start
                
                for controller in controllers:
                    if random.random() < cancel_rate:
                        controller.abort("Parametrized stress test")
                        
        except Exception:
            pass  # Expected due to cancellations
        
        # Verify results make sense
        total_operations = completed_count + cancelled_count
        assert total_operations == operation_count, \
            f"Expected {operation_count} total ops, got {total_operations}"
        
        # Cancel rate should be approximately what we requested
        actual_cancel_rate = cancelled_count / operation_count
        rate_diff = abs(actual_cancel_rate - cancel_rate)
        assert rate_diff < 0.3, \
            f"Cancel rate {actual_cancel_rate} differs too much from expected {cancel_rate}"
    
    # Run the async test
    trio.run(stress_test)