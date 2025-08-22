#!/usr/bin/env python3
"""Command line interface for the Pylecular framework.

This module provides the CLI tool for running Pylecular service brokers
with automatic service discovery and registration from directories.
"""

import argparse
import asyncio
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import List, Optional

from .broker import ServiceBroker
from .service import Service
from .settings import Settings


class ServiceImportError(Exception):
    """Exception raised when service import fails."""

    pass


def import_services_from_directory(directory_path: str) -> List[Service]:
    """Dynamically import all Python files in a directory and return Service instances.

    Args:
        directory_path: Path to directory containing service modules

    Returns:
        List of instantiated Service objects

    Raises:
        ServiceImportError: If directory doesn't exist or other import errors
    """
    services: List[Service] = []
    directory = Path(directory_path)

    if not directory.exists():
        raise ServiceImportError(f"Directory {directory_path} does not exist")

    if not directory.is_dir():
        raise ServiceImportError(f"Path {directory_path} is not a directory")

    # Get all Python files in the directory
    python_files = list(directory.glob("*.py"))
    if not python_files:
        print(f"No Python files found in directory {directory_path}")
        return services

    # Add the directory parent to path to allow imports
    directory_parent = str(directory.parent)
    if directory_parent not in sys.path:
        sys.path.insert(0, directory_parent)

    for file_path in python_files:
        try:
            # Skip special files
            if file_path.name.startswith("__") or file_path.name.startswith("."):
                continue

            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))

            if spec is None or spec.loader is None:
                print(f"Warning: Could not create module spec for {file_path}")
                continue

            # Load the module
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"Error executing module {file_path}: {e}")
                continue

            # Find all Service subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, Service)
                    and obj != Service
                    and obj.__module__ == module.__name__
                ):
                    try:
                        # Instantiate the service
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
    namespace: str = "default",
) -> None:
    """Create a broker, register services from directory, and run until termination.

    Args:
        service_dir: Directory containing service modules
        broker_id: Unique identifier for this broker node
        transporter: Transporter connection string
        log_level: Logging level
        log_format: Log output format (PLAIN or JSON)
        namespace: Service namespace for isolation

    Raises:
        ServiceImportError: If service loading fails
        Exception: If broker startup fails
    """
    # Initialize settings
    settings = Settings(transporter=transporter, log_level=log_level, log_format=log_format)

    print(f"Starting Pylecular broker '{broker_id}' with transporter: {transporter}")
    print(f"Loading services from directory: {service_dir}")

    broker: Optional[ServiceBroker] = None
    try:
        # Create the broker
        broker = ServiceBroker(broker_id, settings=settings, namespace=namespace)

        # Import and register all services
        services = import_services_from_directory(service_dir)

        if not services:
            print(f"Warning: No services found in directory {service_dir}")
            print("Broker will start without services")
        else:
            print(f"Registering {len(services)} service(s):")
            for service in services:
                await broker.register(service)
                print(f"  - {service.name}")

        # Start the broker
        print("Starting broker...")
        await broker.start()

        print(f"Broker '{broker_id}' is running. Press Ctrl+C to stop.")
        print("Waiting for requests...")

        # Wait for termination signal
        await broker.wait_for_shutdown()

    except ServiceImportError:
        # Re-raise service import errors as-is
        raise
    except Exception as e:
        print(f"Error running broker: {e}")
        # Ensure broker is stopped if it was started
        if broker:
            try:
                await broker.stop()
            except Exception:
                pass  # Ignore errors during cleanup
        raise


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Pylecular - Run a service broker and load services from a directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Positional arguments
    parser.add_argument("service_dir", type=str, help="Directory containing service files")

    # Optional arguments
    parser.add_argument(
        "--broker-id",
        "-b",
        type=str,
        default=f"node-{os.path.basename(os.getcwd())}",
        help="Unique broker/node identifier",
    )
    parser.add_argument(
        "--transporter",
        "-t",
        type=str,
        default="nats://localhost:4222",
        help="Transporter connection URL (e.g., nats://localhost:4222)",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--log-format",
        "-f",
        type=str,
        default="PLAIN",
        choices=["PLAIN", "JSON"],
        help="Log output format",
    )
    parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        default="default",
        help="Service namespace for logical isolation",
    )

    return parser


def main() -> None:
    """Entry point for the Pylecular CLI command."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Normalize service directory path
    service_dir = args.service_dir
    if not os.path.isabs(service_dir):
        service_dir = os.path.abspath(service_dir)

    try:
        # Run the broker
        asyncio.run(
            run_broker(
                service_dir=service_dir,
                broker_id=args.broker_id,
                transporter=args.transporter,
                log_level=args.log_level,
                log_format=args.log_format,
                namespace=args.namespace,
            )
        )
    except KeyboardInterrupt:
        print("\nBroker stopped by user")
        sys.exit(0)
    except ServiceImportError as e:
        print(f"Service import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
