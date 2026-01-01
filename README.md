# Haruna Rich Presence

This Python script allows you to display the current show, episode, and season (or Movie) you're watching on Haruna to Discord.

# Requirements

- Haruna (probably works with mpv for obvious reasons)
- `pypresence`

Run `pip install pypresence` to install the required module.

# Features

- Filename Parsing: Automatically grabs info from filenames (e.g. "The Simpsons S01E03" displays as Title: The Simpsons, Subtitle: Season 1 | Episode 3) on Discord.
- Single Season Support: Handles simple formats like "Cowboy Bebop E01".
- Generic Support: Displays "Watching" for files if season/episode hasn't been specified.
- Dynamic Status: Tracking for pausing, resuming, and seeking.
- File Extension Filter*: useful if your shows are in .mkv and only want to display that, but not your random 4AM .mp4 clip you saved from Fortnite.

<sub>* To change this, open the script and follow the instructions on it</sub>

# What's next?

Run the script and watch something, it should display your current show, episode, and season (or Movie) with the proper title and subtitle.

You may also run it as a service by moving the `harunarpc.service` file provided to `~/.config/systemd/user`, edit the service file and replace `/path/to/harunarpc.py` with the one where the script is saved and run the following commands:
```
systemctl --user daemon-reload
systemctl --user enable --now harunarpc.service
```
By running `systemctl --user status harunarpc.service` you can check that it's been properly initialized.
This way you can forget about it and always have Rich Presence for Haruna running in the background.

# Last but not least, this was vibecoded, I'm too dumb for stuff like this 🫡
