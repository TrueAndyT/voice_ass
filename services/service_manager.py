#!/usr/bin/env python3
"""
Manages the lifecycle of all microservices, including starting,
stopping, and monitoring their health.
"""

import subprocess
import time
import atexit
from .logger import app_logger

class ServiceManager:
    def __init__(self):
        self.log = app_logger.get_logger("service_manager")
        self.services = []
        atexit.register(self.stop_all_services)

    def start_service(self, name, command, host="127.0.0.1", port=8000):
        """Start a microservice as a subprocess."""
        self.log.info(f"Starting service: {name} on {host}:{port}")
        try:
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            self.services.append({
                "name": name,
                "process": process,
                "host": host,
                "port": port,
                "command": command
            })
            self.log.info(f"Service '{name}' started with PID: {process.pid}")
            return process
        except Exception as e:
            self.log.error(f"Failed to start service '{name}': {e}", exc_info=True)
            return None

    def stop_service(self, name):
        """Stop a specific microservice by name."""
        for service in self.services:
            if service["name"] == name:
                self.log.info(f"Stopping service: {name} (PID: {service['process'].pid})")
                service['process'].terminate()
                service['process'].wait()
                self.log.info(f"Service '{name}' stopped")
                self.services.remove(service)
                break

    def stop_all_services(self):
        """Stop all running microservices."""
        self.log.info("Stopping all services...")
        for service in self.services:
            self.log.info(f"Stopping service: {service['name']} (PID: {service['process'].pid})")
            service['process'].terminate()
            service['process'].wait()
        self.log.info("All services stopped")

    def check_service_health(self, name):
        """Check if a service is running and responsive."""
        # TODO: Implement health check logic (e.g., HTTP request)
        pass

