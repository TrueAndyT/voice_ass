#!/usr/bin/env python3
"""
Manages the lifecycle of all microservices, including starting,
stopping, and monitoring their health.
"""

import subprocess
import time
import atexit
import os
import signal
from .utils.logger import app_logger

class ServiceManager:
    def __init__(self):
        self.log = app_logger.get_logger("service_manager")
        self.services = []
        atexit.register(self.stop_all_services)

    def start_service(self, name, command, host="127.0.0.1", port=8000):
        """Start a microservice as a subprocess."""
        self.log.debug(f"Starting service: {name} on {host}:{port}")
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root,
                preexec_fn=os.setsid  # So we can later kill the whole process group
            )
            self.services.append({
                "name": name,
                "process": process,
                "pid": process.pid,
                "pgid": os.getpgid(process.pid),
                "host": host,
                "port": port,
                "command": command
            })
            self.log.debug(f"Service '{name}' started with PID: {process.pid}")
            return process
        except Exception as e:
            self.log.error(f"Failed to start service '{name}': {e}", exc_info=True)
            return None

    def stop_service(self, name):
        """Stop a specific microservice by name."""
        for service in list(self.services):  # Copy to avoid mutation issues
            if service["name"] == name:
                self._terminate_service(service)
                self.services.remove(service)
                break

    def stop_all_services(self):
        """Stop all running microservices."""
        self.log.debug("Stopping all services...")
        for service in list(self.services):
            self._terminate_service(service)
        self.log.debug("All services stopped")

    def _terminate_service(self, service):
        """Terminate a subprocess safely and forcibly if needed."""
        proc = service['process']
        name = service['name']
        pid = service['pid']
        pgid = service.get('pgid', None)

        self.log.debug(f"Terminating service: {name} (PID: {pid})")

        try:
            if pgid:
                os.killpg(pgid, signal.SIGTERM)
            else:
                proc.terminate()
        except Exception as e:
            self.log.warning(f"Error sending SIGTERM to {name}: {e}")

        try:
            proc.wait(timeout=5)
            self.log.debug(f"Service '{name}' exited cleanly")
        except subprocess.TimeoutExpired:
            self.log.warning(f"Service '{name}' did not exit in time. Forcing kill.")
            try:
                if pgid:
                    os.killpg(pgid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait(timeout=3)
                self.log.debug(f"Service '{name}' forcibly killed")
            except Exception as e:
                self.log.error(f"Failed to kill service '{name}': {e}")

    def check_service_health(self, name):
        """Check if a service is running and responsive."""
        # Placeholder: implement actual HTTP health check if needed
        for service in self.services:
            if service["name"] == name:
                return service["process"].poll() is None
        return False
