# Gesture-Controlled Virtual Mouse

Control your computer using hand gestures captured through your webcam. This project uses **MediaPipe Hands** to detect hand landmarks, **OpenCV** to process webcam frames, and **PyAutoGUI** to translate recognized gestures into mouse and media-control actions.

The right hand controls the mouse, while the left hand provides media controls.

## Features

### Right-hand controls

| Gesture | Action |
|---|---|
| Closed fist | Move the mouse cursor |
| Index finger extended | Single click (hold the gesture briefly) |
| Index and middle fingers extended | Double-click (hold the gesture briefly) |
| Thumb and index finger brought close together, with the other fingers open | Drag |
| Open palm | No mouse action assigned |

### Left-hand controls

| Gesture | Action |
|---|---|
| Index finger extended, other fingers closed | Adjust system volume by moving the index fingertip |
| All fingertips brought close to the thumb | Mute/unmute |
| Open palm | Change to the next track |
| Thumb, index and middle fingers open; ring and pinky closed | Play/pause |
| Thumb and index finger brought close together, with the other fingers open | Scroll |

The code also recognizes two short gesture sequences with the right hand to open locally stored audio files. See **Customizing audio shortcuts** below.

## How it works

1. OpenCV captures frames from the default webcam.
2. Each frame is flipped to provide a mirror-like view and converted from BGR to RGB.
3. MediaPipe detects the hand and returns 21 hand landmarks.
4. The program estimates finger states using landmark geometry and checks distances between fingertips.
5. Recognized gestures are mapped to mouse or media actions through PyAutoGUI.

## Tech stack

- Python
- OpenCV
- MediaPipe
- NumPy
- PyAutoGUI

## Requirements

- A computer with a working webcam
- Python installed
- A supported desktop environment
- The dependencies listed in [`requirements.txt`](requirements.txt)

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the project

Start the script:

```bash
python hand_landmarks.py
```

Allow webcam access if your operating system asks for permission. Keep your hand visible in front of the camera.

Press **`q`** in the OpenCV preview window to stop the program.

## Customizing audio shortcuts

The script contains two right-hand gesture sequences that open audio files using Windows' `os.startfile()`:

- `middle → middle → ring → pinky → middle`
- `ring → ring → middle → middle → pinky`

Update the file paths in `hand_landmarks.py` to point to audio files on your computer. These paths are machine-specific, and `os.startfile()` is Windows-specific.

## Configuration

You can tune these values near the beginning of `hand_landmarks.py`:

| Variable | Purpose |
|---|---|
| `sensitivity` | Controls cursor movement sensitivity |
| `dead_zone` | Filters out very small hand movements |
| `scroll_sensitivity` | Controls scroll response |
| `hold_threshold` | Number of consecutive frames required before a click |
| `sequence_frames_threshold` | Time window used to collect a gesture sequence |

MediaPipe is configured to detect one hand at a time with minimum detection and tracking confidence values of `0.5`.

## Important notes

- The project uses the default webcam (`cv2.VideoCapture(0)`). Change the camera index if your system uses a different device.
- The script uses PyAutoGUI to control your actual mouse and media keys. Test it in a safe environment before relying on it.
- The current code sets `pyautogui.FAILSAFE = False`, disabling PyAutoGUI's usual corner-based emergency stop. Consider enabling the failsafe while testing.
- The audio shortcuts use local file paths and must be configured for your machine.
- Gesture recognition can be affected by lighting, camera quality, hand position, and how clearly the fingers are visible.
- The current implementation is configured for one detected hand at a time.

## Project structure

```text
.
├── hand_landmarks.py
├── requirements.txt
└── README.md
```

## Future improvements

- Add gesture calibration and user-configurable gesture mappings.
- Improve gesture stability with smoothing and more robust state handling.
- Add an on-screen guide showing available gestures.
- Make audio shortcuts configurable instead of using hard-coded paths.
- Add support for simultaneous two-hand tracking.

## Contributing

Contributions, bug reports, and suggestions are welcome. Fork the repository, make your changes, and open a pull request.

## License

No license is currently specified. Add a license file before allowing others to reuse, modify, or distribute this project.
