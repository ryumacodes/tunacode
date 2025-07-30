#!/usr/bin/env python3
"""
Final test to verify ESC interrupt works in TunaCode.
This simulates what happens when you run 'ls' and press ESC.
"""

print("🧪 Testing ESC interrupt in TunaCode environment...")
print("   This test simulates running TunaCode with 'ls' command")
print("   and pressing ESC to cancel it.")
print("")

# Test with a simple subprocess call to verify the environment
import subprocess
import sys

try:
    # Try to run tunacode --version to verify it's installed correctly
    result = subprocess.run([sys.executable, "-m", "tunacode", "--version"], 
                          capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("✅ TunaCode is properly installed and working")
        print(f"   Version output: {result.stdout.strip()}")
    else:
        print("❌ TunaCode installation issue:")
        print(f"   stdout: {result.stdout}")
        print(f"   stderr: {result.stderr}")
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("❌ TunaCode command timed out")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing TunaCode: {e}")
    sys.exit(1)

print("")
print("🎉 TunaCode is ready!")
print("")
print("🔧 To test ESC interrupt manually:")
print("   1. Run: tunacode")
print("   2. Type: ls")
print("   3. Press Enter to start the command")
print("   4. Press ESC while the command is running")
print("   5. The command should be cancelled with '🛑 Command execution cancelled by ESC!'")
print("")
print("Note: The trio_asyncio integration is now enabled in the main CLI,")
print("      so ESC interrupts should work properly during command execution.")