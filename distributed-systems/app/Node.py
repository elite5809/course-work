from enum import Enum
from json import dumps, loads
from os import environ
from random import random
from signal import raise_signal, signal, SIGINT, SIGTERM
from threading import Thread
from time import sleep

import argparse
import logging
import redis
import rpyc

PORT = 5000
MAX_OPS = 4
HEART_DELAY = 10
WORK_TIMEOUT = 50
RUNTIME_DELAY = 0.01
SLOW_DELAY = 1
SLOW_DELAY_CHANCE = 0.001
BAD_DELAY = 5
BAD_DELAY_CHANCE = 0.0001
CRASH_CHANCE = 0.00001

class NodeState(Enum):
	ELECTION = 0,
	WORKER = 1,
	LEADER = 2

class Node(rpyc.Service):
	### Node Methods ###
	def __init__(self, args):
		logging.debug("[__init__] Initializing the node...")
		### Connection Parameters ###
		self.hostname = environ['HOSTNAME']
		self.mw_conn = rpyc.connect(str(args['mw_name']), str(args['mw_port']))
		self.redis_conn = redis.StrictRedis(str(args['r_name']), str(args['r_port']), decode_responses=True)
		self.delay = float(args['delay'])

		### Registry Variables ###
		try:
			self.node_id = self.mw_conn.root.register(self.hostname)
			if not self.node_id:
				logging.debug("[__init__] Registration failed; Retrying...")
				self.node_id = self.mw_conn.root.register(self.hostname)
		except Exception as e:
			logging.error(f"[__init__] Error: {e}")
			raise Exception("Registration failed")
		self.node_id = int(self.node_id)
		logging.info(f"[__init__] Registered with node_id: {self.node_id}")
		self.registry = {}
		self.connections = {}
		self.dead_nodes = set()

		### Election Variables ###
		self.state = NodeState.ELECTION
		self.leader_id = None
		self.nominee_id = None

		### Worker Variables ###
		self.task = None
		self.result = None

		### Leader Variables ###
		self.current_task = {
			"task_id": "",
			"task": 0,
			"progress": [],
			"committed": []
		}
		self.worker_status = {}
		self.worker_timeouts = {}

	def reset_leader_info(self):
		self.current_task = {
			"task_id": "",
			"task": 0,
			"progress": [],
			"committed": []
		}
		self.worker_status = {}
		self.worker_timeouts = {}

	def reset_worker_info(self):
		self.task = None
		self.result = None

	def update_registry(self):
		logging.debug("[update_registry] Updating the registry...")
		try:
			self.registry = dict(self.mw_conn.root.get_registry())
		except Exception as e:
			logging.error(f"[update_registry] Error: {e}")
		for node_id in self.dead_nodes: 
			if node_id not in self.registry: continue
			self.registry.pop(node_id)
		self.dead_nodes.clear()
		for node_id, node in self.registry.items():
			if node_id in self.connections: continue
			self.connections.update({node_id: rpyc.connect(node, PORT)})

	def detected_dead_node(self, node_id: int):
		logging.debug(f"[detected_dead_node] Detected dead node: {node_id}")
		self.dead_nodes.add(node_id)
		if node_id in self.connections:
			self.connections.pop(node_id).close()

	### Election Methods ###
	def election(self, close_callback):
		logging.info("[election] Starting the election...")
		self.leader_id = None
		self.nomination()
		while not self.leader_id:
			if close_callback(): return
			logging.debug(f"[election] Waiting for the leader to be elected...")
			sleep(0.1)
			if self.nominee_id:
				logging.debug(f"[election] Nominee {self.nominee_id} is elected")
				self.leader_id = self.nominee_id
		logging.info(f"[election] Leader elected: {self.leader_id}")
		self.state = NodeState.LEADER if (self.leader_id == self.node_id) else NodeState.WORKER
		self.nominee_id = None
		if self.leader_id == self.node_id:
			self.state = NodeState.LEADER
			self.reset_worker_info()
			self.get_leader_info()
		else:
			self.state = NodeState.WORKER
			self.reset_leader_info()

	def nomination(self):
		logging.info("[nomination] Sending nomination...")
		for node_id, node in self.registry.items():
			try:
				logging.debug(f"[nomination] Sending nomination to {node_id}:{node}...")
				if not self.connections[node_id].root.send_nomination(self.node_id):
					logging.debug(f"[nomination] Node {node_id}:{node} rejected my nomination")
					return
			except Exception as e:
				logging.error(f"[nomination] Error: {e}")
				self.detected_dead_node(node_id)
		self.confirmation()

	def confirmation(self):
		logging.info("[confirmation] Sending confirmation...")
		for node_id, node in self.registry.items():
			try:
				logging.debug(f"[confirmation] Sending confirmation to {node_id}:{node}...")
				if not self.connections[node_id].root.send_confirmation(self.node_id):
					logging.debug(f"[confirmation] Node {node_id}:{node} rejected my confirmation")
					self.leader_id = None
			except Exception as e:
				logging.error(f"[confirmation] Error: {e}")
				self.detected_dead_node(node_id)

	def exposed_send_nomination(self, node_id: int):
		simulate_network_latency(self.delay)
		logging.info(f"[send_nomination] Received nomination: {node_id}")
		if node_id == self.leader_id:
			logging.debug(f"Node {node_id} is already the leader; Accepting the nomination...")
			return True
		
		id_check = lambda a, b: a >= b
		if not id_check(node_id, self.node_id):
			logging.debug(f"[send_nomination] Node {node_id} is smaller than me; Rejecting the nomination...")
			return False
		
		if self.leader_id and not id_check(node_id, self.leader_id):
			logging.debug(f"[send_nomination] Node {node_id} is smaller than the leader {self.leader_id}; Rejecting the nomination...")
			return False
		
		if self.nominee_id and not id_check(node_id, self.nominee_id):
			logging.debug(f"[send_nomination] Node {node_id} is smaller than the nominee {self.nominee_id}; Rejecting the nomination...")
			return False
		
		logging.debug(f"[send_nomination] Node {node_id} is the new nominee; Accepting the nomination...")
		self.state = NodeState.ELECTION
		self.nominee_id = node_id
		return True

	def exposed_send_confirmation(self, node_id: int):
		simulate_network_latency(self.delay)
		logging.info(f"[send_confirmation] Received confirmation: {node_id}")
		if not self.leader_id:
			logging.debug(f"[send_confirmation] No leader has been elected; Rejecting the confirmation...")
			return False
		
		is_leader = (node_id == self.leader_id)
		logging.debug(f"[send_confirmation] Node {node_id} is the leader; Accepting the confirmation...")
		return is_leader

	### Leader Methods ###
	def leader(self):
		logging.debug("[leader] Handling operations...")
		logging.debug("[leader] Current task: " + str(self.current_task) if self.current_task else "No task")
		if self.current_task["task_id"]:
			logging.debug(f"[leader] Task {self.current_task['task_id']} is in progress...")
			self.check_worker_tasks()
			self.assign_new_task()
			self.update_current_task()
		else:
			logging.debug(f"[leader] No task in progress; Getting new task...")
			self.get_new_task()
		self.send_leader_info()

	def get_new_task(self):
		logging.debug(f"[get_new_task] Getting new tasks...")
		task_info = None
		try:
			task_info = self.mw_conn.root.get_task()
		except Exception as e:
			logging.error(f"[get_new_task] Error: {e}")
		if task_info and task_info != (None, None):
			task_id, task = task_info
			logging.info(f"[get_new_task] Received task {task_id} with {task}")
			self.reset_leader_info()
			self.current_task["task_id"] = task_id if task_id else ""
			self.current_task["task"] = task if task else 0
			self.current_task["progress"].extend([n for n in range(task, 0, -1)])
			self.current_task["committed"].clear()
			self.send_leader_info()
		logging.debug("[get_new_task] Current task: " + str(self.current_task) if self.current_task else "No task")

	def check_worker_tasks(self):
		logging.debug(f"[check_worker_tasks] Checking for completed tasks...")
		workers_finished = []
		for node_id, task in self.worker_status.items():
			logging.debug(f"[check_worker_tasks] Checking task {task} for {node_id}")
			result = None
			try:
				result = self.connections[node_id].root.get_result()
			except Exception as e:
				logging.error(f"[check_worker_tasks] Error: {e}")
				self.detected_dead_node(node_id)
				self.current_task["progress"].extend(task)
				workers_finished.append(node_id)
				continue
			if result:
				logging.info(f"[check_worker_tasks] Task {task} completed by {node_id}: {result}")
				self.current_task["committed"].append(result)
				workers_finished.append(node_id)
			else:
				logging.debug(f"[check_worker_tasks] Task {task} not done yet by {node_id}")
				self.worker_timeouts[node_id] -= 1
				if self.worker_timeouts[node_id] <= 0:
					logging.debug(f"[check_worker_tasks] Worker {node_id} timed out; Reassigning task {task}")
					self.current_task["progress"].extend(task)
					workers_finished.append(node_id)
		self.current_task["progress"].sort(reverse=True)
		self.current_task["committed"].sort(reverse=True)
		for node_id in workers_finished:
			self.worker_status.pop(node_id)
			self.worker_timeouts.pop(node_id)

	def assign_new_task(self):
		logging.debug(f"[assign_new_task] Assigning new tasks...")
		num_workers = len(self.registry) - len(self.worker_status) - len(self.dead_nodes) - 1
		logging.debug(f"[assign_new_task] Available workers: {num_workers}")
		logging.debug(f"[assign_new_task] Current task: {self.current_task}")
		logging.debug(f"[assign_new_task] Worker status: {self.worker_status}")
		while len(self.current_task["progress"]) > 0 and num_workers > 0:
			task = []
			num_ops = min(MAX_OPS, len(self.current_task["progress"]))
			for i in range(num_ops): task.append(self.current_task["progress"].pop(0))
			logging.debug(f"[assign_new_task] Assigning task: {task}")
			assigned = False
			for node_id, node in self.registry.items():
				if node_id == self.node_id or node_id in self.worker_status or node in self.dead_nodes: continue
				num_workers -= 1
				logging.debug(f"[assign_new_task] Assigning task {task} to {node_id}")
				try:
					if (self.connections[node_id].root.send_task(dumps(task))):
						logging.info(f"[assign_new_task] Task {task} assigned to {node_id}")
						self.worker_status.update({node_id: task})
						self.worker_timeouts.update({node_id: WORK_TIMEOUT})
						assigned = True
						break
					logging.debug(f"[assign_new_task] Node {node_id} rejected task {task}")
				except Exception as e:
					logging.error(f"[assign_new_task] Error: {e}")
					self.detected_dead_node(node_id)
			if not assigned:
				logging.debug(f"[assign_new_task] No worker available for task {task}")
				self.current_task["progress"].extend(task)
			self.current_task["progress"].sort(reverse=True)

	def update_current_task(self):
		logging.debug(f"[update_current_task] Updating current task...")
		if len(self.current_task["progress"]) == 0 and len(self.worker_status) == 0:
			if len(self.current_task["committed"]) == 1:
				result = self.current_task["committed"].pop()
				logging.info(f"[update_current_task] Task {self.current_task['task_id']} completed: {result}")
				try:
					self.mw_conn.root.send_result(self.current_task["task_id"], result)
					self.reset_leader_info()
				except Exception as e:
					logging.error(f"[update_current_task] Error: {e}")
			elif len(self.current_task["committed"]) > 1:
				self.current_task["progress"] = [n for n in self.current_task["committed"]]
				self.current_task["committed"].clear()
			else: # length of committed is 0
				self.current_task["progress"] = [n for n in range(self.current_task["task"], 0, -1)]

	def get_leader_info(self):
		logging.debug("[get_leader_info] Getting leader info...")
		leader_info = None
		try:
			leader_info = self.redis_conn.get("leader_info")
		except Exception as e:
			logging.error(f"[get_leader_info] Error: {e}")
		if leader_info:
			leader_save = loads(leader_info)
			logging.debug(f"[get_leader_info] Leader info: {leader_info}")
			self.current_task = leader_save["current_task"]
			self.worker_status = leader_save["worker_status"]
			self.worker_timeouts = leader_save["worker_timeouts"]

	def send_leader_info(self):
		logging.debug("[send_leader_info] Sending leader info...")
		leader_info = {
			"current_task": self.current_task,
			"worker_status": self.worker_status,
			"worker_timeouts": self.worker_timeouts
		}
		logging.debug(f"[send_leader_info] Leader info: {leader_info}")
		try:
			self.redis_conn.set("leader_info", dumps(leader_info))
		except Exception as e:
			logging.error(f"[send_leader_info] Error: {e}")

	### Worker Methods ###
	def worker(self):
		logging.debug("[worker] Working operation...")
		if self.task:
			self.result = 1
			for num in self.task:
				self.result *= num
			self.task = None

	def exposed_send_task(self, data: str):
		simulate_network_latency(self.delay)
		logging.debug(f"[send_task] Received data: {data}")
		if self.state != NodeState.WORKER:
			logging.debug(f"[send_task] Not a worker; Rejecting {data}...")
			return False
		if self.task:
			logging.debug(f"[send_task] Task already exists; Dropping {data}...")
			return False
		task = loads(data)
		logging.info(f"[send_task] Task accepted: {task}")
		self.task = task
		return True

	def exposed_get_result(self):
		simulate_network_latency(self.delay)
		logging.debug(f"[get_result] Sending result: {self.result}")
		tmp = self.result
		self.result = None
		return tmp

