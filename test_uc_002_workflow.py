#!/usr/bin/env python3
"""
Test script to demonstrate UC-002 workflow in one session
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "examples"))

from use_case_2_async_job_submission_patched import MockInterProJobManager

async def test_workflow():
    """Test the complete async workflow"""
    print("🧪 Testing UC-002 Async Job Workflow")
    print("="*50)

    # Initialize manager
    manager = MockInterProJobManager()

    # Test 1: Submit a job
    print("\n1️⃣ Submitting job...")
    result = await manager.submit_analysis_job(
        input_file=Path("examples/data/large_dataset.fasta"),
        priority=8,
        databases="Pfam,PRINTS"
    )

    if result["status"] == "success":
        job_id = result["job_id"]
        print(f"✅ Job submitted: {job_id}")
    else:
        print("❌ Job submission failed")
        return

    # Test 2: Check status immediately
    print("\n2️⃣ Checking status immediately...")
    status = await manager.get_job_status(job_id)
    if status["status"] == "success":
        print(f"📊 Status: {status['job_status']} ({status['progress']}%)")

    # Test 3: Wait a bit and check again
    print("\n3️⃣ Waiting and checking status again...")
    await asyncio.sleep(2)
    status = await manager.get_job_status(job_id)
    if status["status"] == "success":
        print(f"📊 Status: {status['job_status']} ({status['progress']}%)")

    # Test 4: Wait for completion
    print("\n4️⃣ Waiting for completion...")
    await asyncio.sleep(2)
    status = await manager.get_job_status(job_id)
    if status["status"] == "success":
        print(f"📊 Status: {status['job_status']} ({status['progress']}%)")

    # Test 5: Get results
    if status["job_status"] == "completed":
        print("\n5️⃣ Getting results...")
        results = await manager.get_job_result(job_id)
        if results["status"] == "success":
            print(f"📁 Results retrieved successfully!")
            print(f"First few lines of results:")
            print(results["results"][:200] + "...")

    # Test 6: List all jobs
    print("\n6️⃣ Listing all jobs...")
    all_jobs = await manager.list_jobs()
    if all_jobs["status"] == "success":
        print(f"📋 Found {len(all_jobs['jobs'])} jobs:")
        for job in all_jobs["jobs"]:
            print(f"  • {job['job_id']}: {job['status']}")

    # Test 7: Submit another job and cancel it
    print("\n7️⃣ Testing job cancellation...")
    result2 = await manager.submit_analysis_job(
        input_file=Path("examples/data/sample.fasta"),
        priority=3
    )

    if result2["status"] == "success":
        job_id2 = result2["job_id"]
        print(f"✅ Second job submitted: {job_id2}")

        # Cancel it
        cancel_result = await manager.cancel_job(job_id2)
        if cancel_result["status"] == "success":
            print(f"🚫 Job cancelled successfully")

    print("\n✅ UC-002 workflow test completed!")

if __name__ == "__main__":
    asyncio.run(test_workflow())