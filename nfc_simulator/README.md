# Hotel NFC Key Simulator

This is a simulation tool for testing the Hotel Virtual Key System without physical NFC hardware. It simulates a door lock reading a digital key and verifying it with the backend API.

## Features

- Simulate NFC key taps with real or random UUIDs
- Verify keys with the backend API
- Track access history
- Interactive mode for testing
- Configurable lock ID and location

## Installation

1. Make sure you have Python 3.8+ installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

Start the simulator in interactive mode:

```bash
python simulator.py
```

### Command Line Mode

Verify a specific key and exit:

```bash
python simulator.py <key_uuid>
```

### Options

```
--api URL       API URL (default: https://8f35-2a01-e0a-159-2b50-59fa-aa12-df1c-1016.ngrok-free.app/api/v1)
--lock ID       Lock ID (default: LOCK-A123B456)
--device INFO   Device info (default: NFC Simulator v1.0)
--location LOC  Device location (default: Main Entrance)
```

### Interactive Commands

- `scan <key_uuid>` - Simulate scanning a specific key
- `random` - Simulate scanning a random key UUID
- `history` - Show access history
- `config` - Show current configuration
- `set lock <id>` - Change the lock ID
- `set location <location>` - Change the location
- `exit` or `quit` - Exit the simulator

## Example

```bash
# Start in interactive mode
python simulator.py --lock LOCK-B789C012 --location "Room 302"

# Scan a specific key
> scan 550e8400-e29b-41d4-a716-446655440000

# Generate and scan a random key
> random
```

## Integration Testing

You can use this simulator to test the end-to-end workflow:

1. Create a reservation in the system
2. Generate a digital key for the reservation
3. Use the simulator to verify the key against the correct lock
4. Check that access is granted correctly

This allows for testing the key verification system without physical hardware.
