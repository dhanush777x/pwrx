<div align="center">

# pwrx

**A modern Linux power manager TUI - built for ThinkPads, Legions and IdeaPads**

![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python)
![Textual](https://img.shields.io/badge/textual-TUI-purple?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Linux-orange?style=flat-square&logo=linux)

</div>

<div align="center">

<a href="https://ibb.co/Vc2DB44C"><img src="https://i.ibb.co/LXn6p77g/pwrx.png" alt="pwrx" border="0"></a>

</div>

---

## Features

- **Battery monitoring** - charge, health, energy, AC status
- **TLP profile switching** - AC, BAT, Performance, Balanced, Power-saver
- **Lenovo conservation mode** - toggle 80% charge cap with a single key
- **CPU stats** - usage, frequency, governor, temperature (AMD k10temp + Intel coretemp)
- **Catppuccin Mocha** theme by default - `ctrl+t` to toggle Latte
- **Vim navigation** - `j/k` to move, `Enter` to apply, `1-5` for direct profile select
- **Non-blocking UI** - all IO runs in background threads, keys are always instant
- **Auto-refresh** every 2 seconds

## Layout

```
┌──────────────┬──────────────┐
│   Battery    │     TLP      │
├──────────────┼──────────────┤
│     CPU      │ Conservation │
└──────────────┴──────────────┘
```

## Keybindings

| Key       | Action                                                                      |
| --------- | --------------------------------------------------------------------------- |
| `j` / `k` | Move TLP cursor up / down                                                   |
| `Enter`   | Apply selected TLP profile                                                  |
| `1` – `5` | Direct select TLP profile (AC / BAT / Performance / Balanced / Power-saver) |
| `c`       | Toggle conservation mode                                                    |
| `ctrl+t`  | Cycle theme (Mocha ↔ Latte)                                                 |
| `r`       | Refresh all data                                                            |
| `q`       | Quit                                                                        |

## Installation

### From source

```bash
git clone https://github.com/dhanush777x/pwrx.git
cd pwrx
pipx install .
```

> [!NOTE]
>
> `pipx install .` automatically installs all Python dependencies
> (`textual`, `psutil`, `rich`) from `pyproject.toml`. No separate
> `pip install -r requirements.txt` needed.

### Optional system packages

These are **not** Python packages - install them separately if needed:

```bash
# TLP - required for profile switching (Arch/EndeavourOS)
sudo pacman -S tlp
sudo systemctl enable --now tlp

# Ubuntu/Debian
sudo apt install tlp
sudo systemctl enable --now tlp
```

## TLP sudo setup (one-time)

TLP profile switching requires passwordless sudo. Run once:

```bash
sudo visudo -f /etc/sudoers.d/pwrx
```

Add (replace `yourusername`):

```
yourusername ALL=(ALL) NOPASSWD: /usr/bin/tlp
yourusername ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/platform/drivers/ideapad_acpi/*
```

## Conservation mode sudo setup (Lenovo only)

Conservation mode writes to sysfs and also needs passwordless sudo:

```bash
# Find your exact path first: your path might vary
ls /sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode

# Then add to sudoers (replace path if different):
sudo visudo -f /etc/sudoers.d/pwrx
# yourusername ALL=(ALL) NOPASSWD: /usr/bin/tee /sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode
```

## Requirements

- Linux (tested on EndeavourOS, Arch-based distros)
- Python 3.10+
- [TLP](https://linrunner.de/tlp/) (for profile switching)
- Lenovo IdeaPad/ThinkPad (optional - for conservation mode)

## Dependencies

```
textual >= 0.47.0
psutil  >= 5.9.0
rich    >= 13.0.0
```

## Project structure

```
power_manager/
├── cli.py              # entrypoint
├── config.py           # paths, constants, theme
├── core/
│   ├── utils.py        # sysfs read/write helpers
│   └── permissions.py  # sudo detection
├── services/
│   ├── battery.py      # battery stats
│   ├── tlp.py          # TLP profile management
│   ├── conservation.py # Lenovo conservation mode
│   ├── cpu.py          # CPU stats
│   └── hardware.py     # vendor/battery detection
└── ui/
    ├── app.py          # Textual app, keybindings, theme
    ├── views.py        # panel widgets
    └── widgets.py      # reusable components
```

## License

Released under the [MIT License](LICENSE) - free to use, modify, and distribute.

## Note

This project was vibe coded for my personal requirements.
If you run into issues or have feature requests, open one on the [Issues](https://github.com/dhanush777x/pwrx/issues) page.
Improvements and fixes are welcome - feel free to raise a [PR](https://github.com/dhanush777x/pwrx/pulls).
