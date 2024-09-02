import os
import shutil
import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

LOGGER = logging.getLogger()

class BackupHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

    def on_created(self, event):
        if not event.is_directory:
            self.wait_for_completion(event.src_path)
            self.process_new_file(event.src_path)

    def wait_for_completion(self, file_path, check_interval=1, stable_time=5):
        """Wait until the file is fully uploaded by checking if the file size is stable."""
        previous_size = -1
        stable_counter = 0
        
        while True:
            current_size = os.path.getsize(file_path)
            if current_size == previous_size:
                stable_counter += check_interval
            else:
                stable_counter = 0  # Reset counter if file size changes

            if stable_counter >= stable_time:
                break

            previous_size = current_size
            time.sleep(check_interval)

    def process_new_file(self, src_path):
        LOGGER.info(f"New file detected: {src_path}")
        
        # Clean up and rotate backups
        self.cleanup_and_rotate_backups(src_path)

        # Move the file to the final destination
        destination_path = os.path.join(self.config['archive_directory'], os.path.basename(src_path))
        shutil.move(src_path, destination_path)
        LOGGER.info(f"Moved {src_path} to {destination_path}")

    def cleanup_and_rotate_backups(self, src_path):
        """Clean up old backups of the same name and rotate the remaining files."""
        destination_path = self.config['archive_directory']
        base_name = os.path.basename(src_path)
        name_without_ext, ext = os.path.splitext(base_name)
        
        # Find all existing backups of the same base name
        matching_files = sorted(
            [f for f in os.listdir(destination_path) if f.startswith(name_without_ext) and f.endswith(ext)],
            key=lambda f: os.path.getmtime(os.path.join(destination_path, f)),
            reverse=True
        )

        keep_count = self.config.get('keep_latest', 2)

        # Delete older backups if they exceed the keep count
        if len(matching_files) >= keep_count:
            for file_to_delete in matching_files[keep_count-1:]:
                os.remove(os.path.join(destination_path, file_to_delete))
                LOGGER.info(f"Deleted old backup: {file_to_delete}")

        # Find all existing backups of the same base name, again.
        matching_files = sorted(
            [f for f in os.listdir(destination_path) if f.startswith(name_without_ext) and f.endswith(ext)],
            key=lambda f: os.path.getmtime(os.path.join(destination_path, f)),
            reverse=True
        )

        # Rotate the remaining files
        for i in range(len(matching_files) - 1, 0, -1):
            old_file = os.path.join(destination_path, matching_files[i])
            new_file = os.path.join(destination_path, f"{name_without_ext}.{i+1}{ext}")
            os.rename(old_file, new_file)
            LOGGER.info(f"Rotated {old_file} to {new_file}")

        # The most recent backup will be renamed to .1
        if matching_files:
            latest_file = os.path.join(destination_path, matching_files[0])
            new_name = os.path.join(destination_path, f"{name_without_ext}.1{ext}")
            os.rename(latest_file, new_name)
            LOGGER.info(f"Renamed {latest_file} to {new_name}")

def start(config):
    observer = Observer()
    event_handler = BackupHandler(config)
    observer.schedule(event_handler, path=config['watch_directory'], recursive=False)
    observer.start()
    LOGGER.info(f"Watching directory: {config['watch_directory']}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
