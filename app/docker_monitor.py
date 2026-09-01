import subprocess
import json


def get_docker_metrics():

    try:
        result = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{json .}}"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "available": False,
                "error": result.stderr.strip()
            }

        containers = []

        for line in result.stdout.splitlines():

            if not line.strip():
                continue

            data = json.loads(line)

            containers.append({
                "name": data.get("Name"),
                "cpu_percent": data.get("CPUPerc"),
                "memory_usage": data.get("MemUsage"),
                "memory_percent": data.get("MemPerc"),
                "network_io": data.get("NetIO"),
                "block_io": data.get("BlockIO"),
                "pids": data.get("PIDs")
            })

        return {
            "available": True,
            "container_count": len(containers),
            "containers": containers
        }

    except FileNotFoundError:

        return {
            "available": False,
            "error": "Docker command not found"
        }

    except subprocess.TimeoutExpired:

        return {
            "available": False,
            "error": "Docker stats timed out"
        }


if __name__ == "__main__":

    print(
        json.dumps(
            get_docker_metrics(),
            indent=2
        )
    )
