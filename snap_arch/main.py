import os
import argparse
import logging
import time

import toml

from snap_arch import snap
from snap_arch import arch

logging.basicConfig()

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
formatter.converter = time.gmtime

for handler in LOGGER.handlers:
    handler.setFormatter(formatter)

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = toml.load(file)
    return config

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help='/path/to/config.toml')
    args = parser.parse_args()

    if args.config:
        if os.path.isfile(args.config):
            config = load_config(args.config)

            running_mode = config.get('running_mode')
            if running_mode == 'snap':
                LOGGER.info("Running in snapshot mode.")
                snap.start(config)
            elif running_mode == 'arch':
                LOGGER.info("Running in archive mode.")
                arch.start(config)
            else:
                LOGGER.error("Running mode not specified.")
                exit()
    else:
        LOGGER.error('Missing parameter --config')

if __name__ == "__main__":
    run()
