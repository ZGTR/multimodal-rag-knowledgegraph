#!/usr/bin/env python3
"""
Task Monitoring API Demo

This script demonstrates how to use the new task monitoring API
to track and monitor background tasks.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def main():
    """Demo the task monitoring API"""
    print("🚀 Task Monitoring API Demo")
    print("=" * 50)
    
    # 1. Check how many background tasks are running
    print("\n1️⃣  Checking running background tasks...")
    try:
        response = requests.get(f"{BASE_URL}/tasks/count/running")
        if response.status_code == 200:
            count = response.json()["running_tasks"]
            print(f"   📊 Currently running tasks: {count}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to API server")
        print("   💡 Start the server with: uvicorn src.api.main:app --reload")
        return
    
    # 2. Get detailed task statistics
    print("\n2️⃣  Getting task statistics...")
    response = requests.get(f"{BASE_URL}/tasks/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   📈 Total tasks: {stats['total_tasks']}")
        print(f"   🏃 Running tasks: {stats['running_tasks']}")
        print(f"   ⏳ Pending tasks: {stats['pending_tasks']}")
        print(f"   ✅ Completed tasks: {stats['completed_tasks']}")
        print(f"   ❌ Failed tasks: {stats['failed_tasks']}")
        print(f"   📊 Success rate: {stats['success_rate']:.1f}%")
    
    # 3. Trigger a background task
    print("\n3️⃣  Triggering a background task...")
    ingest_data = {
        "videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=ingest_data)
    if response.status_code == 200:
        result = response.json()
        task_id = result["task_id"]
        print(f"   🎯 Task queued with ID: {task_id}")
        print(f"   📝 Command: {' '.join(result['cmd'])}")
        
        # 4. Monitor the task
        print("\n4️⃣  Monitoring task progress...")
        for i in range(10):
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/tasks/{task_id}")
            if response.status_code == 200:
                task = response.json()
                status = task["status"]
                progress = task.get("progress", "No progress info")
                print(f"   ⏳ Check {i+1}: Status={status}, Progress={progress}")
                
                if status in ["completed", "failed"]:
                    print(f"   ✅ Task finished with status: {status}")
                    if status == "failed" and task.get("error_message"):
                        print(f"   ❌ Error: {task['error_message']}")
                    break
            else:
                print(f"   ❌ Failed to get task status: {response.status_code}")
        
        # 5. Final statistics
        print("\n5️⃣  Final statistics...")
        response = requests.get(f"{BASE_URL}/tasks/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   📊 Running tasks: {stats['running_tasks']}")
            print(f"   📈 Total tasks: {stats['total_tasks']}")
    
    # 6. Show all recent tasks
    print("\n6️⃣  Recent tasks...")
    response = requests.get(f"{BASE_URL}/tasks/all?limit=5")
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        print(f"   📋 Showing {len(tasks)} recent tasks:")
        for task in tasks:
            print(f"      • {task['task_id'][:8]}... - {task['status']} - {task['created_at']}")
    
    print("\n✅ Demo completed!")
    print("\n💡 Try these commands:")
    print("   curl -X GET 'http://localhost:8000/tasks/count/running'")
    print("   curl -X GET 'http://localhost:8000/tasks/stats'")
    print("   curl -X GET 'http://localhost:8000/tasks/running'")

if __name__ == "__main__":
    main() 