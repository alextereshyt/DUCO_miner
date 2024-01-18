#!/usr/bin/env python3
# Minimal version of Duino-Coin PC Miner, useful for developing own apps.
# Created by revox 2020-2022
# Modifications made by Robert Furr (robtech21) and YeahNotSewerSide
# Mining Pools added by mkursadulusoy - 2022-09-06

import hashlib
import os
from socket import socket, AF_INET, SOCK_STREAM
import sys
import time
from urllib.request import Request, urlopen
from json import loads
from threading import Thread

soc_list = []  # List to store sockets

def current_time():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time

def fetch_pools():
    while True:
        try:
            response = loads(urlopen(Request("https://server.duinocoin.com/getPool")).read().decode())
            NODE_ADDRESS = response["ip"]
            NODE_PORT = response["port"]

            return NODE_ADDRESS, NODE_PORT
        except Exception as e:
            print(f'{current_time()} : Error retrieving mining node, retrying in 15s')
            time.sleep(15)

def miner_thread(username, mining_key, node_address, node_port):
    try:
        soc = socket(AF_INET, SOCK_STREAM)
        soc.connect((node_address, node_port))
        print(f'{current_time()} : Connected to {node_address}:{node_port}')

        server_version = soc.recv(100).decode()
        print(f'{current_time()} : Server Version: ' + server_version)

        # Mining section
        while True:
            # Send job request for lower diff
            soc.send(bytes(
                "JOB,"
                + str(username)
                + ",LOW,"
                + str(mining_key),
                encoding="utf8"))

            # Receive work
            job = soc.recv(1024).decode().rstrip("\n")
            # Split received data to job and difficulty
            job = job.split(",")
            difficulty = job[2]

            hashingStartTime = time.time()
            #time.sleep(25)
            base_hash = hashlib.sha1(str(job[0]).encode('ascii'))
            temp_hash = None

            for result in range(100 * int(difficulty) + 1):
                # Calculate hash with difficulty
                temp_hash = base_hash.copy()
                temp_hash.update(str(result).encode('ascii'))
                ducos1 = temp_hash.hexdigest()

                # If hash is even with expected hash result
                if job[1] == ducos1:
                    hashingStopTime = time.time()
                    timeDifference = hashingStopTime - hashingStartTime
                    hashrate = result / timeDifference

                    # Send numeric result to the server
                    soc.send(bytes(
                        str(result)
                        + ","
                        + str(hashrate)
                        + ",Official ESP8266 Miner 3.5",
                        encoding="utf8"))

                    # Get feedback about the result
                    feedback = soc.recv(1024).decode().rstrip("\n")
                    # If result was good
                    if feedback == "GOOD":
                        print(f'{current_time()} : Accepted share',
                              result,
                              "Hashrate",
                              int(hashrate / 1000),
                              "kH/s",
                              "Difficulty",
                              difficulty)
                        break
                    # If result was incorrect
                    elif feedback == "BAD":
                        print(f'{current_time()} : Rejected share',
                              result,
                              "Hashrate",
                              int(hashrate / 1000),
                              "kH/s",
                              "Difficulty",
                              difficulty)
                        break

    except Exception as e:
        print(f'{current_time()} : Error occurred: ' + str(e) + ", restarting in 5s.")
        time.sleep(5)
    finally:
        soc.close()

def main():
    global soc_list
    num_connections = 15  # Set the number of connections you want
    username = 'alextereshyt'  # Replace with your username
    mining_key = 'alextereshyt'  # Replace with your mining key

    for i in range(num_connections):
        try:
            NODE_ADDRESS, NODE_PORT = fetch_pools()
        except Exception as e:
            NODE_ADDRESS = "server.duinocoin.com"
            NODE_PORT = 2813
            print(f'{current_time()} : Using default server port and address')

        t = Thread(target=miner_thread, args=(username, mining_key, NODE_ADDRESS, NODE_PORT))
        t.start()
        soc_list.append(t)

    for t in soc_list:
        t.join()

if __name__ == "__main__":
    main()
