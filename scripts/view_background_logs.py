#!/usr/bin/env python3
"""
Simple Background Task Log Viewer

This script provides a simple way to view background task logs in real-time.
"""

import sys
import os
import time
import subprocess
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bootstrap.logger import enable_debug_logging, enable_info_logging

def print_usage():
    """Print usage instructions"""
    print("Background Task Log Viewer")
    print("=" * 40)
    print("Usage:")
    print("  python scripts/view_background_logs.py [debug|info]")
    print()
    print("Examples:")
    print("  python scripts/view_background_logs.py debug  # Enable debug logging")
    print("  python scripts/view_background_logs.py info   # Enable info logging")
    print("  python scripts/view_background_logs.py        # Use default info logging")
    print()
    print("Then in another terminal:")
    print("  1. Start API server: uvicorn src.api.main:app --reload")
    print("  2. Make API calls to trigger background tasks")
    print("  3. Watch logs in the API server terminal")

def test_logging():
    """Test logging functionality"""
    from src.bootstrap.logger import get_logger
    
    logger = get_logger("test_viewer")
    
    print("\n🧪 Testing Logging Output:")
    print("-" * 30)
    
    logger.info("This is an INFO level log message")
    logger.debug("This is a DEBUG level log message")
    logger.warning("This is a WARNING level log message")
    logger.error("This is an ERROR level log message")
    
    print("\n✅ Logging test completed!")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        log_level = sys.argv[1].lower()
        if log_level == "debug":
            enable_debug_logging()
            print("🔍 Debug logging enabled")
        elif log_level == "info":
            enable_info_logging()
            print("ℹ️  Info logging enabled")
        else:
            print(f"❌ Unknown log level: {log_level}")
            print_usage()
            return
    else:
        enable_info_logging()
        print("ℹ️  Info logging enabled (default)")
    
    print_usage()
    test_logging()
    
    print("\n" + "=" * 40)
    print("🎯 Next Steps:")
    print("1. Open a new terminal")
    print("2. Start the API server: uvicorn src.api.main:app --reload")
    print("3. Make API calls to trigger background tasks")
    print("4. Watch the logs in the API server terminal")
    print()
    print("Example API call:")
    print('curl -X POST "http://localhost:8000/ingest" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}\'')

if __name__ == "__main__":
    main() 