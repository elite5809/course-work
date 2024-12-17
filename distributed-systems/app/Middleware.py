from random import getrandbits
from signal import signal, SIGINT, SIGTERM
from threading import Thread
from time import sleep

import argparse
import logging
import rpyc

QUEUE_CAPACITY = 10
NODE_PORT = 5000
HEART_DELAY = 60

class Middleware(rpyc.Service):
	### Middleware Methods ###
	def __init__(self):
		logging.info("[__init__] Initializing the middleware...")
		self.nodes = {}
		self.tasks = {}
		self.queue = []
		self.results = {}
	
	### RPyC Methods ###
	def exposed_add_queue(self, n: int):
		logging.debug(f"[queue] Queuing {n}...")

		if len(self.queue) >= QUEUE_CAPACITY:
			logging.debug(f"[queue] Queue is full; Dropping {n}...")
			return None
		
		task_id = None
		while not task_id and not (task_id in self.tasks or task_id in self.results):
			task_id = str(hex(getrandbits(64)))[2:]
		logging.debug(f"[queue] Generated task_id: {task_id}")
		self.tasks.update({task_id: n})
		self.queue.append(task_id)
		logging.info(f"[queue] Queued {n} with task_id {task_id}")
		return task_id

	def exposed_get_result(self, task_id: str):
		logging.info(f"[get_result] Sending result for task_id {task_id}...")
		if task_id in self.results: return self.results.pop(task_id)
		return None
	
	def exposed_register(self, node: str):
		logging.debug(f"[register] Registering {node}...")
		node_id = 1
		while node_id in self.nodes: node_id += 1
		logging.info(f"[register] Registered {node} with ID: {node_id}")
		self.nodes.update({node_id: node})
		return node_id
	
	def exposed_get_registry(self):
		logging.debug(f"[get_registry] Sending the registry...")
		return self.nodes.copy()
	
	def exposed_unregister(self, node_id: int):
		logging.debug(f"[unregister] Unregistering {node_id}...")
		if node_id in self.nodes:
			logging.info(f"[unregister] Unregistered {node_id}")
			self.nodes.pop(node_id)
			return True
		logging.debug(f"[unregister] Unregistration failed")
		return False

	def exposed_get_task(self):
		logging.debug(f"[send_task] Sending task...")
		if not self.queue: return (None, None)
		task_id = self.queue.pop(0)
		n = self.tasks.get(task_id)
		logging.info(f"[send_task] Sending task {task_id} with {n}")
		return (task_id, n)

	def exposed_send_result(self, task_id: str, result: int):
		logging.info(f"[send_result] Got result for task_id {task_id}: {result}")
		if task_id in self.tasks:
			self.tasks.pop(task_id)
			self.results.update({task_id: result})
			return True
		logging.debug(f"[send_result] Task {task_id} not found")
		return False

def _on_exit(sig, frame):
	logging.info("[_on_exit] Signal captured; Exiting...")
	logging.debug("[_on_exit] Setting the close flag...")
	global close
	close = True
	logging.debug("[_on_exit] Joining the heartbeat thread...")
	if heartbeat_thread: heartbeat_thread.join()
	logging.debug("[_on_exit] Closing the server...")
	if server: server.close()

### Threaded Methods ###
def heartbeat(mw_inst: Middleware, close_callback):
	logging.info("[heartbeat] Heartbeat thread started")
	count = 0
	while not close_callback():
		if count != 0: count %= HEART_DELAY
		elif not mw_inst.nodes: continue
		else:
			for node_id, node in mw_inst.nodes.items():
				if close_callback(): break
				try:
					node_conn = rpyc.connect(node, port=NODE_PORT)
					node_conn.ping()
					node_conn.close()
				except Exception as e:
					logging.error(f"Error: {e}")
					mw_inst.unregister(node_id)
		count += 1
		sleep(1)
	logging.info("[heartbeat] Heartbeat thread stopped")

server = None
heartbeat_thread = None
close = False
if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	logging.info("Starting the middleware...")

	parser = argparse.ArgumentParser(description='Middleware')
	parser.add_argument("--port", type=int, default=21212, help="Middleware port")
	args = parser.parse_args()
	logging.debug(f"Middleware port: {args.port}")

	logging.debug("Setting the signal handlers...")
	signal(SIGINT, _on_exit)
	signal(SIGTERM, _on_exit)

	logging.debug("Initializing the RPyC server...")
	middleware = Middleware()
	server = rpyc.ThreadedServer(middleware, port=21212, protocol_config={"allow_public_attrs": True})

	logging.debug("Initializing the heartbeat thread...")
	heartbeat_thread = Thread(target=heartbeat, args=[middleware, lambda: close])
	heartbeat_thread.start()

	server.start()
