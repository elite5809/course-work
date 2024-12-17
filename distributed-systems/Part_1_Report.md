# Leader Election - Part 1 Implementation

## Implementation

I will explain my system from 'top' (Client) to 'bottom' (Node cluster)

### Client

The Client connects to the Middleware and queues for factorials to be calculated. There is always at least 1 number to be calculated. Once that number is queued, the client will wait on a response for it to print out the result of the number.

The Client keeps track of which result corresponds to each number using the unique IDs the Middleware assigns each task as described below.

### Middleware

The Middleware handles the requests from the client, from the leader of the Nodes, and from all the Nodes in general. 

The client can request for a number to be queued and for the result using a unique ID that was returned when the number was queued.

The leader will request for a task and, when finished, will request for the Middleware to accept the result when completed.

Each Node can request the registry of Node IDs and the affilated Node hostnames (docker container IDs) for use in communicating within the network. The Middleware does not handle the election or directly impact the assignment of tasks for workers.

To handle the registry, the Middleware does conduct a heartbeat to each Node, but it does so every minute to reduce network communications. The registry does not need to remain strictly consistent.

### Node

Each Node runs three threads:

- Heartbeat - Checks if the leader is alive
- Run - Runs the finite state machine for the Node; if this errors, it raises a `SIGTERM` signal to shutdown the Node which is handled by `_on_exit()`
- RPyC Server - Handles all synchronous communications received by the Node

Below are each of the three states that a Node might be in. Each node stores its own copy of the registry, the set of nodes it has detected as dead, and other variables needed for connection to the Middleware (Redis not implemented for this part). When a Node updates its registry, it prunes off any Nodes that it detects as dead.

#### Elections

This system uses the bully algorithm to handle the election. The ID assigned by the Middleware to the Node is used to distinguish each during an election. The highest ID will win the election. Each Node stores its own copy of who it thinks the current leader is and the current nominee as thehighest Node to have sent a nomination.

Each Node during the election state will send out its nomination. When a Node receives the nomination, it will accept <b><i>only</i></b> if the nominee is bigger than the ID of the current Node, the leader ID, <b><i>and</i></b> the nominee ID (if the current Node does not have a leader or nominee, it skips those checks). Otherwise, it rejects the nomination.

Once the biggest Node receives an accepted nomination from each Node, it will confirm with the other Nodes that it is that Node's leader. Once the others have confirmed that, the biggest Node goes into the leader state. The other Nodes will go into the worker state.

#### Leader

The leader is the only Node to make requests to the Middleware and assign tasks to the workers. It does not have any exposed functions since no role should be asking the leader for information.

If the leader does not have a task, it will request one from the Middleware. Once assigned a task, it will first check if workers have any results (when first given a task, no workers have any work, so this is effectively skipped). It assigns new tasks for workers not doing any work. Afterwards, it updates the leader-held task information with the progress made and what values have been calculated and committed so far. This is repeated until the task is done. Once the task is done, we send the result to the Middleware, and reset the state of the current task.

#### Worker

The worker idles while waiting for a new worker task (an array of numbers to multiply). The leader will send the worker a task, and upon the retreival of the task, it will calculate the answer for that given task and store the result. Once the leader requests for the result, the result is sent and reset. If a new task is sent without the result requested, the result from the previous task is lost.

### Implications
- Clients will handle timeouts for tasks and any errors sent from the Middleware such as not queueing a number or having a result available for a task id
- Middleware will not fail. In a practical implementation, there would be a load-balanced set of middleware servers handling the requests from clients and clusters.
- Tasks currently are assumed to have a solution and will eventually return (despite Python's flexible limitation on int to str conversions for representation purposes; going slight more than 1500! will cause Python to throw a system error about using more than 4300 characters to represent the number).
- Nodes do not ever need to change their port and will always be the same across all Nodes.

## Instructions

### Middleware

- `--port` - change the port of the server (Default: 21212)

### Node

- `delay` - adds simulated network delay to Node communication (Default: 0.001)
- `--mw-name` - change the hostname of the middleware (Default: "middleware")
- `--mw-port` - change the port of the middleware (Default: 21212)

### Client

- `n` - factorial numbers to calculate (Must have at least one; no default)
- `--host` - change the hostname of the middleware (Default: "middleware")
- `--port` - change the port of the middleware (Default: 21212)

## Challenges

### Threading/Pointers

The first hiccup I hit was one of pointers. As I was trying to implement the election, I noticed that variable updates where not being reflected. My initial assumptions were that I had race conditions among other common threading issues (considering each RPyC connection is its own thread and so is the runtime on the Node main loop).

After much time, I identified that in the first argument of `rpyc.ThreadedServer`, the service it takes in the class, but I had assumed that the pointers would all be the same since `self` is used. But in the documentation, it implies that each connection uses <b><i>its own instance</i></b> of the service. So, two different connections are using two different object of the same class. It is only when you create the instance of the object first (e.g `rpyc.ThreadedServer(Node(...), ...)`) that RPyC will use the same object for each threaded connection create. This information was found at [this link](https://rpyc.readthedocs.io/en/latest/tutorial/tut3.html#shared-service-instance)

This was overall the most frustrating portion of the homework since the code looked normal from an object-oriented perspective.

### Setting up the leader

This was a challenge since I wanted to set up the leader in such a way that would easily lead into Part 2 of the implementation. I wanted to ensure that data could be centrally located on a Node and easy to transfer while ensuring that each request had consistent data typing and some error checking implemented. Trying to also parse out work for workers while not duplicating work or removing work not done was somewhat non-trival since I wanted an efficient process that does not attempt to send requests to Nodes that are known to be dead. Working with a changing name scheme (happens more to me than I realized) for functions did not benefit me immediately. I had changed things like `get_result` and `send_result` to be semantically in the perspective of the server (get results from client and send results to client respectively) to be in the perspective of the client (get results from the server and send results to the server).

This issue was not as bad as the pointer but a small, consistent problem during implementing the leader functionality.

### RPyC Oddities

There was some slight issues with sending data over RPyC. Because I close the connections almost immediately after finishing some request, I had sent data that required a pointer to the object on the client, but because I closed the connection, it was throwing a kind of error I had not dealt with since I hadn't worked with RPC libraries trying to access objects on another process. I ended up encoding the data in a string for parsing on the other end (e.g. the leader sends an array of numbers for a worker to multiply; worker will parse the string instead of trying to access the pointer for the array on the leader's process) to resolve the issue. It worked well, but that was not an issue I was expecting to face.