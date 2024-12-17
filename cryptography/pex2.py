"""
Hash Collider
"""

import hashlib

if __name__ == "__main__":
    # Program Title
    print("Hash Collider")

    ### TASK 1 ###
    print("\nStarting Task 1...\n")
    # Read in samplefile.txt
    data = open("samplefile.txt", "rb").read()
    print("Running hash collision for file: samplefile.txt")
    # Get the full MD5 digest for the file
    file_hash = hashlib.md5(data).hexdigest()
    print(f"Full MD5 digest is: {file_hash}")
    # Get the first 5 characters of the MD5 digest for TinyHash
    file_hash = file_hash[:5]
    print(f"TinyHash digest is: {file_hash}")

    # Task 1 hash collision
    count = 0
    for i in range(1000000000):
        # Append the number to the end of the file
        tmp = data + str(i).encode()
        # Get the TinyHash digest for the file
        tmp_hash = hashlib.md5(tmp).hexdigest()[:5]
        # If the TinyHash digest matches the file's TinyHash digest, we have a collision
        if tmp_hash == file_hash:
            # Increment the collision count
            count += 1
            print(f"Found TinyHash collision # {count} after trying {i + 1} numbers.")
            # Save the collision to a file
            with open(f"collision{count}.txt", "wb") as f: f.write(tmp)
            print(f"Collision saved as file: collision{count}.txt")
            # If we have 5 collisions, we can stop
            if count >= 5: break
    
    ### TASK 2 ###
    print("\nStarting Task 2...\n")
    # Read in contract.txt
    data = open("contract.txt", "rb").read()
    print("Running hash collision for file: contract.txt")
    # Get the full MD5 digest for the file
    file_hash = hashlib.md5(data).hexdigest()
    print(f"Full MD5 digest is: {file_hash}")
    # Get the first 5 characters of the MD5 digest for TinyHash
    file_hash = file_hash[:5]
    print(f"TinyHash digest is: {file_hash}")

    # Task 2 hash collision
    # Remove the number amount from the end of the file
    data = data[:-6]
    for i in range(1, 100000):
        # Append the number to the end of the file
        tmp = data + str(i).encode()
        # Get the TinyHash digest for the file
        tmp_hash = hashlib.md5(tmp).hexdigest()[:5]
        # If the TinyHash digest matches the file's TinyHash digest, we have a collision
        if tmp_hash == file_hash:
            print(f"Found TinyHash collision using this number: {i}")
            # Save the collision to a file
            with open(f"newcontract.txt", "wb") as f: f.write(tmp)
            print(f"New contract saved to file: newcontract.txt")
            break