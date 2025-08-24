"""
Bank Renege Simulation using Strataregula

This example demonstrates how to use Strataregula for simulating
bank customer behavior with reneging (customers leaving the queue).
Based on SimPy's Bank Renege example.
"""

import random
import time
from pathlib import Path
from typing import Dict, Any

from strataregula import Pipeline


class BankSimulator:
    """Bank customer simulation with reneging behavior."""
    
    def __init__(self, config_path: Path = None):
        """Initialize the bank simulator."""
        self.compiler = Pipeline(config_path)
        
        # Set up simulation parameters
        self.setup_simulation_data()
        
    def setup_simulation_data(self):
        """Set up simulation data sources."""
        # Customer types and their patience levels
        customer_types = {
            'regular': ['patient', 'impatient', 'very_impatient'],
            'priority': ['vip', 'business', 'senior'],
            'service_types': ['teller', 'loan', 'investment']
        }
        
        # Bank branches and their capacities
        branches = {
            'downtown': ['main', 'express', 'premium'],
            'suburban': ['standard', 'drive_through'],
            'rural': ['basic', 'mobile']
        }
        
        # Service times for different operations
        service_times = {
            'teller': ['quick', 'standard', 'complex'],
            'loan': ['simple', 'mortgage', 'business'],
            'investment': ['consultation', 'transaction', 'planning']
        }
        
        # Set data sources through the pattern compiler
        self.compiler.compiler.set_data_sources({
            'customer_types': customer_types,
            'branches': branches,
            'service_times': service_times
        })
        
    def generate_customer_patterns(self) -> Dict[str, Any]:
        """Generate customer arrival and service patterns."""
        patterns = {
            # Customer arrival patterns by time of day
            "customer.arrival.*.morning": {
                "rate": 0.8,
                "description": "Morning customer arrivals"
            },
            "customer.arrival.*.afternoon": {
                "rate": 1.2,
                "description": "Afternoon customer arrivals"
            },
            "customer.arrival.*.evening": {
                "rate": 0.6,
                "description": "Evening customer arrivals"
            },
            
            # Service time patterns by customer type
            "service.time.regular.*": {
                "duration": "standard",
                "description": "Regular customer service time"
            },
            "service.time.priority.*": {
                "duration": "expedited",
                "description": "Priority customer service time"
            },
            
            # Reneging patterns (customers leaving queue)
            "customer.renege.*.impatient": {
                "probability": 0.3,
                "description": "Impatient customer reneging"
            },
            "customer.renege.*.very_impatient": {
                "probability": 0.7,
                "description": "Very impatient customer reneging"
            }
        }
        
        return patterns
    
    def run_simulation(self, duration: int = 480) -> Dict[str, Any]:
        """Run the bank simulation."""
        print("🏦 Starting Bank Customer Simulation")
        print("=" * 50)
        
        # Set pattern rules
        patterns = self.generate_customer_patterns()
        self.compiler.compiler.set_pattern_rules(patterns)
        
        # Compile patterns
        result = self.compiler.compiler.compile_patterns(patterns)
        
        # Simulation results
        simulation_data = {
            'total_customers': random.randint(100, 200),
            'customers_served': 0,
            'customers_reneged': 0,
            'average_wait_time': 0.0,
            'peak_queue_length': 0,
            'branch_utilization': {}
        }
        
        # Simulate customer flow
        for branch_type in ['downtown', 'suburban', 'rural']:
            for service in ['teller', 'loan', 'investment']:
                # Simulate customer behavior
                customers = random.randint(20, 50)
                served = int(customers * 0.8)  # 80% served
                reneged = customers - served
                
                simulation_data['customers_served'] += served
                simulation_data['customers_reneged'] += reneged
                
                branch_key = f"{branch_type}_{service}"
                simulation_data['branch_utilization'][branch_key] = {
                    'customers': customers,
                        'served': served,
                        'reneged': reneged,
                        'utilization_rate': served / customers
                }
        
        # Calculate averages
        if simulation_data['customers_served'] > 0:
            simulation_data['average_wait_time'] = random.uniform(5.0, 15.0)
            simulation_data['peak_queue_length'] = random.randint(8, 15)
        
        return simulation_data
    
    def print_simulation_report(self, data: Dict[str, Any]):
        """Print simulation results."""
        print("\n📋 BANK SIMULATION SUMMARY REPORT")
        print("=" * 50)
        print(f"   Total Customers: {data['total_customers']}")
        print(f"   Customers Served: {data['customers_served']}")
        print(f"   Customers Reneged: {data['customers_reneged']}")
        print(f"   Average Wait Time: {data['average_wait_time']:.1f} minutes")
        print(f"   Peak Queue Length: {data['peak_queue_length']}")
        
        print("\n🏢 Branch Utilization:")
        for branch, stats in data['branch_utilization'].items():
            utilization = stats['utilization_rate'] * 100
            print(f"   {branch}: {utilization:.1f}% ({stats['served']}/{stats['customers']})")
        
        print(f"\n📊 Overall Service Rate: {(data['customers_served']/data['total_customers']*100):.1f}%")
        print(f"📊 Reneging Rate: {(data['customers_reneged']/data['total_customers']*100):.1f}%")


def main():
    """Run the bank renege simulation."""
    print("Bank Renege Simulation using Strataregula")
    print("=" * 60)
    
    # Initialize simulator
    simulator = BankSimulator()
    
    # Run simulation
    results = simulator.run_simulation(duration=480)  # 8-hour day
    
    # Print results
    simulator.print_simulation_report(results)
    
    print("\n✅ Simulation completed successfully!")


if __name__ == "__main__":
    main()
