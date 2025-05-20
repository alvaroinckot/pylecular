#!/usr/bin/env python3
import argparse
import asyncio
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import List

from pylecular.broker import Broker
from pylecular.service import Service
from pylecular.settings import Settings


def import_services_from_directory(directory_path: str) -> List[Service]:
    """Dynamically import all Python files in a directory and return all Service classes."""
    services = []
    directory = Path(directory_path)
    
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Directory {directory_path} does not exist or is not a directory")

    # Get all Python files in the directory
    python_files = list(directory.glob("*.py"))
    if not python_files:
        print(f"No Python files found in directory {directory_path}")
        return services

    # Add the directory to path to allow imports
    sys.path.insert(0, str(directory.parent))
    
    for file_path in python_files:
        try:
            # Skip __init__ and other special files
            if file_path.name.startswith("__"):
                continue
                
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            
            if spec is None or spec.loader is None:
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all Service subclasses in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, Service) and obj != Service):
                    try:
                        service_instance = obj()
                        services.append(service_instance)
                        print(f"Found service: {service_instance.name}")
                    except Exception as e:
                        print(f"Error instantiating service {name}: {e}")
                        
        except Exception as e:
            print(f"Error importing {file_path}: {e}")
                
    return services


async def run_broker(
    service_dir: str, 
    broker_id: str, 
    transporter: str, 
    log_level: str,
    log_format: str = "PLAIN",
    namespace: str = "default"
):
    """Create a broker, register all services from the directory, and wait for termination."""
    settings = Settings(
        transporter=transporter,
        log_level=log_level,
        log_format=log_format
    )
    
    print(f"Starting Pylecular broker '{broker_id}' with transporter: {transporter}")
    print(f"Loading services from directory: {service_dir}")
    
    try:
        broker = Broker(broker_id, settings=settings, namespace=namespace)
        
        # Import and register all services
        services = import_services_from_directory(service_dir)
        
        if not services:
            print(f"Warning: No services found in directory {service_dir}. Broker will start without services.")
        else:
            print(f"Registering {len(services)} service(s):")
            for service in services:
                broker.register(service)
                print(f"  - {service.name}")
            
        # Start the broker
        print("Starting broker...")
        await broker.start()
        
        print(f"Broker '{broker_id}' is running. Press Ctrl+C to stop.")
        print("Waiting for requests...")
        
        # Wait for termination
        await broker.wait_for_shutdown()
        
    except Exception as e:
        print(f"Error starting broker: {e}")
        raise


def main():
    """Entry point for the CLI command."""
    parser = argparse.ArgumentParser(
        description="Pylecular - Run a service broker and load services from a directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "service_dir", 
        type=str, 
        help="Directory containing service files"
    )
    parser.add_argument(
        "--broker-id", "-b", 
        type=str, 
        default="node-" + os.path.basename(os.getcwd()), 
        help="Broker ID"
    )
    parser.add_argument(
        "--transporter", "-t", 
        type=str, 
        default="nats://localhost:4222",
        help="Transporter URL (e.g., nats://localhost:4222)"
    )
    parser.add_argument(
        "--log-level", "-l", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level"
    )
    parser.add_argument(
        "--log-format", "-f", 
        type=str, 
        default="PLAIN",
        choices=["PLAIN", "JSON"],
        help="Log format"
    )
    parser.add_argument(
        "--namespace", "-n", 
        type=str, 
        default="default",
        help="Service namespace"
    )
    
    args = parser.parse_args()
    
    # Convert the service_dir to absolute path if it's relative
    service_dir = args.service_dir
    if not os.path.isabs(service_dir):
        service_dir = os.path.abspath(service_dir)
    
    try:
        asyncio.run(run_broker(
            service_dir=service_dir,
            broker_id=args.broker_id,
            transporter=args.transporter,
            log_level=args.log_level,
            log_format=args.log_format,
            namespace=args.namespace
        ))
    except KeyboardInterrupt:
        print("\nBroker stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
