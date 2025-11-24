#!/usr/bin/env python3
"""
Integration test runner that automates Docker Compose and test execution.
"""

import subprocess
import sys
import time
from pathlib import Path


class IntegrationTestRunner:
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.node_services_dir = self.test_dir / "node_services"
        self.compose_file = self.test_dir / "docker-compose.yaml"
        self.test_files = [
            "test_service_discovery.py",
            "test_basic_communication.py",
            "test_events.py",
        ]
        self.docker_compose_process = None
        self.node_process = None

    def print_status(self, message, status="INFO"):
        """Print formatted status message."""
        symbols = {"INFO": "ℹ️", "OK": "✓", "ERROR": "✗", "WAIT": "⏳"}  # noqa: RUF001
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")

    def run_command(self, cmd, cwd=None, capture=False):
        """Run a shell command."""
        if capture:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False
            )
            return result.returncode, result.stdout, result.stderr
        else:
            return subprocess.run(cmd, shell=True, cwd=cwd, check=False).returncode, "", ""

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        self.print_status("Checking dependencies...", "WAIT")

        # Check Docker
        code, _, _ = self.run_command("docker --version", capture=True)
        if code != 0:
            self.print_status("Docker is not installed or not running", "ERROR")
            return False

        # Check Docker Compose
        code, _, _ = self.run_command("docker compose version", capture=True)
        if code != 0:
            code, _, _ = self.run_command("docker-compose --version", capture=True)
            if code != 0:
                self.print_status("Docker Compose is not installed", "ERROR")
                return False

        # Check Node.js
        code, _, _ = self.run_command("node --version", capture=True)
        if code != 0:
            self.print_status("Node.js is not installed", "ERROR")
            return False

        self.print_status("All dependencies found", "OK")
        return True

    def setup_node_services(self):
        """Install Node.js dependencies."""
        self.print_status("Setting up Node.js services...", "WAIT")

        if not self.node_services_dir.exists():
            self.print_status(
                f"Node services directory not found: {self.node_services_dir}", "ERROR"
            )
            return False

        # Check if node_modules exists
        node_modules = self.node_services_dir / "node_modules"
        if not node_modules.exists():
            self.print_status("Installing Node.js dependencies...", "WAIT")
            code, _, err = self.run_command("npm install", cwd=self.node_services_dir)
            if code != 0:
                self.print_status(f"Failed to install Node dependencies: {err}", "ERROR")
                return False

        self.print_status("Node.js services ready", "OK")
        return True

    def start_docker_compose(self):
        """Start Docker Compose services."""
        self.print_status("Starting Docker Compose services...", "WAIT")

        # Stop any existing containers
        self.run_command("docker compose down", cwd=self.test_dir, capture=True)

        # Start services
        code, _, err = self.run_command("docker compose up -d", cwd=self.test_dir)
        if code != 0:
            self.print_status(f"Failed to start Docker Compose: {err}", "ERROR")
            return False

        # Wait for NATS to be ready
        self.print_status("Waiting for NATS to be ready...", "WAIT")
        for _i in range(30):
            code, out, _ = self.run_command(
                "docker compose exec -T nats nc -zv localhost 4222", cwd=self.test_dir, capture=True
            )
            if code == 0 or "succeeded" in out.lower() or "connected" in out.lower():
                self.print_status("NATS is ready", "OK")
                return True
            time.sleep(1)

        # Alternative check
        code, _, _ = self.run_command("nc -zv localhost 4222", capture=True)
        if code == 0:
            self.print_status("NATS is ready", "OK")
            return True

        self.print_status("NATS failed to start", "ERROR")
        return False

    def start_node_services(self):
        """Start Node.js Moleculer services."""
        self.print_status("Starting Node.js Moleculer services...", "WAIT")

        # Start Node services in background
        self.node_process = subprocess.Popen(
            ["node", "index.js"],
            cwd=self.node_services_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a bit for services to initialize
        time.sleep(3)

        # Check if process is still running
        if self.node_process.poll() is not None:
            stdout, stderr = self.node_process.communicate()
            self.print_status(f"Node services failed to start: {stderr}", "ERROR")
            return False

        self.print_status("Node.js services started", "OK")
        return True

    def run_python_tests(self):
        """Run Python integration tests."""
        self.print_status("Running Python integration tests...", "WAIT")

        all_passed = True
        results = {}

        for test_file in self.test_files:
            test_path = self.test_dir / test_file
            if not test_path.exists():
                self.print_status(f"Test file not found: {test_file}", "ERROR")
                results[test_file] = "NOT_FOUND"
                continue

            self.print_status(f"Running {test_file}...", "WAIT")

            # Run the test
            code, stdout, stderr = self.run_command(
                f"python {test_file}", cwd=self.test_dir, capture=True
            )

            if code == 0:
                self.print_status(f"{test_file} PASSED", "OK")
                results[test_file] = "PASSED"
            else:
                self.print_status(f"{test_file} FAILED", "ERROR")
                if stdout:
                    print(f"  Output: {stdout}")
                if stderr:
                    print(f"  Error: {stderr}")
                results[test_file] = "FAILED"
                all_passed = False

        print("\n" + "=" * 50)
        print("INTEGRATION TEST RESULTS")
        print("=" * 50)
        for test, result in results.items():
            symbol = "✓" if result == "PASSED" else "✗"
            print(f"{symbol} {test}: {result}")
        print("=" * 50)

        return all_passed

    def cleanup(self):
        """Clean up Docker Compose and Node services."""
        self.print_status("Cleaning up...", "WAIT")

        # Stop Node services
        if self.node_process:
            self.print_status("Stopping Node.js services...", "WAIT")
            self.node_process.terminate()
            try:
                self.node_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.node_process.kill()

        # Stop Docker Compose
        self.print_status("Stopping Docker Compose...", "WAIT")
        self.run_command("docker compose down", cwd=self.test_dir, capture=True)

        self.print_status("Cleanup complete", "OK")

    def run(self):
        """Run the complete integration test suite."""
        try:
            # Check dependencies
            if not self.check_dependencies():
                return False

            # Setup Node services
            if not self.setup_node_services():
                return False

            # Start Docker Compose
            if not self.start_docker_compose():
                return False

            # Start Node services
            if not self.start_node_services():
                return False

            # Wait a bit for everything to stabilize
            self.print_status("Waiting for services to stabilize...", "WAIT")
            time.sleep(3)

            # Run tests
            success = self.run_python_tests()

            return success

        except KeyboardInterrupt:
            self.print_status("Interrupted by user", "ERROR")
            return False
        except Exception as e:
            self.print_status(f"Unexpected error: {e}", "ERROR")
            return False
        finally:
            self.cleanup()


def main():
    runner = IntegrationTestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
