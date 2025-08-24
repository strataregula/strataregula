"""
Machine Shop Simulation using Strataregula

This example demonstrates how to use Strataregula for simulating
a machine shop with different machine types and job processing.
Based on SimPy's Machine Shop example.
"""

import random
import time
from pathlib import Path
from typing import Dict, Any

from strataregula import Pipeline


class MachineShopSimulator:
    """Machine shop production simulation."""
    
    def __init__(self, config_path: Path = None):
        """Initialize the machine shop simulator."""
        self.compiler = Pipeline(config_path)
        
        # Set up simulation parameters
        self.setup_simulation_data()
        
    def setup_simulation_data(self):
        """Set up simulation data sources."""
        # Machine types and their capabilities
        machine_types = {
            'lathe': ['small', 'medium', 'large'],
            'milling': ['cnc', 'manual', 'precision'],
            'drilling': ['radial', 'bench', 'portable'],
            'grinding': ['surface', 'cylindrical', 'tool']
        }
        
        # Job types and their requirements
        job_types = {
            'simple': ['basic_turning', 'drilling', 'sanding'],
            'complex': ['precision_machining', 'multi_axis', 'finishing'],
            'custom': ['prototype', 'one_off', 'specialty']
        }
        
        # Production shifts and scheduling
        production_shifts = {
            'day': ['morning', 'afternoon'],
            'night': ['evening', 'graveyard'],
            'weekend': ['saturday', 'sunday']
        }
        
        # Set data sources through the pattern compiler
        self.compiler.compiler.set_data_sources({
            'machine_types': machine_types,
            'job_types': job_types,
            'production_shifts': production_shifts
        })
        
    def generate_production_patterns(self) -> Dict[str, Any]:
        """Generate machine shop production patterns."""
        patterns = {
            # Job arrival patterns by shift
            "job.arrival.*.day": {
                "rate": 1.2,
                "description": "Day shift job arrivals"
            },
            "job.arrival.*.night": {
                "rate": 0.8,
                "description": "Night shift job arrivals"
            },
            "job.arrival.*.weekend": {
                "rate": 0.4,
                "description": "Weekend shift job arrivals"
            },
            
            # Machine assignment by job type
            "machine.assignment.simple.*": {
                "machine_type": "basic",
                "description": "Simple job machine assignment"
            },
            "machine.assignment.complex.*": {
                "machine_type": "precision",
                "description": "Complex job machine assignment"
            },
            "machine.assignment.custom.*": {
                "machine_type": "specialty",
                "description": "Custom job machine assignment"
            },
            
            # Processing time patterns
            "processing.time.simple.*": {
                "time_hours": 2.0,
                "description": "Simple job processing time"
            },
            "processing.time.complex.*": {
                "time_hours": 8.0,
                "description": "Complex job processing time"
            },
            "processing.time.custom.*": {
                "time_hours": 12.0,
                "description": "Custom job processing time"
            }
        }
        
        return patterns
    
    def run_simulation(self, duration: int = 168) -> Dict[str, Any]:
        """Run the machine shop simulation."""
        print("🏭 Starting Machine Shop Production Simulation")
        print("=" * 50)
        
        # Set pattern rules
        patterns = self.generate_production_patterns()
        self.compiler.compiler.set_pattern_rules(patterns)
        
        # Compile patterns
        result = self.compiler.compiler.compile_patterns(patterns)
        
        # Simulation results
        simulation_data = {
            'total_jobs': random.randint(60, 120),
            'jobs_completed': 0,
            'total_production_hours': 0.0,
            'average_processing_time': 0.0,
            'machine_utilization': {},
            'production_by_shift': {},
            'quality_metrics': {}
        }
        
        # Machine capacities and efficiencies
        machine_capacities = {
            'lathe': {'capacity': 8, 'efficiency': 0.85},
            'milling': {'capacity': 6, 'efficiency': 0.90},
            'drilling': {'capacity': 10, 'efficiency': 0.80},
            'grinding': {'capacity': 4, 'efficiency': 0.95}
        }
        
        # Simulate production operations
        for shift_type in ['day', 'night', 'weekend']:
            for job_type in ['simple', 'complex', 'custom']:
                # Simulate job arrivals
                jobs = random.randint(10, 30)
                simulation_data['total_jobs'] += jobs
                
                # Determine processing time based on job type
                if job_type == 'simple':
                    processing_time = random.uniform(1.5, 3.0)
                elif job_type == 'complex':
                    processing_time = random.uniform(6.0, 10.0)
                else:  # custom
                    processing_time = random.uniform(10.0, 15.0)
                
                # Calculate production hours
                production_hours = jobs * processing_time
                simulation_data['total_production_hours'] += production_hours
                simulation_data['jobs_completed'] += jobs
                
                # Track production by shift
                if shift_type not in simulation_data['production_by_shift']:
                    simulation_data['production_by_shift'][shift_type] = 0
                simulation_data['production_by_shift'][shift_type] += jobs
                
                # Track machine utilization
                for machine_type in ['lathe', 'milling', 'drilling', 'grinding']:
                    if machine_type not in simulation_data['machine_utilization']:
                        simulation_data['machine_utilization'][machine_type] = {
                            'jobs_processed': 0,
                            'hours_used': 0.0,
                            'efficiency': 0.0
                        }
                    
                    # Simulate machine usage
                    machine_jobs = int(jobs * random.uniform(0.2, 0.4))
                    machine_hours = machine_jobs * processing_time
                    
                    simulation_data['machine_utilization'][machine_type]['jobs_processed'] += machine_jobs
                    simulation_data['machine_utilization'][machine_type]['hours_used'] += machine_hours
                    
                    # Calculate efficiency
                    capacity = machine_capacities[machine_type]['capacity']
                    efficiency = machine_capacities[machine_type]['efficiency']
                    simulation_data['machine_utilization'][machine_type]['efficiency'] = efficiency
        
        # Calculate averages
        if simulation_data['jobs_completed'] > 0:
            simulation_data['average_processing_time'] = simulation_data['total_production_hours'] / simulation_data['jobs_completed']
        
        # Quality metrics
        simulation_data['quality_metrics'] = {
            'first_pass_yield': random.uniform(0.85, 0.95),
            'rework_rate': random.uniform(0.05, 0.15),
            'scrap_rate': random.uniform(0.01, 0.05)
        }
        
        return simulation_data
    
    def print_simulation_report(self, data: Dict[str, Any]):
        """Print simulation results."""
        print("\n📋 MACHINE SHOP SIMULATION SUMMARY REPORT")
        print("=" * 50)
        print(f"   Total Jobs: {data['total_jobs']}")
        print(f"   Jobs Completed: {data['jobs_completed']}")
        print(f"   Total Production Hours: {data['total_production_hours']:.1f}")
        print(f"   Average Processing Time: {data['average_processing_time']:.1f} hours")
        
        print("\n🏭 Production by Shift:")
        for shift, count in data['production_by_shift'].items():
            percentage = (count / data['jobs_completed']) * 100
            print(f"   {shift.title()}: {percentage:.1f}% ({count} jobs)")
        
        print("\n⚙️ Machine Utilization:")
        for machine, stats in data['machine_utilization'].items():
            efficiency = stats['efficiency'] * 100
            print(f"   {machine.title()}: {efficiency:.1f}% efficiency ({stats['jobs_processed']} jobs)")
        
        print("\n📊 Quality Metrics:")
        print(f"   First Pass Yield: {data['quality_metrics']['first_pass_yield']*100:.1f}%")
        print(f"   Rework Rate: {data['quality_metrics']['rework_rate']*100:.1f}%")
        print(f"   Scrap Rate: {data['quality_metrics']['scrap_rate']*100:.1f}%")
        
        print(f"\n📈 Overall Production Rate: {data['jobs_completed']/data['total_production_hours']:.2f} jobs/hour")


def main():
    """Run the machine shop simulation."""
    print("Machine Shop Simulation using Strataregula")
    print("=" * 60)
    
    # Initialize simulator
    simulator = MachineShopSimulator()
    
    # Run simulation
    results = simulator.run_simulation(duration=168)  # 1 week
    
    # Print results
    simulator.print_simulation_report(results)
    
    print("\n✅ Simulation completed successfully!")


if __name__ == "__main__":
    main()
