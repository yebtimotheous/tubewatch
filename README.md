# TubeWatch v0.1.0

# Author: Yeb Timotheous

# Email: yebtimotheous1010@gmail.com

TubeWatch is a Python-based automation tool designed to manage and simulate YouTube video playback. Leveraging Selenium WebDriver, TubeWatch can automatically play, loop, and manage multiple YouTube videos across several browser windows. This tool is particularly useful for scenarios requiring repeated video playback, such as testing, analytics, or automated viewing.

## Features

- **Automated Video Playback**: Play YouTube videos automatically with customizable playback durations and repetition counts.
- **Ad Handling**: Automatically detects and skips YouTube ads using multiple strategies to ensure uninterrupted playback.
- **Playback Speed Control**: Adjusts the playback rate to your desired speed.
- **Video Quality Management**: Sets and maintains the video quality to a specified resolution.
- **Multiple Windows Support**: Runs multiple browser instances simultaneously for extensive operations.
- **Logging**: Comprehensive logging to track actions, errors, and system status.
- **Profile Management**: Generates unique Chrome profiles for each browser instance to manage sessions independently.
- **Cross-Platform**: Compatible with major operating systems including Windows, macOS, and Linux.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yebtimotheous/tubewatch.git
   cd tubewatch
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Configure Settings**

   Open `tube.py` and adjust the constants at the beginning of the script as needed:

   - `PLAYBACK_RATE`: Set your desired video playback speed.
   - `VIDEO_PLAY_DURATION`: Duration (in seconds) for which each video should play.
   - `VIDEO_REPETITIONS`: Number of times each video should be repeated.
   - `NUM_WINDOWS`: Number of browser windows to run concurrently.
   - `CLEANUP_PROFILES`: Set to `True` to remove Chrome profiles after execution.

2. **Run the Script**

   ```bash
   python tube.py
   ```

   - You will be prompted to enter whether you want to provide a channel URL or a direct video URL.
   - Follow the on-screen instructions to input the necessary URLs.

## Configuration

- **Logging**: Logs are stored in `watch.log`. You can adjust the logging level and format in the `setup_logging` function.
- **Profiles Directory**: Chrome profiles are stored in the `profiles` directory by default. You can change this by modifying the `PROFILES_DIR` constant.
- **Timeouts and Retries**: Adjust the `TIMEOUTS` dictionary and `MAX_RETRIES` constant to control the script's resilience and waiting periods.

## Dependencies

- Python 3.6+
- Selenium
- WebDriver Manager
- Other dependencies as listed in `requirements.txt`

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).

## Disclaimer

Use TubeWatch responsibly and ensure compliance with YouTube's [Terms of Service](https://www.youtube.com/t/terms). The author is not responsible for any misuse of this tool.

## Support

For any issues or feature requests, please open an issue on the [GitHub repository](https://github.com/yebtimotheous/tubewatch/issues).
