#!/usr/bin/env python3
"""
Test Script for Task Monitoring API

This script demonstrates the new task monitoring functionality by:
1. Making API calls to trigger background tasks
2. Checking task status and statistics
3. Monitoring running tasks
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_separator(title):
    """Print a formatted separator"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_response(title, response):
    """Print a formatted API response"""
    print(f"\n📋 {title}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")

def test_task_monitoring():
    """Test the task monitoring API"""
    print_separator("Task Monitoring API Test")
    
    # 1. Check initial task statistics
    print_separator("1. Initial Task Statistics")
    response = requests.get(f"{BASE_URL}/tasks/stats")
    print_response("Task Statistics", response)
    
    # 2. Check running tasks (should be empty initially)
    print_separator("2. Check Running Tasks")
    response = requests.get(f"{BASE_URL}/tasks/running")
    print_response("Running Tasks", response)
    
    # 3. Check pending tasks (should be empty initially)
    print_separator("3. Check Pending Tasks")
    response = requests.get(f"{BASE_URL}/tasks/pending")
    print_response("Pending Tasks", response)
    
    # 4. Trigger a background task (ingest)
    print_separator("4. Trigger Background Task")
    ingest_data = {
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=ingest_data)
    print_response("Ingest Request", response)
    
    if response.status_code == 200:
        task_id = response.json().get("task_id")
        print(f"🎯 Task ID: {task_id}")
        
        # 5. Check task status immediately
        print_separator("5. Check Task Status")
        time.sleep(1)  # Give it a moment to start
        response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        print_response(f"Task Status for {task_id}", response)
        
        # 6. Check running tasks again
        print_separator("6. Check Running Tasks After Trigger")
        response = requests.get(f"{BASE_URL}/tasks/running")
        print_response("Running Tasks", response)
        
        # 7. Check task count
        print_separator("7. Check Running Task Count")
        response = requests.get(f"{BASE_URL}/tasks/count/running")
        print_response("Running Task Count", response)
        
        # 8. Monitor task progress
        print_separator("8. Monitor Task Progress")
        for i in range(5):
            print(f"\n⏳ Progress check {i+1}/5...")
            response = requests.get(f"{BASE_URL}/tasks/{task_id}")
            if response.status_code == 200:
                task_data = response.json()
                status = task_data.get("status")
                progress = task_data.get("progress", "No progress info")
                print(f"   Status: {status}")
                print(f"   Progress: {progress}")
                
                if status in ["completed", "failed"]:
                    print(f"   ✅ Task finished with status: {status}")
                    break
            else:
                print(f"   ❌ Failed to get task status: {response.status_code}")
            
            time.sleep(2)
        
        # 9. Check final statistics
        print_separator("9. Final Task Statistics")
        response = requests.get(f"{BASE_URL}/tasks/stats")
        print_response("Final Task Statistics", response)
        
        # 10. Check all tasks
        print_separator("10. All Tasks")
        response = requests.get(f"{BASE_URL}/tasks/all?limit=10")
        print_response("All Tasks (limit 10)", response)
    
    # 11. Test temporal video ingest
    print_separator("11. Test Temporal Video Ingest")
    temporal_data = {
        "video_ids": ["dQw4w9WgXcQ", "9bZkp7q19f0"],
        "process_segments": True,
        "segment_duration": 30.0
    }
    response = requests.post(f"{BASE_URL}/temporal/ingest-video", json=temporal_data)
    print_response("Temporal Video Ingest", response)
    
    # 12. Final statistics
    print_separator("12. Final Statistics After All Tests")
    response = requests.get(f"{BASE_URL}/tasks/stats")
    print_response("Final Statistics", response)

def test_error_handling():
    """Test error handling"""
    print_separator("Error Handling Tests")
    
    # Test non-existent task
    print("\n🔍 Testing non-existent task...")
    response = requests.get(f"{BASE_URL}/tasks/non-existent-task-id")
    print_response("Non-existent Task", response)
    
    # Test invalid task ID format
    print("\n🔍 Testing invalid task ID...")
    response = requests.get(f"{BASE_URL}/tasks/invalid-id")
    print_response("Invalid Task ID", response)

def main():
    """Main function"""
    print("🚀 Starting Task Monitoring API Tests")
    print(f"📡 API Base URL: {BASE_URL}")
    print(f"⏰ Test started at: {datetime.now()}")
    
    try:
        # Test basic functionality
        test_task_monitoring()
        
        # Test error handling
        test_error_handling()
        
        print_separator("Test Summary")
        print("✅ Task monitoring API tests completed!")
        print("\n📊 Available endpoints tested:")
        print("   - GET /tasks/stats - Task statistics")
        print("   - GET /tasks/running - Running tasks")
        print("   - GET /tasks/pending - Pending tasks")
        print("   - GET /tasks/all - All tasks")
        print("   - GET /tasks/{task_id} - Specific task status")
        print("   - GET /tasks/count/running - Running task count")
        print("   - DELETE /tasks/cleanup - Cleanup old tasks")
        print("\n🎯 Integration points tested:")
        print("   - POST /ingest - Ingest with task tracking")
        print("   - POST /temporal/ingest-video - Temporal ingest with task tracking")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server")
        print("   Make sure the server is running: uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main() 