### Signal Handler ###
def _on_exit(sig, frame):
	logging.info(f"[_on_exit] Signal captured; Exiting...")
	logging.debug(f"[_on_exit] Setting the close flag...")
	global close
	close = True
	logging.debug(f"[_on_exit] Joining the heartbeat thread...")
	if heartbeat_thread: heartbeat_thread.join()
	logging.debug(f"[_on_exit] Joining the node thread...")
	if node_thread: node_thread.join()
	logging.debug(f"[_on_exit] Closing the RPyC server...")
	if server: server.close()
	logging.debug(f"Exiting...")
	exit(exit_code)

### Utility Methods ###
def simulate_network_latency(delay: float):
	if random() > SLOW_DELAY_CHANCE:
		sleep(delay)
	elif random() > BAD_DELAY_CHANCE:
		logging.info(f"[simulate_network_latency] Simulating slow network latency...")
		sleep(SLOW_DELAY)
	else:
		logging.info(f"[simulate_network_latency] Simulating bad network latency...")
		sleep(BAD_DELAY)

def simulate_crash():
	if random() < CRASH_CHANCE:
		logging.error(f"[simulate_crash] Simulating a crash...")
		raise Exception("Simulated crash")

### Threaded Methods ###
def heartbeat(node_inst: Node, close_callback):
	logging.info("[heartbeat] Heartbeat thread started")
	count = 0
	while not close_callback():
		if count != 0: count %= HEART_DELAY
		elif not node_inst.leader_id: logging.debug("[heartbeat] No leader; No need to ping")
		elif node_inst.leader_id == node_inst.node_id: logging.debug("[heartbeat] I am the leader; No need to ping")
		else:
			try:
				node_inst.connections[node_inst.leader_id].ping()
				logging.debug(f"[heartbeat] Leader {node_inst.leader_id} is up; Sleeping...")
			except Exception as e:
				logging.error(f"[heartbeat] Leader {node_inst.leader_id} is down; Starting election... Error: {e}")
				node_inst.state = NodeState.ELECTION
				node_inst.detected_dead_node(node_inst.leader_id)
		count += 1
		sleep(1)
	logging.info("[heartbeat] Heartbeat thread stopped")

