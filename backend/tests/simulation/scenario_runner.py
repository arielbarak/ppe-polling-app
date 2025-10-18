"""
Scenario runner for simulating different test scenarios.
"""

import asyncio
from typing import List, Dict, Any
import random
import time
from .user_simulator import SimulatedUser


class ScenarioRunner:
    """
    Runs different test scenarios with simulated users.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.users: List[SimulatedUser] = []
        self.results = {
            "scenario": "",
            "total_users": 0,
            "successful_registrations": 0,
            "successful_ppes": 0,
            "successful_votes": 0,
            "failed_operations": [],
            "timings": {},
            "errors": []
        }
    
    def create_users(self, count: int) -> List[SimulatedUser]:
        """Create simulated users."""
        users = []
        for i in range(count):
            user_id = f"sim_user_{i:04d}_{int(time.time() * 1000)}"
            user = SimulatedUser(user_id, self.base_url)
            user.generate_keypair()
            users.append(user)
        
        self.users = users
        self.results["total_users"] = count
        return users
    
    async def run_honest_scenario(self, poll_id: str, num_users: int = 50):
        """
        Run honest scenario: all users follow protocol correctly.
        
        Args:
            poll_id: Poll identifier
            num_users: Number of users to simulate
        """
        print(f"\n{'='*60}")
        print(f"RUNNING HONEST SCENARIO: {num_users} users")
        print(f"{'='*60}\n")
        
        self.results["scenario"] = "honest"
        users = self.create_users(num_users)
        
        # Phase 1: Concurrent registration
        print(f"\n--- Phase 1: Registration ({num_users} users) ---")
        registration_tasks = [
            user.register_for_poll(poll_id, solve_captcha=True)
            for user in users
        ]
        registration_results = await asyncio.gather(*registration_tasks, return_exceptions=True)
        
        self.results["successful_registrations"] = sum(
            1 for r in registration_results if r is True
        )
        print(f"Registrations: {self.results['successful_registrations']}/{num_users}")
        
        # Phase 2: PPE between neighbors (simulate ideal graph assignments)
        print(f"\n--- Phase 2: PPE Certifications ---")
        registered_users = [u for u, r in zip(users, registration_results) if r is True]
        
        # Simulate each user doing PPE with 2-3 neighbors
        ppe_tasks = []
        for i, user in enumerate(registered_users):
            # Get 2 random neighbors (simplified ideal graph)
            neighbors = random.sample(
                [u for u in registered_users if u != user],
                min(2, len(registered_users) - 1)
            )
            for neighbor in neighbors:
                ppe_tasks.append(
                    user.perform_ppe_with_peer(poll_id, neighbor.user_id)
                )
        
        if ppe_tasks:
            ppe_results = await asyncio.gather(*ppe_tasks, return_exceptions=True)
            self.results["successful_ppes"] = sum(1 for r in ppe_results if r is True)
            print(f"PPE Completions: {self.results['successful_ppes']}/{len(ppe_tasks)}")
        
        # Phase 3: Voting
        print(f"\n--- Phase 3: Voting ---")
        options = ["Option A", "Option B", "Option C"]
        vote_tasks = [
            user.vote(poll_id, random.choice(options))
            for user in registered_users
        ]
        vote_results = await asyncio.gather(*vote_tasks, return_exceptions=True)
        
        self.results["successful_votes"] = sum(1 for r in vote_results if r is True)
        print(f"Votes Cast: {self.results['successful_votes']}/{len(registered_users)}")
        
        # Collect timing statistics
        self._collect_timings(users)
        
        print(f"\n{'='*60}")
        print("SCENARIO COMPLETE")
        print(f"{'='*60}\n")
        
        return self.results
    
    async def run_sybil_attack_scenario(self, poll_id: str, 
                                       num_honest: int = 30,
                                       num_sybils: int = 20):
        """
        Run Sybil attack scenario.
        
        Args:
            poll_id: Poll identifier
            num_honest: Number of honest users
            num_sybils: Number of Sybil identities
        """
        print(f"\n{'='*60}")
        print(f"RUNNING SYBIL ATTACK SCENARIO")
        print(f"Honest users: {num_honest}, Sybil identities: {num_sybils}")
        print(f"{'='*60}\n")
        
        self.results["scenario"] = "sybil_attack"
        
        # Create honest users
        honest_users = self.create_users(num_honest)
        
        # Create Sybil users (controlled by attacker)
        sybil_users = []
        for i in range(num_sybils):
            user_id = f"sybil_{i:04d}_{int(time.time() * 1000)}"
            user = SimulatedUser(user_id, self.base_url)
            user.generate_keypair()
            sybil_users.append(user)
        
        all_users = honest_users + sybil_users
        self.results["total_users"] = len(all_users)
        
        # Phase 1: Registration (all users try to register)
        print(f"\n--- Phase 1: Registration ---")
        registration_tasks = [
            user.register_for_poll(poll_id, solve_captcha=True)
            for user in all_users
        ]
        registration_results = await asyncio.gather(*registration_tasks, return_exceptions=True)
        
        self.results["successful_registrations"] = sum(1 for r in registration_results if r is True)
        print(f"Registrations: {self.results['successful_registrations']}/{len(all_users)}")
        
        # Phase 2: PPE - Sybils primarily certify each other
        print(f"\n--- Phase 2: PPE (with collusion) ---")
        registered_users = [u for u, r in zip(all_users, registration_results) if r is True]
        registered_sybils = [u for u in sybil_users if u in registered_users]
        registered_honest = [u for u in honest_users if u in registered_users]
        
        ppe_tasks = []
        
        # Honest users certify randomly
        for user in registered_honest:
            neighbors = random.sample(
                [u for u in registered_users if u != user],
                min(2, len(registered_users) - 1)
            )
            for neighbor in neighbors:
                ppe_tasks.append(user.perform_ppe_with_peer(poll_id, neighbor.user_id))
        
        # Sybils primarily certify each other (collusion)
        for sybil in registered_sybils:
            # 80% chance to certify another Sybil, 20% honest user
            for _ in range(2):
                if random.random() < 0.8 and len(registered_sybils) > 1:
                    peer = random.choice([s for s in registered_sybils if s != sybil])
                else:
                    if registered_honest:
                        peer = random.choice(registered_honest)
                    else:
                        continue
                ppe_tasks.append(sybil.perform_ppe_with_peer(poll_id, peer.user_id))
        
        if ppe_tasks:
            ppe_results = await asyncio.gather(*ppe_tasks, return_exceptions=True)
            self.results["successful_ppes"] = sum(1 for r in ppe_results if r is True)
            print(f"PPE Completions: {self.results['successful_ppes']}")
        
        # Phase 3: Voting (Sybils vote for same option)
        print(f"\n--- Phase 3: Voting (coordinated Sybil votes) ---")
        sybil_option = "Option A"  # All Sybils vote for this
        
        vote_tasks = []
        for user in registered_honest:
            vote_tasks.append(user.vote(poll_id, random.choice(["Option A", "Option B", "Option C"])))
        
        for sybil in registered_sybils:
            vote_tasks.append(sybil.vote(poll_id, sybil_option))
        
        vote_results = await asyncio.gather(*vote_tasks, return_exceptions=True)
        self.results["successful_votes"] = sum(1 for r in vote_results if r is True)
        print(f"Votes Cast: {self.results['successful_votes']}")
        
        # Analyze attack effectiveness
        print(f"\n--- Attack Analysis ---")
        print(f"Sybil votes for '{sybil_option}': {len(registered_sybils)}")
        print(f"Honest votes distributed across options")
        print(f"Verification should detect Sybil cluster!")
        
        self._collect_timings(all_users)
        
        print(f"\n{'='*60}")
        print("SYBIL ATTACK SCENARIO COMPLETE")
        print(f"{'='*60}\n")
        
        return self.results
    
    async def run_load_test(self, poll_id: str, num_users: int = 100):
        """
        Run load test with many concurrent users.
        
        Args:
            poll_id: Poll identifier
            num_users: Number of concurrent users
        """
        print(f"\n{'='*60}")
        print(f"RUNNING LOAD TEST: {num_users} concurrent users")
        print(f"{'='*60}\n")
        
        self.results["scenario"] = "load_test"
        users = self.create_users(num_users)
        
        start_time = time.time()
        
        # All operations concurrent
        print(f"\n--- Concurrent Operations ---")
        
        tasks = []
        for user in users:
            # Each user: register -> PPE -> vote
            tasks.append(self._user_full_flow(user, poll_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        
        print(f"\n--- Load Test Results ---")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Successful completions: {successful}/{num_users}")
        print(f"Throughput: {successful/elapsed:.2f} users/second")
        
        self.results["successful_registrations"] = successful
        self.results["total_time"] = elapsed
        self.results["throughput"] = successful / elapsed if elapsed > 0 else 0
        
        self._collect_timings(users)
        
        return self.results
    
    async def _user_full_flow(self, user: SimulatedUser, poll_id: str) -> Dict[str, Any]:
        """Complete flow for one user."""
        try:
            # Register
            if not await user.register_for_poll(poll_id):
                return {"success": False, "stage": "registration"}
            
            # Simulate PPE with one peer (simplified)
            peer_id = f"peer_{random.randint(1000, 9999)}"
            if not await user.perform_ppe_with_peer(poll_id, peer_id):
                return {"success": False, "stage": "ppe"}
            
            # Vote
            if not await user.vote(poll_id, random.choice(["Option A", "Option B"])):
                return {"success": False, "stage": "voting"}
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _collect_timings(self, users: List[SimulatedUser]):
        """Collect timing statistics from all users."""
        all_timings = {
            "registration": [],
            "ppe_completion": [],
            "vote_cast": []
        }
        
        for user in users:
            user_timings = user.get_average_timings()
            for operation, stats in user_timings.items():
                if operation in all_timings:
                    all_timings[operation].append(stats)
        
        # Compute aggregate statistics
        import statistics
        self.results["timings"] = {}
        for operation, timing_list in all_timings.items():
            if timing_list:
                means = [t["mean"] for t in timing_list]
                self.results["timings"][operation] = {
                    "avg_mean": statistics.mean(means),
                    "min": min(t["min"] for t in timing_list),
                    "max": max(t["max"] for t in timing_list)
                }
    
    def print_summary(self):
        """Print summary of results."""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Scenario: {self.results['scenario']}")
        print(f"Total Users: {self.results['total_users']}")
        print(f"Successful Registrations: {self.results['successful_registrations']}")
        print(f"Successful PPEs: {self.results['successful_ppes']}")
        print(f"Successful Votes: {self.results['successful_votes']}")
        
        if self.results.get("timings"):
            print(f"\nTiming Statistics:")
            for operation, stats in self.results["timings"].items():
                print(f"  {operation}:")
                print(f"    Average: {stats['avg_mean']:.3f}s")
                print(f"    Min: {stats['min']:.3f}s")
                print(f"    Max: {stats['max']:.3f}s")
        
        if self.results.get("throughput"):
            print(f"\nThroughput: {self.results['throughput']:.2f} users/second")
        
        print(f"{'='*60}\n")