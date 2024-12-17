from os import system
from os.path import exists
from sys import platform
from time import sleep

import argparse

parser = argparse.ArgumentParser(description='Execution script')
parser.add_argument("command", type=str, choices=["start", "stop"], help="Command to execute")
parser.add_argument("--attached", action="store_true", help="Run the docker containers in attached mode")
args = parser.parse_args()

match args.command:
	case "start":
		if exists("redis"):
			system("rmdir redis" if platform == "win32" else "rm -r ./redis" if platform == "linux" else "")
		system("docker compose up" + (" -d" if not args.attached else ""))
	case "stop":
		system("docker compose down")
		sleep(1)
		if exists("redis"):
			system("rmdir redis" if platform == "win32" else "rm -r ./redis" if platform == "linux" else "")
	case _:
		raise ValueError(f"Unknown command: {args.command}")
