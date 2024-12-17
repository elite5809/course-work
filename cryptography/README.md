# Hash Collider

The purpose of this project was to give students a practical example of how finding hash collisions can cause integrity issues when using weak hashes such as MD5.

The first example is a snippet from an O'Reilly online textbook where we are able iterate through a large amount of numbers, append it at the end of the file, and find multiple collisions as we continue iterating.

In the second example, we have a digital contract that stipulates a trade agreement, but by using hash collision, Bob is able to lower the price on the digital contract while maintaining the hash of the file, giving the illusion of an unmodified file.