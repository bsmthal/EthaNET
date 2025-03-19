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