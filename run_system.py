import subprocess
import time
import sys
import os

def run_component(command, title):
    print(f"[*] Starting {title}...")
    if sys.platform == "win32":
        subprocess.Popen(f"start \"{title}\" {command}", shell=True)
    else:
        # Linux/Mac (simplified, might need terminal emulator adjustment)
        subprocess.Popen(command.split())

def main():
    print("=== Traffic Generation System Orchestrator ===")
    print("[1] Start Redis (Assumed running or manual start needed)")
    print("[2] Start C2 Server")
    print("[3] Start TG Backend (Mock/Real)")
    print("[4] Start Bot Client")
    print("[5] Run All")
    
    choice = input("Select option (default 5): ").strip() or "5"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mg_dir = os.path.join(base_dir, "MG")
    tg_dir = os.path.join(base_dir, "TG")
    
    # Python executable
    python_exe = sys.executable

    if choice in ["2", "5"]:
        # Start C2
        c2_script = os.path.join(mg_dir, "c2_server_v3.py")
        run_component(f"{python_exe} \"{c2_script}\"", "C2 Server")
        time.sleep(2)

    if choice in ["3", "5"]:
        # Start TG (This would normally be 'npm run dev' in TG folder)
        # For now, we'll just print a message as we might not want to launch full node env automatically
        # unless requested. But let's try to launch it if possible.
        print("[*] To start TG Frontend, please run 'npm run dev' in the TG folder manually.")
        # subprocess.Popen(f"cd \"{tg_dir}\" && npm run dev", shell=True) 

    if choice in ["4", "5"]:
        # Start Bot
        bot_script = os.path.join(mg_dir, "bot_client_v3.py")
        run_component(f"{python_exe} \"{bot_script}\"", "Bot Client")

    print("[*] System startup initiated.")

if __name__ == "__main__":
    main()
