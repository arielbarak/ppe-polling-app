"""
Main script to run simulations.

Usage:
    python -m tests.simulation.run_simulation --scenario honest --users 50
    python -m tests.simulation.run_simulation --scenario sybil --honest 30 --sybils 20
    python -m tests.simulation.run_simulation --scenario load --users 100
"""

import asyncio
import argparse
import httpx
import sys
from .scenario_runner import ScenarioRunner


async def create_test_poll(base_url: str) -> str:
    """Create a test poll for simulation."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/polls",
            json={
                "question": "Simulation Test Poll",
                "options": ["Option A", "Option B", "Option C"]
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            poll_id = data["id"]
            print(f"Created test poll: {poll_id}")
            return poll_id
        else:
            print(f"Failed to create poll: {response.status_code}")
            sys.exit(1)


async def verify_poll(base_url: str, poll_id: str):
    """Run verification on the poll after simulation."""
    print(f"\n{'='*60}")
    print("RUNNING POST-SIMULATION VERIFICATION")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient() as client:
        # Get comprehensive verification
        response = await client.get(
            f"{base_url}/polls/{poll_id}/verification/comprehensive",
            timeout=60.0
        )
        
        if response.status_code == 200:
            verification = response.json()
            
            print(f"Verification Status: {'VALID' if verification['is_valid'] else 'INVALID'}")
            print(f"\nSummary: {verification['summary']}")
            
            if verification.get('errors'):
                print(f"\nErrors Found:")
                for error in verification['errors']:
                    print(f"  ERROR: {error}")
            
            if verification.get('warnings'):
                print(f"\nWarnings:")
                for warning in verification['warnings']:
                    print(f"  WARNING: {warning}")
            
            if verification.get('analysis', {}).get('suspicious_clusters'):
                clusters = verification['analysis']['suspicious_clusters']
                print(f"\n🚨 Suspicious Clusters Detected: {len(clusters)}")
                for i, cluster in enumerate(clusters):
                    print(f"  Cluster {i+1}: {cluster['size']} nodes, conductance={cluster['conductance']:.4f}")
            
            print()
        else:
            print(f"Verification failed: {response.status_code}")


async def main():
    """Main entry point for simulations."""
    parser = argparse.ArgumentParser(description="Run PPE polling system simulations")
    parser.add_argument("--scenario", choices=["honest", "sybil", "load"], 
                       default="honest", help="Scenario to run")
    parser.add_argument("--users", type=int, default=50, 
                       help="Number of users (honest scenario)")
    parser.add_argument("--honest", type=int, default=30, 
                       help="Number of honest users (sybil scenario)")
    parser.add_argument("--sybils", type=int, default=20, 
                       help="Number of Sybil identities (sybil scenario)")
    parser.add_argument("--base-url", default="http://localhost:8000",
                       help="Base URL of the API")
    parser.add_argument("--verify", action="store_true",
                       help="Run verification after simulation")
    
    args = parser.parse_args()
    
    # Create test poll
    poll_id = await create_test_poll(args.base_url)
    
    # Run scenario
    runner = ScenarioRunner(args.base_url)
    
    if args.scenario == "honest":
        results = await runner.run_honest_scenario(poll_id, args.users)
    elif args.scenario == "sybil":
        results = await runner.run_sybil_attack_scenario(poll_id, args.honest, args.sybils)
    elif args.scenario == "load":
        results = await runner.run_load_test(poll_id, args.users)
    
    # Print summary
    runner.print_summary()
    
    # Run verification if requested
    if args.verify:
        await verify_poll(args.base_url, poll_id)


if __name__ == "__main__":
    asyncio.run(main())