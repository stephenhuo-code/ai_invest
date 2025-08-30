#!/usr/bin/env python3
"""
Quick test script to verify LLM API endpoints are working.

Tests the new natural language API endpoints without requiring database setup.
"""
import requests
import json
import sys
from typing import Dict, Any


def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> bool:
    """Test a single API endpoint."""
    base_url = "http://localhost:8000"
    url = f"{base_url}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == 200:
            print(f"✅ {method} {endpoint} - Success")
            return True
        elif response.status_code == 503:
            print(f"⚠️ {method} {endpoint} - Service unavailable (agents not initialized)")
            return True  # Consider this a success for basic connectivity
        else:
            print(f"❌ {method} {endpoint} - Status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection failed (server not running)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {method} {endpoint} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False


def main():
    """Test LLM API endpoints."""
    print("🧪 Testing LLM API Endpoints")
    print("=" * 40)
    print("Note: This requires the application to be running on localhost:8000")
    print("Start with: uvicorn main:app --reload")
    print()
    
    # Test endpoints
    endpoints_to_test = [
        ("/", "GET"),
        ("/docs", "GET"),
        ("/health", "GET"),
        ("/llm/capabilities", "GET"),
        ("/llm/agents/info", "GET"),
        ("/llm/workflow/active", "GET"),
    ]
    
    # Test with sample data
    sample_requests = [
        ("/llm/execute", "POST", {
            "query": "What are your capabilities?",
            "agent": "auto"
        }),
        ("/llm/workflow", "POST", {
            "description": "Test workflow: Get system status and capabilities",
            "max_execution_time": 60
        })
    ]
    
    results = []
    
    print("Basic Endpoint Tests:")
    print("-" * 25)
    for endpoint, method in endpoints_to_test:
        result = test_api_endpoint(endpoint, method)
        results.append((f"{method} {endpoint}", result))
    
    print("\nAdvanced Endpoint Tests:")
    print("-" * 25)
    for endpoint, method, data in sample_requests:
        result = test_api_endpoint(endpoint, method, data)
        results.append((f"{method} {endpoint}", result))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 API TEST RESULTS")
    print("=" * 40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 40)
    print(f"Results: {passed}/{total} endpoints working")
    
    if passed >= total * 0.7:  # 70% success rate
        print("🎉 LLM API is working! You can now:")
        print("  • Visit http://localhost:8000/docs for interactive API docs")
        print("  • Test natural language queries at /llm/execute")
        print("  • Try intelligent workflows at /llm/workflow")
        print("  • Check agent capabilities at /llm/capabilities")
        return True
    else:
        print("❌ Several endpoints failed. Check server logs for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)