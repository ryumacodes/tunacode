#!/usr/bin/env python3
"""
Simple test of keyboard input detection without Trio complexity.
"""
import sys
import termios
import tty
import select

def test_simple_keyboard():
    """Test basic keyboard input detection."""
    
    print("🔧 Testing Basic Keyboard Input Detection")
    print("=" * 50)
    print("Instructions:")
    print("1. Press any key to see it detected")
    print("2. Press ESC to test Esc detection")
    print("3. Press Ctrl+C to exit")
    print()
    
    if not sys.stdin.isatty():
        print("❌ Error: Not running in a terminal")
        return
    
    # Save original terminal settings
    original_settings = termios.tcgetattr(sys.stdin.fileno())
    
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        print("✓ Terminal set to raw mode")
        print("✓ Waiting for key presses...")
        print()
        
        while True:
            # Check if input is available (non-blocking)
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                key_code = ord(key)
                
                print(f"🔑 Key detected: '{key}' (ASCII: {key_code})")
                
                if key_code == 27:  # Esc key
                    print("🎉 ESC KEY DETECTED! - This would trigger cancellation")
                    break
                elif key_code == 3:  # Ctrl+C
                    print("👋 Ctrl+C detected - exiting")
                    break
                else:
                    print(f"   Other key: {repr(key)}")
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by Ctrl+C")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Restore original terminal settings
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_settings)
            print("\n✓ Terminal settings restored")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not restore terminal settings: {e}")

if __name__ == "__main__":
    test_simple_keyboard()