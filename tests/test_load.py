"""
Load Testing for CustoFlow API

Tests the system under load to verify performance and stability.
"""
import asyncio
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import statistics
import pytest


# API endpoint
API_URL = "http://localhost:8000/chat"


def make_request(user_id: str, message: str) -> Dict:
    """
    Make a single API request.
    
    Args:
        user_id: User identifier
        message: Message to send
        
    Returns:
        Response dictionary with timing and status
    """
    start_time = time.time()
    try:
        response = requests.post(
            API_URL,
            json={
                "message": message,
                "user_id": user_id
            },
            timeout=30
        )
        elapsed = time.time() - start_time
        
        return {
            "status_code": response.status_code,
            "response_time": elapsed,
            "success": response.status_code == 200,
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status_code": None,
            "response_time": elapsed,
            "success": False,
            "error": str(e)
        }


def run_load_test(
    num_requests: int = 50,
    concurrent_users: int = 10,
    messages: List[str] = None
) -> Dict:
    """
    Run load test with concurrent requests.
    
    Args:
        num_requests: Total number of requests
        concurrent_users: Number of concurrent users
        messages: List of messages to use (cycles if needed)
        
    Returns:
        Test results dictionary
    """
    if messages is None:
        messages = [
            "What is your refund policy?",
            "Where is my order 12345?",
            "How long does shipping take?",
            "I need help with a damaged product",
            "What are your payment methods?"
        ]
    
    print(f"Starting load test: {num_requests} requests, {concurrent_users} concurrent users")
    
    results = []
    start_time = time.time()
    
    # Create thread pool for concurrent requests
    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        
        for i in range(num_requests):
            user_id = f"load_test_user_{i % concurrent_users}"
            message = messages[i % len(messages)]
            future = executor.submit(make_request, user_id, message)
            futures.append(future)
        
        # Collect results
        for future in futures:
            result = future.result()
            results.append(result)
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    response_times = [r["response_time"] for r in results]
    successful = sum(1 for r in results if r["success"])
    failed = num_requests - successful
    
    stats = {
        "total_requests": num_requests,
        "concurrent_users": concurrent_users,
        "total_time": total_time,
        "requests_per_second": num_requests / total_time if total_time > 0 else 0,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / num_requests * 100) if num_requests > 0 else 0,
        "response_times": {
            "min": min(response_times) if response_times else 0,
            "max": max(response_times) if response_times else 0,
            "mean": statistics.mean(response_times) if response_times else 0,
            "median": statistics.median(response_times) if response_times else 0,
            "p95": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "p99": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
        },
        "errors": [r["error"] for r in results if r["error"]]
    }
    
    return stats


def print_load_test_results(stats: Dict):
    """Print load test results in a readable format."""
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Concurrent Users: {stats['concurrent_users']}")
    print(f"Total Time: {stats['total_time']:.2f}s")
    print(f"Requests/Second: {stats['requests_per_second']:.2f}")
    print(f"\nSuccess Rate: {stats['success_rate']:.1f}%")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nResponse Times:")
    print(f"  Min: {stats['response_times']['min']:.3f}s")
    print(f"  Max: {stats['response_times']['max']:.3f}s")
    print(f"  Mean: {stats['response_times']['mean']:.3f}s")
    print(f"  Median: {stats['response_times']['median']:.3f}s")
    print(f"  P95: {stats['response_times']['p95']:.3f}s")
    print(f"  P99: {stats['response_times']['p99']:.3f}s")
    
    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in set(stats['errors'][:5]):  # Show first 5 unique errors
            print(f"  - {error}")
    
    print("=" * 60)


@pytest.mark.skip(reason="Requires API server to be running")
def test_load_test():
    """Test load testing functionality."""
    # This test is skipped by default as it requires the API server
    # It can be run manually when the server is available
    print("CustoFlow Load Test")
    print("=" * 60)
    print("Make sure the API server is running on http://localhost:8000")
    print("=" * 60)
    
    # Run load test
    stats = run_load_test(
        num_requests=50,
        concurrent_users=10
    )
    
    print_load_test_results(stats)
    
    # Performance thresholds
    print("\nPerformance Thresholds:")
    if stats['success_rate'] >= 95:
        print("✅ Success rate: PASS (>= 95%)")
    else:
        print(f"❌ Success rate: FAIL ({stats['success_rate']:.1f}% < 95%)")
    
    if stats['response_times']['p95'] <= 5.0:
        print(f"✅ P95 response time: PASS (<= 5s)")
    else:
        print(f"❌ P95 response time: FAIL ({stats['response_times']['p95']:.2f}s > 5s)")
    
    if stats['requests_per_second'] >= 5:
        print(f"✅ Throughput: PASS (>= 5 req/s)")
    else:
        print(f"❌ Throughput: FAIL ({stats['requests_per_second']:.2f} req/s < 5 req/s)")


if __name__ == "__main__":
    print("CustoFlow Load Test")
    print("=" * 60)
    print("Make sure the API server is running on http://localhost:8000")
    print("=" * 60)
    
    # Run load test
    stats = run_load_test(
        num_requests=50,
        concurrent_users=10
    )
    
    print_load_test_results(stats)
    
    # Performance thresholds
    print("\nPerformance Thresholds:")
    if stats['success_rate'] >= 95:
        print("✅ Success rate: PASS (>= 95%)")
    else:
        print(f"❌ Success rate: FAIL ({stats['success_rate']:.1f}% < 95%)")
    
    if stats['response_times']['p95'] <= 5.0:
        print(f"✅ P95 response time: PASS (<= 5s)")
    else:
        print(f"❌ P95 response time: FAIL ({stats['response_times']['p95']:.2f}s > 5s)")
    
    if stats['requests_per_second'] >= 5:
        print(f"✅ Throughput: PASS (>= 5 req/s)")
    else:
        print(f"❌ Throughput: FAIL ({stats['requests_per_second']:.2f} req/s < 5 req/s)")

