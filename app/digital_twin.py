import psutil
import platform
import json
from datetime import datetime

from app.docker_monitor import get_docker_metrics


def get_system_telemetry():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "platform": platform.system(),
        "kernel": platform.release(),

        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=0.5),
            "cores": psutil.cpu_count()
        },

        "memory": {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "available_gb": round(memory.available / (1024 ** 3), 2),
            "usage_percent": memory.percent
        },

        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "usage_percent": disk.percent
        }
    }


def get_digital_twin():

    return {
        "timestamp": datetime.now().isoformat(),

        "system": get_system_telemetry(),

        "docker": get_docker_metrics()
    }


if __name__ == "__main__":

    twin = get_digital_twin()

    print(json.dumps(twin, indent=2))
