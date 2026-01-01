# Haruna Rich Presence

This Python script allows you to display the current show, episode, and season (or movie) you're watching on [Haruna](https://github.com/KDE/haruna) to Discord.
| <img width="401" height="161" alt="Screenshot_20260101_210818" src="https://github.com/user-attachments/assets/59177f55-8670-4fdf-95d8-68e7b90f4e98" /> | <img width="398" height="157" alt="Screenshot_20260101_220207" src="https://github.com/user-attachments/assets/377d6b3f-c959-4419-b642-03b082b7280f" /> |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| <img width="403" height="165" alt="Screenshot_20260101_210716" src="https://github.com/user-attachments/assets/f3fc228c-cba8-44f6-9dbc-e906b22baf13" /> | <img width="402" height="160" alt="Screenshot_20260101_220319" src="https://github.com/user-attachments/assets/cb909fcb-77d1-4ba8-99e0-315473b53fe6" /> |



# Requirements

- [Haruna](https://github.com/KDE/haruna) (likely works with mpv for obvious reasons)
- `pypresence`

Run `pip install pypresence` to install the required module.

# Features

- **Filename Parsing**
  - Automatically grabs info from filenames (e.g. "The Simpsons S01E03" displays as Title: The Simpsons, Subtitle: Season 1 | Episode 3)
- **Single Season Support**
  - Handles single season format (e.g. "Cowboy Bebop E01")
- **Generic Support**
  - Displays "Watching" for files where season/episode hasn't been specified
- **Dynamic Status**
  - Tracking for pausing, resuming, and seeking
- **File Extension Filter**
  - (*) Useful if your shows are in .mkv and only want to display that, but not your random 4AM .mp4 clip you saved from Fortnite

<sub> (*) To change this, open the script and follow the instructions on it</sub>

# What's next?

Run the script and watch something, it should display your current show, episode, and season (or movie) with the proper title and subtitle.

You may also run it as a service by moving the `harunarpc.service` file provided to `~/.config/systemd/user`, edit the service file and replace `/path/to/harunarpc.py` with the one where the script is saved and run the following commands:
```
systemctl --user daemon-reload
systemctl --user enable --now harunarpc.service
```
By running `systemctl --user status harunarpc.service` you can check that it's been properly initialized.
This way you can forget about it and always have Rich Presence for Haruna running in the background.

### Last but not least, this was vibecoded, I'm too dumb for stuff like this 🫡
