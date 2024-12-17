from signal import signal, SIGINT, SIGTERM
from time import sleep

import argparse
import logging
import rpyc

DELAY = 5 # Delay before retrying

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Client')
parser.add_argument("n", metavar="factorials", type=int, nargs="+", help="Factorials to calculate")
parser.add_argument("--host", type=str, default="middleware", help="Middleware host")
parser.add_argument("--port", type=int, default=21212, help="Middleware port")
args = parser.parse_args()

def _on_exit(sig, frame):
	logging.info(f"[_on_exit] Signal captured; Exiting...")
	if c: c.close() # Close the connection to the middleware

c = None # Connection to the middleware
if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	logging.info(f"Starting the client...")

	logging.debug(f"Setting the signal handlers...")
	signal(SIGINT, _on_exit) # Handle docker stop
	signal(SIGTERM, _on_exit) # Handle docker stop

	logging.debug(f"Connecting to the middleware at {args.host}:{args.port}...")
	try:
		c = rpyc.connect(args.host, args.port) # Connect to the middleware
		logging.debug(f"Connected to the middleware at {args.host}:{args.port}")

		task_ids = {} # IDs of the queued numbers
		for n in args.n:
			logging.debug(f"Queuing {n}...")
			task_id = None # ID of the queued number
			task_id = c.root.add_queue(n) # ID of the queued number
			while not task_id: # Retry if the middleware gives None
				sleep(DELAY) # Give time before retrying
				task_id = c.root.add_queue(n) # ID of the queued number
			logging.info(f"Queued {n} with ID {task_id}")
			task_ids.update({task_id: n}) # Store the result ID of the queued number

		for task_id, n in task_ids.items():
			logging.debug(f"Getting result for {n}...")
			result = None # Result of the queued number
			result = c.root.get_result(task_id) # Result of the queued number
			while not result: # Retry if the middleware gives None
				sleep(DELAY) # Give time before retrying
				result = c.root.get_result(task_id) # Result of the queued number
			logging.info(f"Result for {n}: {result}")
	except Exception as e:
		logging.error(f"Error: {e}")
		exit(1)
