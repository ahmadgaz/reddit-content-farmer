"""
This script is derived from https://github.com/TobbleCobble/reddit-video-maker
"""

import os
import json
import wave
import math
import errno
import random
import logging
import contextlib
from typing import Literal
from timeout import timeout
from google.cloud import logging as cloud_logging


class RedditContentFarmer:
    """
    Allows you to create content from Reddit posts
    """

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        verbose: bool = False,
        track_used_posts: bool = False,
    ):
        """
        Initialize the RedditContentCultivator object\n
        :param client_id: The client ID of your Reddit app
        :param client_secret: The client secret of your Reddit app
        :param user_agent: The user agent of your Reddit app
        :param verbose: Whether to enable verbose logging
        :param track_used_posts: Whether to track used posts in a file called used_stories.txt
        """
        self.__init_logger_(verbose)

        if not client_id or not client_secret or not user_agent:
            raise ValueError(
                "Please provide a client ID, client secret, and user agent"
            )

        try:
            import praw
        except ModuleNotFoundError:
            raise ValueError(
                "Please install PRAW by running `pip install -r requirements.txt`"
            ) from None

        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__user_agent = user_agent
        self.__track_used_posts = track_used_posts

        # praw type alias
        PrawModels = praw.models

        self.__reddit_client = praw.Reddit(
            client_id=self.__client_id,
            client_secret=self.__client_secret,
            user_agent=self.__user_agent,
        )

        self.__posts = []
        self.__comments = {}
        self.__logger.debug("RedditContentFarmer initialized")
        self.__cloud_logger.log_text("RedditContentFarmer initialized")

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def story_already_used(
        self, submission: "RedditContentFarmer.PrawModels.Submission"
    ):
        self.__logger.debug(
            f"Checking if postid: {submission.id} has already been used..."
        )
        self.__cloud_logger.log_text(
            f"Checking if postid: {submission.id} has already been used..."
        )
        if not os.path.exists("used_stories.txt"):
            raise ValueError(
                "Make sure you have a used_stories.txt file in the working directory of your script to track posts that have been used."
            )
        with open("used_stories.txt", "r") as file:
            if submission.title in file.read():
                return True
        return False

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def add_story_title_to_file(
        self, post: "RedditContentFarmer.PrawModels.Submission"
    ):
        self.__logger.debug(f"Adding postid: {post.id} to used_stories.txt...")
        self.__cloud_logger.log_text(f"Adding postid: {post.id} to used_stories.txt...")
        if not os.path.exists("used_stories.txt"):
            raise ValueError(
                "Make sure you have a used_stories.txt file in the working directory of your script to track posts that have been used."
            )
        with open("used_stories.txt", "a") as file:
            file.write(post.title + "\n")

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def __validate_submission_(
        self, submission: "RedditContentFarmer.PrawModels.Submission", word_limit: int
    ):
        used = self.story_already_used(submission) if self.__track_used_posts else False
        if used:
            self.__logger.debug(
                f"Postid: {submission.id} has already been used, skipping..."
            )
            self.__cloud_logger.log_text(
                f"Postid: {submission.id} has already been used, skipping..."
            )
        valid_title = "r/" not in submission.title and "reddit" not in submission.title
        if not valid_title:
            self.__logger.debug(
                f"Postid: {submission.id} has an invalid title, skipping..."
            )
            self.__cloud_logger.log_text(
                f"Postid: {submission.id} has an invalid title, skipping..."
            )
        below_word_limit = len(submission.selftext.split()) < word_limit
        if not below_word_limit:
            self.__logger.debug(
                f"Postid: {submission.id} is above the word limit, skipping..."
            )
            self.__cloud_logger.log_text(
                f"Postid: {submission.id} is above the word limit, skipping..."
            )
        submission_not_in_posts = submission not in self.__posts
        if not submission_not_in_posts:
            self.__logger.debug(
                f"Postid: {submission.id} has already been added, skipping..."
            )
            self.__cloud_logger.log_text(
                f"Postid: {submission.id} has already been added, skipping..."
            )
        valid_submission = (
            valid_title and below_word_limit and submission_not_in_posts and not used
        )
        return valid_submission

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def get_posts(
        self,
        subreddit: str,
        count: int = 1,
        word_limit: int = 200,
        type: Literal["random", "top", "hot", "new"] = "top",
        span: Literal["hour", "day", "week", "month", "year", "all"] = "all",
    ):
        """
        Get posts from a subreddit\n
        :param subreddit: Name of the subreddit
        :param count: Number of posts to get
        :param word_limit: Maximum number of words in a post
        :param type: Type of posts to get
        :param span: Time span of posts to get
        """
        self.__logger.debug("Getting posts...")
        self.__cloud_logger.log_text("Getting posts...")

        max_count = 500

        if count > max_count:
            raise ValueError(f"Count cannot be greater than {max_count}")

        if count < 1:
            raise ValueError("Count cannot be less than 1")

        if word_limit < 1:
            raise ValueError("Word limit cannot be less than 1")

        if self.__track_used_posts and not os.path.exists("used_stories.txt"):
            raise ValueError(
                "Make sure you have a used_stories.txt file in the working directory of your script to track posts that have been used."
            )

        self.__posts = []
        iterations = 0
        max_iterations = 1000

        if type == "random":
            while count > 0:
                if iterations >= max_iterations:
                    raise ValueError("Could not find enough posts")
                for submission in self.__reddit_client.subreddit(
                    subreddit
                ).random_rising(limit=1):
                    if self.__validate_submission_(submission, word_limit):
                        self.__posts.append(submission)
                        count -= 1
                iterations += 1

        if type == "top":
            while count > 0:
                if iterations >= max_iterations:
                    raise ValueError("Could not find enough posts")
                submissions = []
                for submission in self.__reddit_client.subreddit(subreddit).top(
                    span, limit=max_count
                ):
                    submissions.append(submission)
                submission = random.choice(submissions)
                if self.__validate_submission_(submission, word_limit):
                    self.__posts.append(submission)
                    count -= 1
                iterations += 1

        if type == "hot":
            while count > 0:
                if iterations >= max_iterations:
                    raise ValueError("Could not find enough posts")
                submissions = []
                for submission in self.__reddit_client.subreddit(subreddit).hot(
                    limit=1
                ):
                    submissions.append(submission)
                submission = random.choice(submissions)
                if self.__validate_submission_(submission, word_limit):
                    self.__posts.append(submission)
                    count -= 1
                iterations += 1

        if type == "new":
            while count > 0:
                if iterations >= max_iterations:
                    raise ValueError("Could not find enough posts")
                submissions = []
                for submission in self.__reddit_client.subreddit(subreddit).new(
                    limit=1
                ):
                    submissions.append(submission)
                submission = random.choice(submissions)
                if self.__validate_submission_(submission, word_limit):
                    self.__posts.append(submission)
                    count -= 1
                iterations += 1

        self.__logger.debug("Got posts")
        self.__cloud_logger.log_text("Got posts")
        return self.__posts

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def get_comments(self, word_limit: int = 200, limit: int = 6):
        """
        Get comments from posts\n
        :param word_limit: Maximum number of words in a comment
        :param limit: Maximum number of comments to get
        """
        self.__logger.debug("Getting comments...")
        self.__cloud_logger.log_text("Getting comments...")
        self.__comments = {}
        for post in self.__posts:
            self.__comments[post.id] = []
            for top_level_comment in post.comments:
                if (
                    "http" not in top_level_comment.body
                    and len(top_level_comment.body.split()) < word_limit
                    and len(self.__comments[post.id]) < limit
                ):
                    self.__comments[post.id].append(top_level_comment)
                elif len(self.__comments[post.id]) >= limit:
                    break

        self.__logger.debug("Got comments")
        self.__cloud_logger.log_text("Got comments")
        return self.__comments

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def __create_subtitle_clips_(
        self,
        words: list,
        video_width: int,
        fontsize: int,
        font: str,
        color: str,
        stroke_width: int,
        stroke_color: str,
        title_narration_duration: int = 0,
    ):
        """
        Create subtitle clips from words\n
        :param words: List of words
        :param video_width: Width of the video
        :param fontsize: Font size of the subtitles
        :param font: Font of the subtitles
        :param color: Color of the subtitles
        :param stroke_width: Stroke width of the subtitles
        :param stroke_color: Stroke color of the subtitles
        """

        try:
            from moviepy.editor import (
                TextClip,
                CompositeVideoClip,
            )
            from moviepy.video.fx.resize import resize
        except ModuleNotFoundError:
            raise ValueError(
                "Please install moviepy by running `pip install -r requirements.txt`"
            ) from None

        word_clips = []
        for word in words:
            start_time = word.start_sec + title_narration_duration
            end_time = word.end_sec + title_narration_duration
            duration = end_time - start_time + 0.025
            self.__logger.debug(
                f"Word: {word.word.upper()}, Start time: {start_time}, End time: {end_time}, Duration: {duration}"
            )
            self.__cloud_logger.log_text(
                f"Word: {word.word.upper()}, Start time: {start_time}, End time: {end_time}, Duration: {duration}"
            )
            word_stroke_layer = (
                TextClip(
                    word.word.upper(),
                    fontsize=fontsize,
                    font=font,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    bg_color="transparent",
                    size=(video_width * 3 / 4, None),
                    method="caption",
                )
                .set_start(start_time)
                .set_duration(duration)
            )
            word_color_layer = (
                TextClip(
                    word.word.upper(),
                    fontsize=fontsize,
                    font=font,
                    stroke_color="transparent",
                    stroke_width=stroke_width,
                    color=color,
                    bg_color="transparent",
                    size=(video_width * 3 / 4, None),
                    method="caption",
                )
                .set_start(start_time)
                .set_duration(duration)
            )
            word_clip = CompositeVideoClip([word_stroke_layer, word_color_layer])
            word_position = ("center", "center")
            word_clips.append(word_clip.set_position(word_position))

        return word_clips

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def __create_title_image_clip_(
        self,
        words: list,
        title_image: str,
    ):
        """
        Create title image from title words\n
        :param words: List of words
        :param title_image: Path to the title image
        """

        try:
            from moviepy.editor import (
                ImageClip,
            )
            from moviepy.video.fx.resize import resize
        except ModuleNotFoundError:
            raise ValueError(
                "Please install moviepy by running `pip install -r requirements.txt`"
            ) from None

        start_time = 0
        end_time = words[-1].end_sec
        duration = end_time - start_time + 0.025
        self.__logger.debug(
            f"Title image: {title_image}, Start time: {start_time}, End time: {end_time}, Duration: {duration}"
        )
        self.__cloud_logger.log_text(
            f"Title image: {title_image}, Start time: {start_time}, End time: {end_time}, Duration: {duration}"
        )
        title_image_clip = ImageClip(title_image).set_duration(duration)
        title_image_clip = resize(title_image_clip, newsize=1.3)
        title_image_clips = [title_image_clip.set_position("center")]

        return title_image_clips

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def __ceate_title_image_(
        self, text: str, username: str, subreddit: str, output_path: str
    ):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ModuleNotFoundError:
            raise ValueError(
                "Please install PIL by running `pip install -r requirements.txt`"
            ) from None
        if not os.path.exists("subreddit_icons"):
            raise ValueError(
                "Please make sure you have a subreddit_icons folder with `.png` files in the working directory of your script."
            )

        if not os.path.exists(f"subreddit_icons/reddit.png"):
            raise ValueError(
                f"Please make sure you have the default `reddit.png` file in your subreddit_icons folder."
            )

        lines = []
        length = 0
        nextSpace = 0
        font = ImageFont.truetype("helvetica.ttf", 24)
        userFont = ImageFont.truetype("helvetica.ttf", 20)
        for i in range(len(text)):
            if i != 0:
                if i % 45 == 0:
                    if text[i] == " ":
                        lines.append(text[length:i])
                        length = i
                    else:
                        for j in range(len(text[:i])):
                            if text[j] == " ":
                                nextSpace = j
                        lines.append(text[length:nextSpace])
                        length = nextSpace
        lines.append(text[length : len(text)])
        lines.insert(0, "      ")
        lines.insert(0, "      ")
        lines.insert(0, "      ")
        text = ""
        for line in lines:
            if line[0] == " ":
                line = line[1:]
            text += line + "\n"
        size = (60, 60)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        if not os.path.exists(f"subreddit_icons/{subreddit}.png"):
            subreddit = "reddit"
        im = Image.open(f"subreddit_icons/{subreddit}.png")
        im = im.convert("RGBA")
        pfp = im.resize((60, 60))
        img = Image.new("RGB", (500, len(lines) * 28 + 10), color=(30, 30, 30))
        d = ImageDraw.Draw(img)
        d.text((10, 10), text, fill=(250, 250, 250), align="left", font=font)
        d.text((70, 10), subreddit, fill=(250, 250, 250), align="left", font=font)
        d.text((80, 35), username, fill=(200, 200, 200), align="left", font=userFont)
        img.paste(pfp, (5, 5), mask)
        img.save(output_path + "/title.png")

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def create_video(
        self,
        pvleopard_access_key: str,
        narrator: Literal["snoop", "mrbeast", "gwyneth", "male", "female"] = "mrbeast",
        output_path: str = "output",
        length_per_clip: int = 14,
        hasMusic: bool = False,
        font: str = "Lato-Black",
        fontsize: int = 60,
        color: str = "white",
        stroke_width: int = 10,
        stroke_color: str = "black",
    ):
        """
        Create a video from posts\n
        :param pvleopard_access_key: Access key for the pvleopard API
        :param narrator: Narrator of the video
        :param output_path: Path to the output folder
        :param length_per_clip: Length of each background video clip
        :param hasMusic: Whether to add background music
        :param font: Font of the subtitles
        :param fontsize: Font size of the subtitles
        :param color: Color of the subtitles
        :param stroke_width: Stroke width of the subtitles
        :param stroke_color: Stroke color of the subtitles
        """
        self.__logger.debug("Creating video...")
        self.__cloud_logger.log_text("Creating video...")

        if len(self.__posts) == 0:
            raise ValueError("Please get posts before creating a video")

        try:
            from speechify_narration import get_speechify_narration
        except ModuleNotFoundError:
            raise ValueError(
                "The speechify narration module is not found. Please refer to the README for installation instructions and try reinstalling the files."
            ) from None

        try:
            from moviepy.editor import (
                CompositeAudioClip,
                AudioFileClip,
                VideoFileClip,
                CompositeVideoClip,
                concatenate_videoclips,
                concatenate_audioclips,
            )
            from moviepy.audio.fx.audio_loop import audio_loop
            from moviepy.audio.fx.volumex import volumex
            from moviepy.video.fx.resize import resize
        except ModuleNotFoundError:
            raise ValueError(
                "Please install moviepy by running `pip install -r requirements.txt`"
            ) from None
        if hasMusic and not os.path.exists("background_music/"):
            raise ValueError(
                "Please make sure you have a background_music folder with `.mp3` files in the working directory of your script."
            )
        if not os.path.exists("background_videos/"):
            raise ValueError(
                "Please make sure you have a background_videos folder with `.mp4` files in the working directory of your script."
            )
        try:
            import pvleopard
        except ModuleNotFoundError:
            raise ValueError(
                "Please install pvleopard by running `pip install -r requirements.txt`"
            ) from None

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        self.__ceate_title_image_(
            text=self.__posts[0].title,
            username=self.__posts[0].author.name,
            subreddit=self.__posts[0].subreddit.name,
            output_path=output_path,
        )

        # Creates the mp3 files for the title and story in the output folder
        self.__logger.debug("Getting narration audio files...")
        self.__cloud_logger.log_text("Getting narration audio files...")
        get_speechify_narration(
            narrator=narrator,
            text=self.__posts[0].title,
            output_path=output_path,
            output_filename="title_narration.wav",
        )
        get_speechify_narration(
            narrator=narrator,
            text=self.__posts[0].selftext,
            output_path=output_path,
            output_filename="story_narration.wav",
        )

        # Get the duration of the output from the narration audio files
        self.__logger.debug("Getting narration audio duration...")
        self.__cloud_logger.log_text("Getting narration audio duration...")
        self.__audio_duration = 0
        with contextlib.closing(
            wave.open(output_path + "/title_narration.wav", "rb")
        ) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.__audio_duration += math.floor(frames / float(rate))
        with contextlib.closing(
            wave.open(output_path + "/story_narration.wav", "rb")
        ) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            self.__audio_duration += math.floor(frames / float(rate))

        # Get the background video clips and concatenate them
        self.__logger.debug("Getting background video clips...")
        self.__cloud_logger.log_text("Getting background video clips...")
        num_iterations = self.__audio_duration // length_per_clip
        remainder = self.__audio_duration % length_per_clip
        background_video_clips = []
        for i in range(num_iterations + 1):
            if i == num_iterations:
                clip_duration = remainder + 1
            else:
                clip_duration = length_per_clip

            background_video_path = random.choice(os.listdir("background_videos/"))
            self.__logger.debug(
                f"Clip {i}: {background_video_path}, Duration: {clip_duration}"
            )
            self.__cloud_logger.log_text(
                f"Clip {i}: {background_video_path}, Duration: {clip_duration}"
            )
            full_clip = VideoFileClip("background_videos/" + background_video_path)
            clip_start = (
                random.randint(0, math.floor(full_clip.duration)) - clip_duration
            )
            clip = full_clip.subclip(
                clip_start, clip_start + clip_duration
            ).without_audio()
            background_video_clips.append(clip)
        background_video_without_audio = concatenate_videoclips(
            background_video_clips, method="compose"
        )

        # Get the background music and composite it with the narration audio
        self.__logger.debug("Compositing audio and video files...")
        self.__cloud_logger.log_text("Compositing audio and video files...")
        title_narration = AudioFileClip(output_path + "/title_narration.mp3")
        story_narration = AudioFileClip(output_path + "/story_narration.mp3")
        narration = concatenate_audioclips([title_narration, story_narration])
        if hasMusic:
            background_audio_music_path = random.choice(os.listdir("background_music/"))
            background_audio_music = volumex(
                AudioFileClip("background_music/" + background_audio_music_path), 0.1
            )
            background_audio_music = audio_loop(
                background_audio_music, duration=narration.duration
            )
            audio_clip = CompositeAudioClip([narration, background_audio_music])
        else:
            audio_clip = narration
        background_video = background_video_without_audio.set_audio(
            audio_clip
        ).set_duration(background_video_without_audio.duration)

        # Create the subtitles
        self.__logger.debug("Creating subtitles...")
        self.__cloud_logger.log_text("Creating subtitles...")
        leopard = pvleopard.create(access_key=pvleopard_access_key)
        title_transcript, title_words = leopard.process_file(
            output_path + "/title_narration.wav"
        )
        story_transcript, story_words = leopard.process_file(
            output_path + "/story_narration.wav"
        )
        title_image_clips = self.__create_title_image_clip_(
            words=title_words,
            title_image=f"{output_path}/title.png",
        )
        subtitle_clips = self.__create_subtitle_clips_(
            title_narration_duration=title_narration.duration,
            words=story_words,
            video_width=background_video.size[0],
            fontsize=fontsize,
            font=font,
            color=color,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
        )
        text_clips = title_image_clips + subtitle_clips

        # Composite the background video and the subtitles
        self.__logger.debug("Compositing background video and subtitles...")
        self.__cloud_logger.log_text("Compositing background video and subtitles...")
        video = CompositeVideoClip([background_video] + text_clips)
        video.write_videofile(
            output_path + "/output.mp4",
            temp_audiofile=output_path + "/temp_output.mp3",
            fps=30,
            verbose=False,
            logger=None,
        )

    @timeout(1200, os.strerror(errno.ETIMEDOUT))
    def upload_to_instagram(
        self, username: str, password: str, input_path: str, caption: str
    ):
        """
        Upload a video to Instagram\n
        :param username: Username of the Instagram account
        :param password: Password of the Instagram account
        :param input_path: Path to the video to upload
        :param caption: Caption of the post
        """

        self.__logger.debug("Uploading to Instagram...")
        self.__cloud_logger.log_text("Uploading to Instagram...")
        try:
            from instagrapi import Client
        except ModuleNotFoundError:
            raise ValueError(
                "Please install instagrapi by running `pip install -r requirements.txt`"
            ) from None

        if not os.path.exists(input_path):
            raise ValueError("Input video not found.")

        cl = Client()
        self.__logger.debug("Loading session file...")
        self.__cloud_logger.log_text("Loading session file...")
        if not os.path.exists("instagram_session/session.json"):
            self.__logger.debug("Session file not found, creating empty file...")
            self.__cloud_logger.log_text(
                "Session file not found, creating empty file..."
            )
            os.makedirs("instagram_session")
            with open("instagram_session/session.json", "w") as file:
                json.dump({}, file)
        cl.load_settings("instagram_session/session.json")
        cl.login(username, password)
        cl.get_timeline_feed()
        if self.__audio_duration < 60:
            cl.video_upload(
                path=input_path,
                caption=caption,
            )
        else:
            cl.clip_upload(
                path=input_path,
                caption=caption,
            )
        self.__logger.debug("Uploaded to Instagram")
        self.__cloud_logger.log_text("Uploaded to Instagram")
        self.__logger.debug("Updating used_stories.txt...")
        self.__cloud_logger.log_text("Updating used_stories.txt...")
        self.add_story_title_to_file(self.__posts[0])
        self.__logger.debug("Updated used_stories.txt")
        self.__cloud_logger.log_text("Updated used_stories.txt")

    def __del__(self):
        """
        Kill browser processes
        """
        # Windows
        # os.system("taskkill /f /im geckodriver.exe /T")
        # os.system("taskkill /f /im chromedriver.exe /T")
        # os.system("taskkill /f /im chrome.exe /T")
        # os.system("taskkill /f /im IEDriverServer.exe /T")
        # Debian
        os.system("killall -KILL geckodriver")
        os.system("killall -KILL chromedriver")
        os.system("killall -KILL chrome")
        os.system("killall -KILL IEDriverServer")
        os.system("sudo shutdown -h now")

    def __init_logger_(self, verbose: bool) -> None:
        """
        Initialize the logger\n
        :param verbose: Whether to enable verbose logging
        """
        self.__logger = logging.getLogger("RedditContentFarmer")
        self.__cloud_logger = cloud_logging.Client().logger("RedditContentFarmer")
        self.__logger.setLevel(logging.DEBUG)
        if verbose:
            formatter = logging.Formatter("[%(funcName)s] %(message)s")
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.__logger.addHandler(stream_handler)
