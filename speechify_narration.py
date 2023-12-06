import math
import wave
import pyaudio
import time
import nltk
from pydub import AudioSegment
from typing import Literal
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

nltk.download("punkt")


def suppress_exception_in_del(uc):
    old_del = uc.Chrome.__del__

    def new_del(self) -> None:
        try:
            old_del(self)
        except:
            pass

    setattr(uc.Chrome, "__del__", new_del)


def detect_input_audio(data, threshold):
    if not data:
        return False
    rms = math.sqrt(sum([x**2 for x in data]) / len(data))
    if rms > threshold:
        return True
    return False


urls = [
    "https://speechify.com/text-to-speech-online/?ttsvoice=snoop&ttsgender=male&ttslang=English",
    "https://speechify.com/text-to-speech-online/?ttsvoice=mrbeast&ttsgender=male&ttslang=English",
    "https://speechify.com/text-to-speech-online/?ttsvoice=gwyneth&ttsgender=female&ttslang=English",
    "https://speechify.com/text-to-speech-online/?ttsvoice=henry&ttsgender=male&ttslang=English",
    "https://speechify.com/text-to-speech-online/?ttslang=English&ttsgender=female&ttsvoice=Jane",
]


def split_text(text):
    # Split the text into sentences
    sentences = nltk.sent_tokenize(text)
    # Initialize variables
    current_count = 0
    current_text = ""
    result = []
    for sentence in sentences:
        word_count = len(sentence.split())
        # Check if adding the next sentence exceeds the limit
        if current_count + word_count > 200:
            # Add the current text to the result and start a new text
            result.append(current_text.strip())
            current_text = sentence
            current_count = word_count
        else:
            # Add the sentence to the current text
            current_text += " " + sentence
            current_count += word_count
    # Add the last text to the result
    if current_text:
        result.append(current_text.strip())
    return result


def get_speechify_narration(
    narrator: Literal["snoop", "mrbeast", "gwyneth", "male", "female"] = "mrbeast",
    text: str = "Heck yeah baby, I'm a text to speech bot.",
    output_filename: str = "output.wav",
):
    suppress_exception_in_del(uc)

    match narrator:
        case "snoop":
            url = urls[0]
        case "mrbeast":
            url = urls[1]
        case "gwyneth":
            url = urls[2]
        case "male":
            url = urls[3]
        case "female":
            url = urls[4]
        case _:
            url = urls[1]

    options = uc.ChromeOptions()
    options.add_argument("--window-size=1024,768")
    driver = uc.Chrome(options=options)
    driver.get(url)
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=2,
        frames_per_buffer=CHUNK,
    )
    all_frames = []
    textArea = driver.find_element(by=By.ID, value="article")
    textArea.send_keys(Keys.TAB)
    for text_block in split_text(text):
        time.sleep(1)
        textArea.click()
        time.sleep(5)
        textArea.clear()
        time.sleep(1)
        textArea.send_keys(text_block)
        time.sleep(15)
        playButton = driver.find_element(by=By.CLASS_NAME, value="ttso-iframe-play")
        time.sleep(1)
        playButton.click()

        frames = []
        continue_recording = [True] * 300 + [False]
        once_only_trigger = True
        start_recording = False
        while True:
            data = stream.read(CHUNK)
            there_is_input = detect_input_audio(data, 100)
            print(f"{there_is_input}, ")
            frames.append(data)
            continue_recording.append(there_is_input)

            if continue_recording[-1] and once_only_trigger:
                start_recording = True
            if start_recording and once_only_trigger:
                frames = frames[-10:]
                once_only_trigger = False

            if not any(continue_recording[-300:]):
                frames = frames[:-270]
                break
        all_frames = all_frames + frames
        content = driver.find_element(by=By.ID, value="pdf-reader-content")
        driver.execute_script(
            "arguments[0].setAttribute('style',arguments[1])", content, "display: none;"
        )
        time.sleep(1)
        driver.execute_script(
            "arguments[0].setAttribute('style',arguments[1])", textArea, ""
        )
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(output_filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(all_frames))
    wf.close()
    AudioSegment.from_wav(output_filename).export(
        output_filename.replace(".wav", ".mp3"), format="mp3"
    )
    time.sleep(10)
    driver.quit()
