# kondron

Drone control in python with a paid API using https://github.com/raiden-network/microraiden

WIP code. This serves as a very simple example of how you can set a paid API for controlling a drone through telnet. Do not expect nice code.


## Prerequisites

 * Python 3.6
 * [pip](https://pip.pypa.io/en/stable/)

## Setup

```
virtualenv -p python3 env
. env/bin/activate
pip install -r kondron/requirements.txt
```

## Usage

### Server

Only 1 file of code: [./kondron/server/__main__.py](./kondron/server/__main__.py)

```
python -m kondron.server --private-key <PATH_TO_KEY> --rpc-provider http://127.0.0.1:8546
```

### Client

Only 1 file of code: [./kondron/client/__main__.py](./kondron/client/__main__.py)

Start the client and make the API command:

```
python -m kondron.client --private-key <PATH_TO_KEY> --rpc-provider http://127.0.0.1:8546 --command fly1
```
