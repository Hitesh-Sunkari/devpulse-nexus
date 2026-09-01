import psutil
import platform
from datetime import datetime


def get_system_metrics():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = process.info

            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": info["memory_percent"]
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Highest CPU processes
    top_cpu = sorted(
        processes,
        key=lambda x: x["cpu_percent"],
        reverse=True
    )[:5]

    # Highest memory processes
    top_memory = sorted(
        processes,
        key=lambda x: x["memory_percent"],
        reverse=True
    )[:5]

    return {
        "timestamp": datetime.now().isoformat(),

        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "machine": platform.machine()
        },

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
        },

        "top_cpu_processes": top_cpu,
        "top_memory_processes": top_memory
    }


if __name__ == "__main__":

    import json

    metrics = get_system_metrics()

    print(json.dumps(metrics, indent=2))
