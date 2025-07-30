#!/usr/bin/env python3
"""
Basic test to verify that the tools work correctly in trio_asyncio context.
"""

import trio
import trio_asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tunacode.tools.bash import BashTool
from tunacode.tools.run_command import RunCommandTool


async def test_basic_functionality():
    """Test that both tools work for basic commands."""
    print("🧪 Testing basic tool functionality...")
    
    # Test BashTool
    print("Testing BashTool...")
    bash_tool = BashTool()
    bash_result = await bash_tool.execute("echo 'Hello from bash'", timeout=5)
    print(f"BashTool result: {bash_result}")
    assert "Hello from bash" in bash_result
    assert "Exit Code: 0" in bash_result
    
    # Test RunCommandTool
    print("Testing RunCommandTool...")
    run_tool = RunCommandTool()
    run_result = await run_tool.execute("echo 'Hello from run_command'")
    print(f"RunCommandTool result: {run_result}")
    assert "Hello from run_command" in run_result
    
    print("✅ Both tools work correctly!")
    return True


if __name__ == "__main__":
    print("🚀 Testing basic tool functionality...")
    
    async def main():
        async with trio_asyncio.open_loop():
            return await test_basic_functionality()
    
    try:
        result = trio.run(main)
        if result:
            print("\n🎉 All basic functionality tests passed!")
        else:
            print("\n❌ Basic functionality tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)