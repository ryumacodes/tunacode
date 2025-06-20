"""Test to verify that file operations actually use multiple threads."""

import asyncio
import threading
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tunacode.tools.read_file import ReadFileTool
from tunacode.tools.list_dir import ListDirTool


class TestActualParallelism:
    """Verify that our async operations actually run in parallel using threads."""

    @pytest.mark.asyncio
    async def test_read_file_uses_multiple_threads(self, tmp_path):
        """Confirm that multiple read_file calls use different threads."""
        # Track which threads are used
        thread_ids = set()
        original_open = open
        
        def tracking_open(*args, **kwargs):
            # Record the thread ID when open() is called
            thread_ids.add(threading.current_thread().ident)
            # Add a small delay to ensure overlap
            time.sleep(0.1)
            return original_open(*args, **kwargs)
        
        # Create test files
        files = []
        for i in range(3):
            file_path = tmp_path / f"test{i}.txt"
            file_path.write_text(f"Content {i}" * 1000)
            files.append(str(file_path))
        
        # Patch open to track thread usage
        with patch('builtins.open', side_effect=tracking_open):
            tool = ReadFileTool()
            
            # Read files in parallel
            start = time.time()
            results = await asyncio.gather(
                tool.execute(filepath=files[0]),
                tool.execute(filepath=files[1]),
                tool.execute(filepath=files[2])
            )
            duration = time.time() - start
        
        # Verify results
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)  # Tool returns content directly
        
        # CRITICAL: Verify multiple threads were used
        print(f"\nThread IDs used: {thread_ids}")
        print(f"Main thread ID: {threading.main_thread().ident}")
        print(f"Current thread ID: {threading.current_thread().ident}")
        print(f"Number of unique threads: {len(thread_ids)}")
        print(f"Total duration: {duration:.3f}s")
        
        # We should see multiple thread IDs (not just the main thread)
        assert len(thread_ids) >= 2, f"Expected multiple threads, but only got {len(thread_ids)} thread(s)"
        
        # The operations should overlap (take ~0.1s, not 0.3s)
        assert duration < 0.2, f"Operations didn't run in parallel! Took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_list_dir_uses_multiple_threads(self, tmp_path):
        """Confirm that multiple list_dir calls use different threads."""
        thread_ids = set()
        original_scandir = os.scandir
        
        def tracking_scandir(*args, **kwargs):
            # Record the thread ID when scandir is called
            thread_ids.add(threading.current_thread().ident)
            # Add delay to ensure overlap
            time.sleep(0.1)
            return original_scandir(*args, **kwargs)
        
        # Create test directories
        dirs = []
        for i in range(3):
            dir_path = tmp_path / f"dir{i}"
            dir_path.mkdir()
            # Add some files
            for j in range(5):
                (dir_path / f"file{j}.txt").write_text("content")
            dirs.append(str(dir_path))
        
        # Patch scandir to track thread usage
        with patch('os.scandir', side_effect=tracking_scandir):
            tool = ListDirTool()
            
            # List directories in parallel
            start = time.time()
            results = await asyncio.gather(
                tool.execute(directory=dirs[0]),
                tool.execute(directory=dirs[1]),
                tool.execute(directory=dirs[2])
            )
            duration = time.time() - start
        
        # Verify results
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)  # Tool returns content directly
        
        # Verify multiple threads were used
        print(f"\nThread IDs used: {thread_ids}")
        print(f"Number of unique threads: {len(thread_ids)}")
        print(f"Total duration: {duration:.3f}s")
        
        assert len(thread_ids) >= 2, f"Expected multiple threads, but only got {len(thread_ids)} thread(s)"
        assert duration < 0.2, f"Operations didn't run in parallel! Took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_mixed_operations_use_thread_pool(self, tmp_path):
        """Test that mixed read_file and list_dir operations share the thread pool."""
        all_thread_ids = set()
        
        # Track threads for both operations
        original_open = open
        original_scandir = os.scandir
        
        def tracking_open(*args, **kwargs):
            all_thread_ids.add(('open', threading.current_thread().ident))
            time.sleep(0.05)
            return original_open(*args, **kwargs)
        
        def tracking_scandir(*args, **kwargs):
            all_thread_ids.add(('scandir', threading.current_thread().ident))
            time.sleep(0.05)
            return original_scandir(*args, **kwargs)
        
        # Create test data
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "subfile.txt").write_text("sub content")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        
        # Patch both operations
        with patch('builtins.open', side_effect=tracking_open), \
             patch('os.scandir', side_effect=tracking_scandir):
            
            read_tool = ReadFileTool()
            list_tool = ListDirTool()
            
            # Execute mixed operations in parallel
            start = time.time()
            results = await asyncio.gather(
                read_tool.execute(filepath=str(file1)),
                list_tool.execute(directory=str(dir1)),
                read_tool.execute(filepath=str(file2)),
                list_tool.execute(directory=str(tmp_path))
            )
            duration = time.time() - start
        
        # Extract unique thread IDs
        unique_thread_ids = {tid for _, tid in all_thread_ids}
        operations = [op for op, _ in all_thread_ids]
        
        print(f"\nOperations and threads: {all_thread_ids}")
        print(f"Unique thread IDs: {unique_thread_ids}")
        print(f"Number of unique threads: {len(unique_thread_ids)}")
        print(f"Operations performed: {operations}")
        print(f"Total duration: {duration:.3f}s")
        
        # Should use multiple threads
        assert len(unique_thread_ids) >= 2, "Should use multiple threads"
        
        # Should have both types of operations
        assert 'open' in operations and 'scandir' in operations
        
        # Should complete faster than sequential
        assert duration < 0.15, f"Mixed operations didn't parallelize! Took {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_thread_pool_limits(self, tmp_path):
        """Verify the thread pool has reasonable limits."""
        thread_ids = set()
        active_threads = []
        max_concurrent = 0
        
        original_open = open
        
        def tracking_open(*args, **kwargs):
            thread_id = threading.current_thread().ident
            thread_ids.add(thread_id)
            
            # Track concurrent threads
            active_threads.append(thread_id)
            nonlocal max_concurrent
            max_concurrent = max(max_concurrent, len(set(active_threads)))
            
            # Simulate work
            time.sleep(0.1)
            
            # Remove from active
            active_threads.remove(thread_id)
            
            return original_open(*args, **kwargs)
        
        # Create many test files
        files = []
        for i in range(20):  # More than typical thread pool size
            file_path = tmp_path / f"test{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(str(file_path))
        
        with patch('builtins.open', side_effect=tracking_open):
            tool = ReadFileTool()
            
            # Read all files in parallel
            tasks = [tool.execute(filepath=f) for f in files]
            results = await asyncio.gather(*tasks)
        
        print(f"\nTotal unique threads used: {len(thread_ids)}")
        print(f"Max concurrent threads: {max_concurrent}")
        print(f"CPU count: {os.cpu_count()}")
        
        # Should use multiple threads but not unlimited
        assert 2 <= len(thread_ids) <= os.cpu_count() * 5  # asyncio default is min(32, cpu_count + 4)
        assert max_concurrent <= len(thread_ids)


if __name__ == "__main__":
    # Run a quick demo
    import sys
    
    async def demo():
        test = TestActualParallelism()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            print("Testing read_file parallelism...")
            await test.test_read_file_uses_multiple_threads(tmp_path)
            
            print("\n" + "="*50 + "\n")
            
            print("Testing list_dir parallelism...")
            await test.test_list_dir_uses_multiple_threads(tmp_path)
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo())
    else:
        pytest.main([__file__, "-v"])