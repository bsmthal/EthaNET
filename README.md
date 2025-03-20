# EthaNET
Custom wireless protocol implemented in GNU radio, covering the PHY and MAC layers.

| MCS               | LEN      | SEQ    | DES    | SRC    | CRC    | PAYLOAD      |
| :---------------: | :------: | :----: | :----: | :----: | :----: | :----------: |
| 1 byte            | 1 byte   | 1 byte | 1 byte | 1 byte | 1 byte | 0-256 bytes  |

# Usage
There are 2 parts to making this work:
1. Open and run the GNU radio flow
2. Run the python scripts by executing runner.py

```
python3 runner.py -h
```

# Ashton's Contributsions
* Set up boilerplate code for transmitter and receiver in python
* Implement transmitter portion in python
    * takes in information from any file source (including stdin) and chunks it into specified chunk sizes. Packages up chunk sizes and appends a header. PMT serailizes EthaNET packet and sends to GNU Radio flow via ZMQ message socket.
* Implemented Modified ALOHA MAC for the transmitter
    * Transmits a packet and waits for an ACK back from the receiver (access point)
    * If no ACK shows up in a certain amount of itme assume the packet was lost and retransmits
    * Retransmit according to a exponential backoff scheme (longer waits for bigger amounts of retries)

# Brian's Contributions
* 

# Ethan's Contributions
* 

# EthaNET TODO List (Everybody select a task or two)
* Packet synchronization
    * We need a way for the receiver to know when the start of a packet is
* MCS selection at the transmitter (Ashton)
    * Custom python block to extract header and determine which path to send packet through via the selector block
* MCS determination at the receiver
    * after synchronizing, we need to pull off the MCS field first so we can know how to decode the rest of the packet. It may be easier to send the whole header at the lower MCS value and just the data symbols are sent at the potentially different MCS value
* Ensure synchronization and header symbols are sent at the lowest MCS while the data symbols are sent the user selected MCS