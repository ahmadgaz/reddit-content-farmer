# Reddit Content Farmer

Reddit Content Farmer allows you to create short form video clips from Reddit posts and comments.

## Features

-   [x] Specify subreddits to scrape content from
-   [x] Define keywords to filter the content
-   [x] Retrieve both posts and comments
-   [x] Customizable font, font size, and font color
-   [x] Customizable background videos
-   [x] AI voiced narration
-   [x] Upload to instagram automatically

## Requirements

-   [Reddit API](https://www.reddit.com/prefs/apps)
-   [Pvleopard API](https://pvleopard.com/)

## Installation

1. Clone the repository: `git clone https://github.com/your-username/reddit_content_farmer.git`
2. Create a virtual environment: `python -m venv new-env`
3. Activate the virtual environment: `source new-env/bin/activate`
4. Install the required dependencies: `pip install -r requirements.txt`
5. Create a folder called `background_music` and add your background music mp3 files to it. A random file will be selected for each video.
6. Create a folder called `background_videos` and add your background video mp4 files to it. A random file will be selected for each video.
7. Add your environment variables to a file called `.env` in the project directory. The following variables are required:
    - `REDDIT_CLIENT_ID`
    - `REDDIT_CLIENT_SECRET`
    - `REDDIT_USER_AGENT`
    - `INSTAGRAM_USERNAME`
    - `INSTAGRAM_PASSWORD`
    - `PVLEOPARD_ACCESS_KEY`

## Usage

1. Configure the `main.py` file.
2. Run the script: `python main.py`
3. The script will save your files in an output folder and upload the video to instagram automatically.

## Contributing

Contributions are welcome! If you have any suggestions or improvements, please submit a pull request.
