import os
import shutil
import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

LOGGER = logging.getLogger()

class BackupHandler(FileSystemEventHandler):
    def __init__(self, config, watch_directory, archive_directory, keep_latest):
        self.config = config
        self.watch_directory = watch_directory
        self.archive_directory = archive_directory
        self.keep_latest = keep_latest

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
        
        # Move the file to the final destination
        destination_path = os.path.join(self.archive_directory, os.path.basename(src_path))
        shutil.move(src_path, destination_path)
        LOGGER.info(f"Moved {src_path} to {destination_path}")
        
        # Clean up old backups
        self.cleanup_old_backups()

    def cleanup_old_backups(self):
        """Delete old backups if they exceed the keep count."""
        files = sorted(
            [os.path.join(self.archive_directory, f) for f in os.listdir(self.archive_directory) if os.path.isfile(os.path.join(self.archive_directory, f))],
            key=lambda f: os.path.getmtime(f),
            reverse=True
        )

        if len(files) > self.keep_latest:
            for file_to_delete in files[self.keep_latest:]:
                os.remove(file_to_delete)
                LOGGER.info(f"Deleted old backup: {file_to_delete}")

def start(config):
    observer = Observer()
    handlers = []

    for watch_config in config['directories']:
        event_handler = BackupHandler(
            config=config,
            watch_directory=watch_config['watch_directory'],
            archive_directory=watch_config['archive_directory'],
            keep_latest=watch_config.get('keep_latest', 2)
        )
        observer.schedule(event_handler, path=watch_config['watch_directory'], recursive=False)
        handlers.append(event_handler)
        LOGGER.info(f"Watching directory: {watch_config['watch_directory']} with destination: {watch_config['archive_directory']}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
