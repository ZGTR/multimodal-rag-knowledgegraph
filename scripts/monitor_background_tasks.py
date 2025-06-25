#!/usr/bin/env python3
"""
Background Task Monitoring Script

This script helps you monitor and print background task logs in real-time.
It can be used to:
1. Monitor background task execution
2. Set different log levels
3. Test background task logging
4. View detailed processing logs
"""

import sys
import os
import time
import subprocess
import threading
import queue
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bootstrap.logger import get_logger, enable_debug_logging, enable_info_logging
from src.worker.ingest_worker import main as worker_main
from src.ingest.youtube import YouTubeVideoSource

logger = get_logger("background_monitor")

class BackgroundTaskMonitor:
    """Monitor background tasks and their logs"""
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.is_monitoring = False
    
    def start_monitoring(self, log_level="INFO"):
        """Start monitoring background tasks"""
        print(f"🔍 Starting Background Task Monitor (Log Level: {log_level})")
        print("=" * 60)
        
        if log_level.upper() == "DEBUG":
            enable_debug_logging()
        else:
            enable_info_logging()
        
        self.is_monitoring = True
        
        # Start log consumer thread
        log_thread = threading.Thread(target=self._consume_logs)
        log_thread.daemon = True
        log_thread.start()
        
        return self
    
    def _consume_logs(self):
        """Consume logs from the queue and print them"""
        while self.is_monitoring:
            try:
                log_entry = self.log_queue.get(timeout=1)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {log_entry}")
            except queue.Empty:
                continue
    
    def test_background_task_logging(self, video_id="dQw4w9WgXcQ"):
        """Test background task logging with a sample video"""
        print(f"\n🎬 Testing Background Task Logging")
        print(f"Video ID: {video_id}")
        print("-" * 40)
        
        try:
            # Simulate background task execution
            logger.info("Starting background task test")
            
            # Test video processing
            video_source = YouTubeVideoSource()
            for video_item in video_source.fetch_video([video_id]):
                logger.info(f"Video processed: {video_item.title}")
                logger.info(f"Segments: {len(video_item.segments)}")
                logger.info(f"Duration: {video_item.duration:.1f}s")
                
                # Log segment processing
                for i, segment in enumerate(video_item.segments[:3], 1):
                    logger.debug(f"Segment {i}: {segment.start_time:.1f}s - {segment.end_time:.1f}s")
                    if segment.entities:
                        logger.debug(f"  Entities: {segment.entities}")
                
                break  # Just process first video for demo
            
            logger.info("Background task test completed successfully")
            
        except Exception as e:
            logger.error(f"Background task test failed: {e}")
    
    def monitor_worker_execution(self, video_urls=None):
        """Monitor actual worker execution"""
        if not video_urls:
            video_urls = ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
        
        print(f"\n⚙️  Monitoring Worker Execution")
        print(f"Videos: {video_urls}")
        print("-" * 40)
        
        try:
            # Set up worker arguments
            sys.argv = ["worker"] + ["--videos"] + video_urls
            
            # Execute worker
            logger.info("Starting worker execution")
            worker_main()
            logger.info("Worker execution completed")
            
        except Exception as e:
            logger.error(f"Worker execution failed: {e}")
    
    def show_log_examples(self):
        """Show examples of what background task logs look like"""
        print("\n📋 Background Task Log Examples")
        print("=" * 40)
        
        examples = [
            "[2024-01-15 10:30:15] INFO api.ingest: Received ingest request: videos=['dQw4w9WgXcQ']",
            "[2024-01-15 10:30:15] INFO api.ingest: Queuing background task: ['python', '-m', 'src.worker.ingest_worker', '--videos', 'dQw4w9WgXcQ']",
            "[2024-01-15 10:30:16] INFO ingest_worker: [JOB] YouTube ingestion started",
            "[2024-01-15 10:30:16] INFO youtube_strategy: Starting YouTube ingestion for 1 items",
            "[2024-01-15 10:30:16] INFO youtube_strategy: Extracted video IDs: ['dQw4w9WgXcQ']",
            "[2024-01-15 10:30:17] INFO youtube: [1/1] Processing video: dQw4w9WgXcQ",
            "[2024-01-15 10:30:17] INFO youtube: [dQw4w9WgXcQ] Step 1/5: Extracting video metadata...",
            "[2024-01-15 10:30:18] INFO youtube: [dQw4w9WgXcQ] Step 2/5: Retrieving transcript...",
            "[2024-01-15 10:30:19] INFO youtube: [dQw4w9WgXcQ] Step 3/5: Processing temporal segments...",
            "[2024-01-15 10:30:20] INFO youtube: [dQw4w9WgXcQ] Step 5/5: Video processing completed in 4.23s",
            "[2024-01-15 10:30:20] INFO ingest_worker: [JOB] YouTube ingestion finished",
            "[2024-01-15 10:30:20] INFO ingest_worker: [JOB] IngestWorker finished successfully"
        ]
        
        for example in examples:
            print(example)
    
    def stop_monitoring(self):
        """Stop monitoring background tasks"""
        self.is_monitoring = False
        print("\n🛑 Background Task Monitor stopped")

def main():
    """Main function to run the background task monitor"""
    print("Background Task Monitor")
    print("=" * 50)
    print("This script helps you monitor and print background task logs.")
    print()
    
    monitor = BackgroundTaskMonitor()
    
    # Show log examples
    monitor.show_log_examples()
    
    # Test with different log levels
    print("\n" + "=" * 50)
    print("Testing Background Task Logging")
    print("=" * 50)
    
    # Test with INFO level
    print("\n1. Testing with INFO level logging:")
    monitor.start_monitoring("INFO")
    monitor.test_background_task_logging()
    monitor.stop_monitoring()
    
    # Test with DEBUG level
    print("\n2. Testing with DEBUG level logging:")
    monitor.start_monitoring("DEBUG")
    monitor.test_background_task_logging()
    monitor.stop_monitoring()
    
    print("\n" + "=" * 50)
    print("Background Task Monitor Demo Completed!")
    print("=" * 50)
    print("\nTo monitor real background tasks:")
    print("1. Start the API server: uvicorn src.api.main:app --reload")
    print("2. Make API calls to trigger background tasks")
    print("3. Watch the logs in the API server terminal")
    print("\nTo test worker directly:")
    print("python -m src.worker.ingest_worker --videos dQw4w9WgXcQ")

if __name__ == "__main__":
    main() 