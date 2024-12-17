# Leader Election Implementation

## Overview
The instructor will not give you any starter code for this homework assignment. Instead, you will be given a high-level specification of what the code should accomplish and develop your own approach to implement a solution.  Your solution must run in at least one docker container. Still, you may implement the solution as a set of processes within a container communicating with localhost or with a container assigned for each running process. You may implement your solution in a language other than Python.  However, it is a requirement that the Dockerfile contains the correct set of dependencies and tools to compile and run your application.

## Part 1 - Distributed Factorial Computation
The goal of Part 1 is to implement a distributed system to calculate the factorials of numbers using multiple workers and a coordinator. The list below details the requirements of your implementation.  In this writeup, the term `node` refers to a process running as either a worker or a coordinator.

### Part 1 - Deliverables
1. Part 1 Implementation.
1. A written description of how your system works. Clearly state the leader election algorithm used.
1. Instructions in a `.md` file for how to run your Part 1 implementation.
1. A discussion of any challenges you encountered building this system and how you overcame those challenges.

### Part 1 - Specification

1. You should implement the `Node` as class which can run in either a worker or coordinator mode.
    - The `Node` class accepts a `delay` parameter so that you can simulate processing time in messages
1. When running as the coordinator ($C$) node, the node must not perform any numerical computation.
1. Worker ($W_i$) nodes should operate on at most 4 values. The below example demonstrates how operations could be assigned.
    - Calculate $10!$
    - $C$ divides 10! into smaller computations:
        - $C$ assigns $W_0$ to calculate $R_1=10\times 9 \times 8 \times 7$
        - $C$ assigns $W_1$ to calculate $R_2=6\times 5 \times 4 \times 3$
        - $C$ assigns $W_2$ to calculate $R_3=2\times 1$
        - $C$ assigns $W_0$ to calculate $R_4=R_1 \times R_2 \times R_3$
    - Coordinator logs the final result with the format $10!=R_4$
1. Whenever workers perform a computation the worker should delay sending a message for the configured delay parameter
1. Your implementation should support up to 5 workers plus a coordinator.  You may choose to implement more.
1. When the nodes come online, you should run a leader election algorithm
    - You may use your startup script to ensure all nodes are ready to begin the election
    - Using the actual process ID assigned by the operating system might increase the difficulty.
    - You may assign a static ID to your worker nodes to support the election algorithm that does not change even if the process dies
1. The coordinator is responsible for tracking all computations and reassigning incomplete operations to other nodes.  In this part of the implementation, you do not need to worry about failed operations.
1. You should implement some mechanism for the coordinator node to receive instructions.  Some examples are:
    - Add a software layer to receive web requests for the coordinator.
    - Read from a file that can be updated.

## Part 2 - Add Failure Mechanisms and Re-election
The goal of Part 2 is to make your system robust to failed processes or (simulated) network delays. If the implementation instructions are unclear, you may define your own set of assumptions so long as you document the assumptions in your final report.

### Part 2 - Deliverables
1. Part 2 Implementation (A strategy could be to do Part 2 in a separate branch in git).
1. Instructions in a `.md` file for how to run your Part 2 Implementation.
1. Summary of all design decisions and assumptions you had to make during implementation.
1. Discussion of your experience implementing Part 2 and any challenges you faced.

### Part 2 - Specification
1. Modify your coordinator and workers to fail based on some probability. Failure could mean:
    - A process exits (add a mechanism to restart failed processes) OR
    - Unacceptably (you define) long delays
1. Modify your coordinator to identify failed workers
    - When a worker fails, the coordinator can reassign work to a different worker.
    - You can decide how to allow failed workers back into the pool.  Document your decision.
1. Modify your coordinator to send a checkpoint of the current state so that computations do not start from the beginning if the coordinator fails.
    - You can determine how frequently the state is sent. Document your decision in your report.
1. Modify your workers to identify failed coordinators
    - If a worker determines a coordinator has failed, the worker should initiate the election process
