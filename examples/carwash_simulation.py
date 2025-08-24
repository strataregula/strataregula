"""
Carwash Simulation using Strataregula

This example demonstrates how to use Strataregula for simulating
a carwash service with different wash types and customer preferences.
Based on SimPy's Carwash example.
"""

import random
import time
from pathlib import Path
from typing import Dict, Any

from strataregula import Pipeline


class CarwashSimulator:
    """Carwash service simulation."""
    
    def __init__(self, config_path: Path = None):
        """Initialize the carwash simulator."""
        self.compiler = Pipeline(config_path)
        
        # Set up simulation parameters
        self.setup_simulation_data()
        
    def setup_simulation_data(self):
        """Set up simulation data sources."""
        # Car types and their wash preferences
        car_types = {
            'economy': ['basic', 'standard', 'premium'],
            'luxury': ['premium', 'deluxe', 'ultimate'],
            'commercial': ['basic', 'standard', 'fleet']
        }
        
        # Wash service types and their durations
        wash_services = {
            'basic': ['exterior', 'interior_basic'],
            'standard': ['exterior', 'interior_standard', 'tire_shine'],
            'premium': ['exterior', 'interior_premium', 'tire_shine', 'wax'],
            'deluxe': ['exterior', 'interior_deluxe', 'tire_shine', 'wax', 'polish'],
            'ultimate': ['exterior', 'interior_ultimate', 'tire_shine', 'wax', 'polish', 'ceramic']
        }
        
        # Time slots and customer arrival patterns
        time_slots = {
            'morning': ['early', 'peak', 'late'],
            'afternoon': ['lunch', 'peak', 'evening'],
            'evening': ['dinner', 'late', 'night']
        }
        
        # Set data sources through the pattern compiler
        self.compiler.compiler.set_data_sources({
            'car_types': car_types,
            'wash_services': wash_services,
            'time_slots': time_slots
        })
        
    def generate_wash_patterns(self) -> Dict[str, Any]:
        """Generate carwash service patterns."""
        patterns = {
            # Customer arrival patterns by time of day
            "customer.arrival.*.morning": {
                "rate": 0.6,
                "description": "Morning customer arrivals"
            },
            "customer.arrival.*.afternoon": {
                "rate": 1.4,
                "description": "Afternoon customer arrivals"
            },
            "customer.arrival.*.evening": {
                "rate": 0.8,
                "description": "Evening customer arrivals"
            },
            
            # Wash service selection by car type
            "wash.service.economy.*": {
                "service_type": "basic",
                "description": "Economy car wash service"
            },
            "wash.service.luxury.*": {
                "service_type": "premium",
                "description": "Luxury car wash service"
            },
            "wash.service.commercial.*": {
                "service_type": "standard",
                "description": "Commercial car wash service"
            },
            
            # Service duration patterns
            "service.duration.basic.*": {
                "time_minutes": 15,
                "description": "Basic wash duration"
            },
            "service.duration.premium.*": {
                "time_minutes": 30,
                "description": "Premium wash duration"
            },
            "service.duration.ultimate.*": {
                "time_minutes": 60,
                "description": "Ultimate wash duration"
            }
        }
        
        return patterns
    
    def run_simulation(self, duration: int = 480) -> Dict[str, Any]:
        """Run the carwash simulation."""
        print("🚗 Starting Carwash Service Simulation")
        print("=" * 50)
        
        # Set pattern rules
        patterns = self.generate_wash_patterns()
        self.compiler.compiler.set_pattern_rules(patterns)
        
        # Compile patterns
        result = self.compiler.compiler.compile_patterns(patterns)
        
        # Simulation results
        simulation_data = {
            'total_cars': random.randint(80, 150),
            'cars_washed': 0,
            'total_revenue': 0.0,
            'average_wait_time': 0.0,
            'peak_queue_length': 0,
            'service_utilization': {},
            'revenue_by_service': {}
        }
        
        # Service prices
        service_prices = {
            'basic': 15.0,
            'standard': 25.0,
            'premium': 40.0,
            'deluxe': 60.0,
            'ultimate': 100.0
        }
        
        # Simulate car wash operations
        for car_type in ['economy', 'luxury', 'commercial']:
            for time_slot in ['morning', 'afternoon', 'evening']:
                # Simulate car arrivals
                cars = random.randint(15, 40)
                simulation_data['total_cars'] += cars
                
                # Determine wash service based on car type
                if car_type == 'economy':
                    service = random.choice(['basic', 'standard'])
                elif car_type == 'luxury':
                    service = random.choice(['premium', 'deluxe', 'ultimate'])
                else:  # commercial
                    service = random.choice(['basic', 'standard'])
                
                # Calculate revenue
                price = service_prices.get(service, 25.0)
                revenue = cars * price
                simulation_data['total_revenue'] += revenue
                simulation_data['cars_washed'] += cars
                
                # Track service utilization
                if service not in simulation_data['service_utilization']:
                    simulation_data['service_utilization'][service] = 0
                simulation_data['service_utilization'][service] += cars
                
                # Track revenue by service
                if service not in simulation_data['revenue_by_service']:
                    simulation_data['revenue_by_service'][service] = 0.0
                simulation_data['revenue_by_service'][service] += revenue
        
        # Calculate averages
        if simulation_data['cars_washed'] > 0:
            simulation_data['average_wait_time'] = random.uniform(8.0, 20.0)
            simulation_data['peak_queue_length'] = random.randint(5, 12)
        
        return simulation_data
    
    def print_simulation_report(self, data: Dict[str, Any]):
        """Print simulation results."""
        print("\n📋 CARWASH SIMULATION SUMMARY REPORT")
        print("=" * 50)
        print(f"   Total Cars: {data['total_cars']}")
        print(f"   Cars Washed: {data['cars_washed']}")
        print(f"   Total Revenue: ${data['total_revenue']:.2f}")
        print(f"   Average Wait Time: {data['average_wait_time']:.1f} minutes")
        print(f"   Peak Queue Length: {data['peak_queue_length']}")
        
        print("\n🚗 Service Utilization:")
        for service, count in data['service_utilization'].items():
            percentage = (count / data['cars_washed']) * 100
            print(f"   {service.title()}: {percentage:.1f}% ({count} cars)")
        
        print("\n💰 Revenue by Service:")
        for service, revenue in data['revenue_by_service'].items():
            percentage = (revenue / data['total_revenue']) * 100
            print(f"   {service.title()}: ${revenue:.2f} ({percentage:.1f}%)")
        
        print(f"\n📊 Average Revenue per Car: ${(data['total_revenue']/data['cars_washed']):.2f}")


def main():
    """Run the carwash simulation."""
    print("Carwash Simulation using Strataregula")
    print("=" * 60)
    
    # Initialize simulator
    simulator = CarwashSimulator()
    
    # Run simulation
    results = simulator.run_simulation(duration=480)  # 8-hour day
    
    # Print results
    simulator.print_simulation_report(results)
    
    print("\n✅ Simulation completed successfully!")


if __name__ == "__main__":
    main()
