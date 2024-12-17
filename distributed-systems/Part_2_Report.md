# Leader Election - Part 2 Fault Tolerance

## Instructions

### Execution Script

`[python binary] execution_script.py [command] [--attached]`

- `command` - takes `start` or `stop` to start or stop docker containers
- `--attached` - tells docker compose to attach (no effect using `stop` command)

NOTE: Script will remove 'redis' folder recursively from current directory. This ensures each restart of the system is not using old data stored by redis.

### Middleware

- `--port` - change the port of the server (Default: 21212)

### Node

- `delay` - adds simulated network delay to Node communication (Default: 0.001)
- `--mw-name` - change the hostname of the middleware (Default: "middleware")
- `--mw-port` - change the port of the middleware (Default: 21212)
- `--r-name` - change the hostname of the middleware (Default: "redis")
- `--r-port` - change the port of the middleware (Default: 6379)

### Client

- `n` - factorial numbers to calculate (Must have at least one; no default)
- `--host` - change the hostname of the middleware (Default: "middleware")
- `--port` - change the port of the middleware (Default: 21212)

## Design Decisions

### Leader Re-election

Even thought this was implemented in Part 1, this functionality is about making the system fault tolerate. When the leader crashes or closes, the Nodes will detect the leader is down after it fails the hearbeat check and will clear the variable storing the leader node ID. Each node will go into the election state and follow the election as described in Part 1. The Nodes do no communicate with each other or the Middleware to detect whether the leader is down.

### Leader Information Storage

To track the task, task progress, and the statuses of the workers, I created dictionaries to store the information for the leader. Below are what it contained.

- Current task
	- Task ID: used to track whether we have a task or not; also used during debugging
	- Task: factorial number to calculate; can be used to restart task if no progress, no commits, and no statuses are saved
	- Progress: tracks numbers yet to be included in the calculation
	- Committed: results from all calculations; once length is one, return result to the Middleware
- Worker status: tracks which node ID is working on which worker task (array of numbers to calculate vs. leader task which is the factorial number)
- Worker timeout: tracks how many cycles left until we declare a node ID too slow to handle the worker task.

### Leader Information Backup

To send the leader information to the Redis server as the leader checkpoint, I stored each dictionary in a single dictionary called 'leader_info' and used json to send Redis a string representation of the data. To retrieve it as the new leader, I request from Redis the 'leader_info' and parse the string using json into 'leader_save' and further breakdown the dictionary into each of the 3 leader dictionaries as described above.

### Failing & Long Delays

To implement the simulation of slow and bad network delays, I created the function `simulate_network_latency()` which takes in a float for the delay in seconds wanted. The 'slow' and 'bad' delays and chances are defined using const variables, but the regular delay is defined by the parameter inserted into the Node script. I used the built-in `random()` function from the standard Python library to give the random chance.

To implement a simulated crash, I created a `simulate_crash()` function which takes in no arguments and raises a generic exeception with the message 'Simulated crash'. The chance of a crash is stored in a const variable. The same as the network delay, I used the `random()` function to give the random chance.

## Assumptions

- Client: will handle results instantly from the Middleware instead of expecting a block until a result is given.
- Middleware: will not fail/crash; in a practical implementation, this might be load balanced at a higher-level server.
- Redis: will not fail/crash; in a practical implementation, there will be mirrors that keeps the data redundant, and the Nodes will know how to handle a failed primary or mirror Redis server.

## Challenges

### Error Checking

Because I wanted my system to be resilient, there were many points where network connections could raise exceptions and needed to be handled. The challenge was ensuring that the system could continue without the requested information from the recipient. I had to think about what state the system should be in within the `try` code block, the `except` code block, and after the try-catch statement was completed. The `finally` block was not needed for this project.

### Saving the Leader Checkpoints

Initially, I did not realize that Redis stored string representations of objects, so there was some time wasted in not knowing that and trying to implement my own parsing of the data. Once I did a quick search of encoding string representations of dicts and arrays, I was reminded that json does exactly what I needed. Afterwards, it was trivial for the data to be sent to Redis.

### Handling Rejected or Failed Tasks and Dead Nodes

When I first created the current task dictionary, I was not handling rejected tasks, dead nodes, or failed operations, so there were tasks that disappeared from the progress list and, later on when rejected or failed tasks were appended back on the progress list, there were many duplicates in the progress array. I had to ensure that when appending tasks back on the progress array that it did not repeat multiple times as the leader tried giving the same task to multiple worker Nodes. Also, I had to ensure that if a worker continually could not give a result, another worker should handle that task.