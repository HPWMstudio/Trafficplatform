import sys
import os
import subprocess
import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [MASTER] - %(message)s')
logger = logging.getLogger(__name__)

class MasterController:
    """
    The Unified Mechanism: Master Controller
    Orchestrates the 'Detect -> Redirect -> Land' pipeline.
    """

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.processes = {}

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        print("=" * 60)
        print("   THE ULTIMATE TRAFFIC PLATFORM - MASTER CONTROLLER")
        print("   [ Detect ] -> [ Redirect ] -> [ Land ]")
        print("=" * 60)

    def launch_component(self, name, script_name, args=[]):
        """
        Launches a system component in a new process.
        """
        script_path = os.path.join(self.base_dir, script_name)
        if not os.path.exists(script_path):
            logger.error(f"Component not found: {script_path}")
            return

        cmd = [sys.executable, script_path] + args
        
        # On Windows, we can use 'start' to open in new window, or just run in background.
        # For a "Dashboard" feel, running in separate windows is often better for monitoring logs.
        if sys.platform == "win32":
            # Use Popen with shell=True and 'start' to open new console window
            full_cmd = f'start "{name}" {sys.executable} "{script_path}" {" ".join(args)}'
            proc = subprocess.Popen(full_cmd, shell=True)
            self.processes[name] = proc
            logger.info(f"Launched {name} in new window.")
        else:
            # Linux/Mac
            proc = subprocess.Popen(cmd)
            self.processes[name] = proc
            logger.info(f"Launched {name} in background (PID: {proc.pid}).")

    def menu(self):
        while True:
            self.clear_screen()
            self.print_banner()
            print("\nActive Components:")
            for name, proc in self.processes.items():
                status = "Running" if proc.poll() is None else "Stopped"
                print(f"  [{status}] {name}")

            print("\nAvailable Operations:")
            print("  [1] Start C2 Server (Command Center)")
            print("  [2] Start Monitor Agent (The Watchtower)")
            print("  [3] Start Bot Client (Standard Mode)")
            print("  [4] Start Social Agent (Interactive Mode)")
            print("  [5] Start SEO Agent (Hunter Mode)")
            print("  [6] Stop All Components")
            print("  [0] Exit")
            
            choice = input("\nSelect Operation > ").strip()

            if choice == '1':
                self.launch_component("C2 Server", "c2_server_v3.py")
            elif choice == '2':
                self.launch_component("Monitor Agent", "monitor_agent.py")
            elif choice == '3':
                self.launch_component("Bot Client", "bot_client_v3.py")
            elif choice == '4':
                # Launch bot client but maybe we need a wrapper or arg to force social mode?
                # For now, the bot client fetches commands. So we just launch it.
                # But we can also launch a specific script if we had one.
                # Let's launch the bot client, as it contains the SocialAgent logic triggered by C2.
                print("[*] Launching Bot. Issue 'SOCIAL' commands via C2 to activate Social Agent.")
                self.launch_component("Social Bot", "bot_client_v3.py")
            elif choice == '5':
                print("[*] Launching Bot. Issue 'SEO' commands via C2 to activate SEO Agent.")
                self.launch_component("SEO Bot", "bot_client_v3.py")
            elif choice == '6':
                self.stop_all()
            elif choice == '0':
                self.stop_all()
                print("Exiting...")
                break
            else:
                print("Invalid selection.")
            
            input("\nPress Enter to continue...")

    def stop_all(self):
        print("[*] Stopping all components...")
        # On Windows 'start' creates independent processes, so Popen object might not control them directly
        # if shell=True was used for 'start'.
        # But we can try. If not, user has to close windows manually.
        if sys.platform == "win32":
             print("[!] On Windows, please close the opened console windows manually.")
        else:
            for name, proc in self.processes.items():
                if proc.poll() is None:
                    proc.terminate()
                    print(f"Stopped {name}")
        self.processes.clear()

if __name__ == "__main__":
    controller = MasterController()
    controller.menu()
