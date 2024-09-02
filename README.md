# Snap-Arch

Snap-Arch is a robust tool designed to automate the process of periodically taking blockchain snapshots in diverse environments and securely storing them on a designated snapshots server. With customizable retention settings, Snap-Arch ensures that your snapshots are efficiently managed and maintained according to your needs.

## Key Features
- Snapshot Management: Executes long-running snapshot commands, carefully monitoring the process to ensure data integrity from start to finish.
- Automatic File Transfer: Seamlessly transfers newly created snapshots to a specified destination using rsync or SCP, ensuring secure and reliable delivery.
- Snapshot Rotation: Automatically manages snapshots by deleting older files and retaining only a user-defined number of the most recent backups, keeping your storage organized and efficient.
- Easy Configuration: Snap-Arch’s behavior, including snapshot commands, scheduling, and file naming conventions, is easily configured using a simple TOML file.


## Running Modes
Snap Mode: This mode is intended to run locally on the server hosting the blockchain nodes. Snap-Arch will take snapshots according to the specified schedule, patiently wait for the snapshot process to complete, and then transfer the snapshot file via SCP or rsync to the designated destination server.

Arch Mode: In this mode, Snap-Arch monitors a specified directory for new file uploads. Once a file upload is confirmed as complete, the tool automatically moves the file to the archive folder. When the number of files in the archive exceeds the keep_latest threshold, Snap-Arch will delete the oldest files, ensuring that only the most recent snapshots are retained.

### Install Dependencies

```shell
poetry install
```

### Running locally

```shell
poetry run python snap_arch/main.py --config /path/to/config.toml
```

### Building Executable

```shell
./build.sh
```

## License

[Apache License v2](LICENSE)
