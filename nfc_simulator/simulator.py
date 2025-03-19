#!/usr/bin/env python3
"""
NFC Key Simulator for Hotel Virtual Key System

This script simulates an NFC door lock reading a digital key and
verifying it with the backend API. It can be used to test the
key verification workflow without physical hardware.
"""

import argparse
import json
import uuid
import time
import requests
import os
import sys
from datetime import datetime
import logging
from tabulate import tabulate


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("nfc_simulator")

# Default configuration
DEFAULT_API_URL = "https://8f35-2a01-e0a-159-2b50-59fa-aa12-df1c-1016.ngrok-free.app/api/v1"
DEFAULT_LOCK_ID = "LOCK-A123B456"
DEFAULT_DEVICE_INFO = "NFC Simulator v1.0"
DEFAULT_LOCATION = "Main Entrance"


class NFCSimulator:
    """Simulator for NFC door locks"""
    
    def __init__(self, api_url, lock_id, device_info, location):
        """Initialize the NFC simulator."""
        self.api_url = api_url
        self.lock_id = lock_id
        self.device_info = device_info
        self.location = location
        self.session = requests.Session()
        self.access_history = []
        
    def verify_key(self, key_uuid):
        """Verify a key with the backend API."""
        url = f"{self.api_url}/verify/key"
        
        # Prepare the payload
        payload = {
            "key_uuid": key_uuid,
            "lock_id": self.lock_id,
            "device_info": self.device_info,
            "location": self.location
        }
        
        try:
            # Log the request
            logger.info(f"Verifying key {key_uuid} with lock {self.lock_id}")
            
            # Send request to backend
            response = self.session.post(url, json=payload)
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Store in access history
                history_entry = {
                    "timestamp": timestamp,
                    "key_uuid": key_uuid,
                    "is_valid": result["is_valid"],
                    "message": result["message"],
                    "guest_name": result.get("guest_name", "N/A"),
                    "room_number": result.get("room_number", "N/A")
                }
                self.access_history.append(history_entry)
                
                return result
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {"is_valid": False, "message": error_msg}
                
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {"is_valid": False, "message": f"Connection error: {str(e)}"}
    
    def simulate_key_tap(self, key_uuid):
        """Simulate a key tap on the NFC reader."""
        print("\n======================================")
        print(f"🔑 Key Tap Detected: {key_uuid}")
        print(f"🔒 Lock ID: {self.lock_id}")
        print(f"📍 Location: {self.location}")
        print("======================================")
        
        print("Verifying with backend...", end="", flush=True)
        result = self.verify_key(key_uuid)
        time.sleep(1)  # Simulate verification delay
        
        print("\r", end="")
        if result["is_valid"]:
            print("✅ ACCESS GRANTED")
            print(f"🚪 Room: {result.get('room_number', 'N/A')}")
            print(f"👤 Guest: {result.get('guest_name', 'N/A')}")
        else:
            print("❌ ACCESS DENIED")
            print(f"❗ Reason: {result.get('message', 'Unknown error')}")
        
        print("======================================\n")
        return result
    
    def show_access_history(self):
        """Display the access history."""
        if not self.access_history:
            print("No access history to display.")
            return
        
        # Prepare data for tabulate
        headers = ["Timestamp", "Key UUID", "Status", "Room", "Guest", "Message"]
        table_data = []
        
        for entry in self.access_history:
            status = "✅ GRANTED" if entry["is_valid"] else "❌ DENIED"
            table_data.append([
                entry["timestamp"],
                entry["key_uuid"][:8] + "...",
                status,
                entry["room_number"],
                entry["guest_name"],
                entry["message"]
            ])
        
        # Print table
        print("\n=== Access History ===")
        print(tabulate(table_data, headers=headers, tablefmt="pretty"))
        print()
    
    def run_interactive_mode(self):
        """Run the simulator in interactive mode."""
        print("\n==========================================")
        print("🏨 Hotel Key NFC Simulator - Interactive Mode")
        print("==========================================")
        print(f"API URL: {self.api_url}")
        print(f"Lock ID: {self.lock_id}")
        print(f"Location: {self.location}")
        print("==========================================")
        print("Type 'help' for available commands")
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if cmd.lower() == "exit" or cmd.lower() == "quit":
                    print("Exiting simulator...")
                    break
                
                elif cmd.lower() == "help":
                    print("\nAvailable commands:")
                    print("  scan <key_uuid>  - Simulate scanning a key")
                    print("  random           - Simulate scanning a random key UUID")
                    print("  history          - Show access history")
                    print("  config           - Show current configuration")
                    print("  set lock <id>    - Change the lock ID")
                    print("  set location <l> - Change the location")
                    print("  exit/quit        - Exit the simulator")
                
                elif cmd.lower().startswith("scan "):
                    key_uuid = cmd[5:].strip()
                    self.simulate_key_tap(key_uuid)
                
                elif cmd.lower() == "random":
                    key_uuid = str(uuid.uuid4())
                    self.simulate_key_tap(key_uuid)
                
                elif cmd.lower() == "history":
                    self.show_access_history()
                
                elif cmd.lower() == "config":
                    print("\nCurrent Configuration:")
                    print(f"API URL: {self.api_url}")
                    print(f"Lock ID: {self.lock_id}")
                    print(f"Device Info: {self.device_info}")
                    print(f"Location: {self.location}")
                
                elif cmd.lower().startswith("set lock "):
                    self.lock_id = cmd[9:].strip()
                    print(f"Lock ID changed to: {self.lock_id}")
                
                elif cmd.lower().startswith("set location "):
                    self.location = cmd[13:].strip()
                    print(f"Location changed to: {self.location}")
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nExiting simulator...")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # if close_db:
        #     db.close()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NFC Key Simulator for Hotel Virtual Key System")
    
    parser.add_argument("--api", default=DEFAULT_API_URL, 
                        help=f"API URL (default: {DEFAULT_API_URL})")
    
    parser.add_argument("--lock", default=DEFAULT_LOCK_ID,
                        help=f"Lock ID (default: {DEFAULT_LOCK_ID})")
    
    parser.add_argument("--device", default=DEFAULT_DEVICE_INFO,
                        help=f"Device info (default: {DEFAULT_DEVICE_INFO})")
    
    parser.add_argument("--location", default=DEFAULT_LOCATION,
                        help=f"Device location (default: {DEFAULT_LOCATION})")
    
    parser.add_argument("key_uuid", nargs="?", default=None,
                        help="Optional key UUID to verify. If not provided, interactive mode is started.")
    
    return parser.parse_args()


def main():
    """Main function to run the NFC simulator."""
    args = parse_arguments()
    
    # Create simulator
    simulator = NFCSimulator(
        api_url=args.api,
        lock_id=args.lock,
        device_info=args.device,
        location=args.location
    )
    
    # If key UUID provided, verify it and exit
    if args.key_uuid:
        simulator.simulate_key_tap(args.key_uuid)
    else:
        # Otherwise, run in interactive mode
        simulator.run_interactive_mode()


if __name__ == "__main__":
    main()
