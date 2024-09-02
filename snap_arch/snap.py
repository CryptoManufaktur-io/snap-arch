import os
import time
import subprocess
import threading
import logging
import tempfile

from datetime import datetime
from croniter import croniter

LOGGER = logging.getLogger()

def scp_transfer(local_path, destination_path, server, credentials):
    command = f"scp {local_path} {credentials}@{server}:{destination_path}"
    return execute_command(command)

def rsync_transfer(local_path, destination_path, server, credentials):
    command = f"rsync -avz {local_path} {credentials}@{server}:{destination_path}"
    return execute_command(command)

def execute_command(command, wait_for_completion=True):
    """Executes a shell command and optionally waits for its completion."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if wait_for_completion:
            LOGGER.info(result.stdout)  # Optionally log the output
        return True
    except subprocess.CalledProcessError as e:
        LOGGER.info(f"Command failed with error: {e.stderr}")
        return False

def perform_snapshot(chain, config):
    # Navigate to the local path where the compose file is located
    LOGGER.info(f"Creating snapshot on {chain['local_path']}")
    os.chdir(chain['local_path'])
    should_stop_start = False
    snapshot_command = chain['snapshot_command']
    stop_command = chain.get('stop_command', '')

    if len(stop_command) >= 1:
        should_stop_start = True
        LOGGER.info(f"Sending stop command: {stop_command}")

        if not execute_command(stop_command, wait_for_completion=True):
            LOGGER.info("Stop command failed.")
            return

    # Execute snapshot command and wait for it to complete
    LOGGER.info(f"Starting snapshot with command: {snapshot_command}")
    
    if not execute_command(snapshot_command, wait_for_completion=True):
        LOGGER.info("Snapshot command failed.")
        return

    LOGGER.info("Snapshot completed.")

    # Name format for the snapshot
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    snapshot_name = chain['snapshot_name_format'].replace("{timestamp}", timestamp)
    snapshot_path = os.path.join(tempfile.mkdtemp(), snapshot_name)

    # Tar snapshot to temp path if necessary
    if chain['compress_snapshot']:
        LOGGER.info("Compressing file...")

        execute_command(f"tar c {chain['snapshot_output_path']} | lz4 -z - {snapshot_path}")

        LOGGER.info(f"Compressed snapshot located in temp path: {snapshot_path}")
    else:
        # Otherwise just move it to the temp folder.
        execute_command(f"mv {chain['snapshot_output_path']} {snapshot_path}")

    # Transfer snapshot to server
    if config['protocol'] == 'scp':
        scp_transfer(snapshot_path, chain['destination_path'], config['server'], config['credentials'])
    elif config['protocol'] == 'rsync':
        rsync_transfer(snapshot_path, chain['destination_path'], config['server'], config['credentials'])
    elif config['protocol'] == 'mv':
        execute_command(f"mv {snapshot_path} {chain['destination_path']}/{snapshot_name}")

    if should_stop_start:
        # Start the chain again
        start_chain_command = chain['start_chain_command']
        execute_command(start_chain_command)
        LOGGER.info("Chain started again.")

def schedule_job(chain, config):
    cron_expression = chain['schedule_time']
    cron = croniter(cron_expression, datetime.now())
    
    while True:
        next_run = cron.get_next(datetime)
        sleep_time = (next_run - datetime.now()).total_seconds()
        
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        perform_snapshot(chain, config)

def start(config):
    for chain in config['chains']:
        thread = threading.Thread(target=schedule_job, args=(chain, config))
        thread.start()
