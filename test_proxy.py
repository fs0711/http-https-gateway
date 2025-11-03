"""
Simple test script to verify the proxy server is working correctly
"""
import requests
import json

# Proxy server URL (assuming running locally on port 5011)
PROXY_URL = "http://localhost:5011"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{PROXY_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_proxy_get():
    """Test a simple GET request through the proxy"""
    print("\nTesting GET request through proxy...")
    try:
        # This will be forwarded to https://smartswitch.orkofleet.com/
        response = requests.get(f"{PROXY_URL}/", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.content)} bytes")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_proxy_post():
    """Test a POST request through the proxy"""
    print("\nTesting POST request through proxy...")
    try:
        test_data = {"test": "data", "message": "Hello from proxy"}
        # This will be forwarded to https://smartswitch.orkofleet.com/api/test
        response = requests.post(
            f"{PROXY_URL}/api/test",
            json=test_data,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Proxy Server Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Health Check", test_health_check()))
    results.append(("GET Request", test_proxy_get()))
    results.append(("POST Request", test_proxy_post()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