def run(node_inst: Node, close_callback):
	logging.info("[run] Node thread started")
	global exit_code
	try:
		while not close_callback():
			simulate_crash()
			node_inst.update_registry()
			if not node_inst.leader_id or node_inst.nominee_id: node_inst.state = NodeState.ELECTION
			match (node_inst.state):
				case NodeState.ELECTION: node_inst.election(close_callback)
				case NodeState.WORKER: node_inst.worker()
				case NodeState.LEADER: node_inst.leader()
				case _: logging.error(f"[run] Invalid state: {node_inst.state}")
			sleep(RUNTIME_DELAY)
	except Exception as e:
		logging.error(f"[run] Error: {e}")
		exit_code = 1
	finally:
		node_inst.mw_conn.root.unregister(node_inst.node_id)
		if not close_callback(): raise_signal(SIGTERM)
	logging.info("[run] Node thread stopped")

server = None
heartbeat_thread = None
node_thread = None
close = False
exit_code = 0
if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	logging.info("Starting the node...")

	parser = argparse.ArgumentParser(description='Node')
	parser.add_argument("--delay", metavar="network delay", type=float, default=0.03, help="Network delay")
	parser.add_argument("--mw-name", metavar="middleware name", type=str, default="middleware", help="Middleware name")
	parser.add_argument("--mw-port", metavar="middleware port", type=int, default=21212, help="Middleware port")
	parser.add_argument("--r-name", metavar="redis name", type=str, default="redis", help="Redis host")
	parser.add_argument("--r-port", metavar="redis port", type=int, default=6379, help="Redis port")
	args = parser.parse_args()
	logging.debug(f"Node hostname: {environ['HOSTNAME']}")
	logging.debug(f"Middleware name: {args.mw_name}, Middleware port: {args.mw_port}")
	logging.debug(f"Redis host: {args.r_name}, Redis port: {args.r_port}")

	logging.debug("Setting the signal handlers...")
	signal(SIGINT, _on_exit)
	signal(SIGTERM, _on_exit)

	logging.debug("Initializing the RPyC server...")
	try:
		node = Node(vars(args))
	except Exception as e:
		logging.error(f"Error: {e}")
		exit(1)
	server = rpyc.ThreadedServer(node, port=PORT, protocol_config={"allow_public_attrs": True})

	logging.debug("Initializing the heartbeat thread...")
	heartbeat_thread = Thread(target=heartbeat, args=[node, lambda: close])
	heartbeat_thread.start()

	logging.debug("Initializing the node thread...")
	node_thread = Thread(target=run, args=[node, lambda: close])
	node_thread.start()

	server.start()
