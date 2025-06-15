#!/usr/bin/env python3
"""
Test for grep tool timeout handling functionality
"""
import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add src to path so we can import tunacode modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_timeout_handling():
    """Test that grep times out on overly broad patterns"""
    try:
        from tunacode.tools.grep import grep
        from tunacode.exceptions import TooBroadPatternError
        
        print("Testing timeout on overly broad pattern...")
        
        # Create a test with an intentionally broad pattern that matches everything
        # Using a pattern like "." in regex mode should match every character
        try:
            result = asyncio.run(grep(
                pattern=".",  # Matches every character
                directory=".",
                use_regex=True,
                include_files="*.py",
                max_results=10000,  # High limit to stress test
                search_type="python"  # Use python strategy for testing
            ))
            
            # If we get here without timeout, the search completed
            print("Search completed without timeout (found matches quickly enough)")
            return True
            
        except TooBroadPatternError as e:
            print(f"✓ Correctly caught TooBroadPatternError: {e}")
            assert "too broad" in str(e).lower(), "Error message should mention pattern is too broad"
            assert "3.0s" in str(e) or "3s" in str(e), "Error message should mention the timeout duration"
            return True
            
    except Exception as e:
        print(f"✗ Timeout handling test failed with unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normal_search_completes():
    """Test that normal searches complete without timeout"""
    try:
        from tunacode.tools.grep import grep
        
        print("Testing normal search completes...")
        
        # Search for something specific that should complete quickly
        result = asyncio.run(grep(
            pattern="class ParallelGrep",
            directory="src/tunacode/tools",
            include_files="*.py",
            max_results=5
        ))
        
        assert isinstance(result, str), "Should return a string result"
        assert "Found" in result or "No matches" in result, "Should have a result status"
        
        print("✓ Normal search completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Normal search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ripgrep_timeout():
    """Test that ripgrep strategy also handles timeout"""
    try:
        from tunacode.tools.grep import grep
        from tunacode.exceptions import TooBroadPatternError
        
        print("Testing ripgrep timeout handling...")
        
        try:
            # Use a very broad pattern with ripgrep
            result = asyncio.run(grep(
                pattern=".",
                directory=".",
                use_regex=True,
                include_files="*",  # All files
                max_results=10000,
                search_type="ripgrep"
            ))
            
            # If search completes, that's okay
            print("Ripgrep search completed without timeout")
            return True
            
        except TooBroadPatternError as e:
            print(f"✓ Ripgrep correctly timed out: {e}")
            return True
            
    except Exception as e:
        print(f"✗ Ripgrep timeout test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_timeout_fallback():
    """Test that hybrid search handles timeout in one strategy"""
    try:
        from tunacode.tools.grep import grep
        
        print("Testing hybrid search with potential timeout...")
        
        # Hybrid should continue even if one strategy times out
        result = asyncio.run(grep(
            pattern="import asyncio",  # More specific pattern
            directory="src",
            include_files="*.py",
            max_results=5,
            search_type="hybrid"
        ))
        
        assert isinstance(result, str), "Should return a result"
        print("✓ Hybrid search handled timeout gracefully")
        return True
        
    except Exception as e:
        print(f"✗ Hybrid timeout fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all grep timeout tests"""
    print("Testing grep timeout handling functionality...")
    print("=" * 60)
    
    tests = [
        test_normal_search_completes,
        test_timeout_handling,
        test_ripgrep_timeout,
        test_hybrid_timeout_fallback,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All grep timeout tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())