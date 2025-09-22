import pytest
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import socket
from app.models.poll import Poll, UserVerification
from app.services.poll_service import poll_service, _polls_db

# These tests are designed to be run against a running server
# You can skip them in normal test runs by using the "-m 'not stress'" flag
# To run only stress tests: pytest -m stress

BASE_URL = "http://localhost:8000"

def is_server_running():
    """Check if the server is running by attempting to connect to it"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 8000))
        s.close()
        return True
    except:
        return False

def random_string(length=10):
    """Generate a random string for test data"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_large_poll(num_users=100, connectivity_factor=0.1):
    """
    Generate a large poll with many users and certifications
    
    Args:
        num_users: Number of users to create
        connectivity_factor: Fraction of possible connections to create (0.0-1.0)
    
    Returns:
        Poll object with the generated data
    """
    poll = Poll(
        id=f"stress-test-{random_string(8)}",
        question=f"Stress Test Poll with {num_users} users",
        options=["Option 1", "Option 2", "Option 3"]
    )
    
    # Generate users
    poll.registrants = {}
    for i in range(num_users):
        user_id = f"user{i}"
        poll.registrants[user_id] = {"key": f"value{i}"}
    
    # Generate PPE certifications based on connectivity factor
    poll.ppe_certifications = {user_id: set() for user_id in poll.registrants}
    
    user_ids = list(poll.registrants.keys())
    max_connections = num_users * (num_users - 1) // 2  # Maximum possible edges in a complete graph
    num_connections = int(max_connections * connectivity_factor)
    
    # Ensure minimum connectivity (at least 2 connections per user)
    for i, user_id in enumerate(user_ids):
        next_user = user_ids[(i + 1) % num_users]
        prev_user = user_ids[(i - 1) % num_users]
        
        poll.ppe_certifications[user_id].add(next_user)
        poll.ppe_certifications[next_user].add(user_id)
        
        poll.ppe_certifications[user_id].add(prev_user)
        poll.ppe_certifications[prev_user].add(user_id)
    
    # Add additional random connections up to the desired connectivity
    remaining_connections = num_connections - (num_users * 2)
    
    if remaining_connections > 0:
        possible_edges = [(user1, user2) 
                         for i, user1 in enumerate(user_ids) 
                         for user2 in user_ids[i+1:]
                         if user2 not in poll.ppe_certifications[user1]]
        
        if possible_edges:
            selected_edges = random.sample(possible_edges, 
                                          min(remaining_connections, len(possible_edges)))
            
            for user1, user2 in selected_edges:
                poll.ppe_certifications[user1].add(user2)
                poll.ppe_certifications[user2].add(user1)
    
    # Generate verifications (everyone has 2+ verifications)
    poll.verifications = {}
    for user_id in poll.registrants:
        verified_by = set(random.sample(
            [u for u in user_ids if u != user_id], 
            min(2, num_users - 1)
        ))
        poll.verifications[user_id] = UserVerification(verified_by=verified_by)
    
    # Add votes for half the users
    poll.votes = {}
    voting_users = random.sample(user_ids, num_users // 2)
    for user_id in voting_users:
        poll.votes[user_id] = {"option": random.choice(poll.options)}
    
    return poll

@pytest.mark.stress
class TestVerificationPerformance:
    """Performance and stress tests for the verification functionality"""
    
    def test_verification_performance_local(self):
        """Test the performance of the verify_poll_integrity method with different poll sizes"""
        poll_sizes = [10, 50, 100, 200]
        connectivity = 0.2  # 20% of possible connections
        
        results = {}
        
        for size in poll_sizes:
            poll = generate_large_poll(num_users=size, connectivity_factor=connectivity)
            
            start_time = time.time()
            verification_result = poll_service.verify_poll_integrity(poll)
            end_time = time.time()
            
            execution_time = end_time - start_time
            results[size] = {
                "execution_time": execution_time,
                "is_valid": verification_result["is_valid"],
                "min_certifications": verification_result["min_certifications_per_user"],
                "ppe_coverage": verification_result["ppe_coverage"]
            }
            
            # Performance expectations
            if size <= 100:
                assert execution_time < 1.0, f"Verification for {size} users took too long: {execution_time}s"
            else:
                assert execution_time < 3.0, f"Verification for {size} users took too long: {execution_time}s"
        
        # Print results for manual review
        print("\nVerification Performance Results:")
        for size, data in results.items():
            print(f"{size} users: {data['execution_time']:.4f}s, Valid: {data['is_valid']}, " 
                  f"Min Cert: {data['min_certifications']}, Coverage: {data['ppe_coverage']:.2f}")
    
    @pytest.mark.requires_server
    def test_api_verification_performance(self):
        """Test the performance of the verification API endpoint with different poll sizes.
        
        This test validates the API's performance by sending verification requests
        for polls of varying sizes and measuring response times. It requires a
        running server on localhost:8000.
        
        Returns:
            None
            
        Raises:
            pytest.skip: If the server is not running.
        """
        if not is_server_running():
            pytest.skip("Server is not running on localhost:8000")
            
        poll_sizes = [10, 50, 100]
        connectivity = 0.2
        
        results = {}
        
        for size in poll_sizes:
            # Create poll and add to database
            poll = generate_large_poll(num_users=size, connectivity_factor=connectivity)
            _polls_db[poll.id] = poll
            
            # Test API performance
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/polls/{poll.id}/verify")
            end_time = time.time()
            
            assert response.status_code == 200, f"API request failed for poll with {size} users"
            
            execution_time = end_time - start_time
            results[size] = {
                "execution_time": execution_time,
                "response_size": len(response.content)
            }
            
            # Performance expectations - API should be reasonably fast
            if size <= 50:
                assert execution_time < 1.5, f"API verification for {size} users took too long: {execution_time}s"
            else:
                assert execution_time < 5.0, f"API verification for {size} users took too long: {execution_time}s"
        
        # Print results for manual review
        print("\nAPI Verification Performance Results:")
        for size, data in results.items():
            print(f"{size} users: {data['execution_time']:.4f}s, Response size: {data['response_size']/1024:.2f} KB")
    
    @pytest.mark.requires_server
    def test_concurrent_verification_requests(self):
        """Test the server's ability to handle concurrent verification requests.
        
        This test evaluates the server's performance under load by sending multiple
        concurrent verification requests and measuring response times. It requires
        a running server on localhost:8000.
        
        Returns:
            None
            
        Raises:
            pytest.skip: If the server is not running.
        """
        if not is_server_running():
            pytest.skip("Server is not running on localhost:8000")
            
        # Create several polls
        num_polls = 5
        polls = [generate_large_poll(num_users=30) for _ in range(num_polls)]
        
        # Add polls to database
        for poll in polls:
            _polls_db[poll.id] = poll
        
        # Test concurrent requests
        num_concurrent = 10  # 10 concurrent requests
        num_requests = 50    # 50 total requests
        
        poll_ids = [poll.id for poll in polls]
        
        def make_request(poll_id):
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/polls/{poll_id}/verify")
            end_time = time.time()
            
            return {
                "poll_id": poll_id,
                "status_code": response.status_code,
                "execution_time": end_time - start_time
            }
        
        results = []
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request, random.choice(poll_ids)) 
                      for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                assert result["status_code"] == 200, f"Concurrent request failed: {result}"
        
        # Calculate statistics
        execution_times = [r["execution_time"] for r in results]
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        # Print results for manual review
        print(f"\nConcurrent Verification Results:")
        print(f"Average response time: {avg_time:.4f}s")
        print(f"Maximum response time: {max_time:.4f}s")
        print(f"Successful requests: {len([r for r in results if r['status_code'] == 200])}/{num_requests}")
        
        # Performance expectations
        assert avg_time < 2.0, f"Average response time too high: {avg_time}s"
        assert max_time < 5.0, f"Maximum response time too high: {max_time}s"