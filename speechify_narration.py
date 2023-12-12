import io
import json
import time
import nltk
import math
import base64
from typing import Literal
from pydub import AudioSegment
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Work in progress

nltk.download("punkt")


class Word:
    def __init__(self, word, start_sec, end_sec):
        self.word = word
        self.start_sec = start_sec
        self.end_sec = end_sec


class element_has_changed:
    def __init__(self, element):
        self.element = element
        self.initial_html = element.get_attribute("outerHTML")

    def __call__(self, driver):
        current_html = self.element.get_attribute("outerHTML")
        return current_html != self.initial_html


def remove_non_bmp_characters(text):
    """Remove non-BMP (Basic Multilingual Plane) characters from a string."""
    return "".join(char for char in text if ord(char) <= 0xFFFF)


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


def log_filter(log_):
    return (
        log_["method"] == "Network.responseReceived"
        and "json" in log_["params"]["response"]["mimeType"]
    )


def suppress_exception_in_del(uc):
    old_del = uc.Chrome.__del__

    def new_del(self) -> None:
        try:
            old_del(self)
        except:
            pass

    setattr(uc.Chrome, "__del__", new_del)


def get_speechify_narration(
    narrator: Literal["snoop", "mrbeast", "gwyneth", "male", "female"] = "mrbeast",
    text: str = "Heck yeah baby, I'm a text to speech bot.",
    output_path: str = "output/",
    output_filename: str = "output.wav",
):
    suppress_exception_in_del(uc)
    words = []
    start_time = 0

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = uc.Chrome(options=options)
    driver.get("https://speechify.com/text-to-speech-online/")
    # Set a value in local storage
    if narrator == "snoop" or narrator == "narrator":
        speechify_narrator = f"resemble.{narrator}"
    elif narrator == "female":
        speechify_narrator = "azure.Jane"
    elif narrator == "male":
        speechify_narrator = "speechify.henry"
    else:
        speechify_narrator = f"speechify.{narrator}"

    # Set the narrator in local storage
    driver.execute_script(
        f"window.localStorage.setItem('activeVoiceID', '{speechify_narrator}');"
    )
    driver.refresh()
    value = driver.execute_script(
        "return window.localStorage.getItem('activeVoiceID');"
    )
    print("Value in local storage for 'activeVoiceID':", value)

    text = remove_non_bmp_characters(text)
    textArea = driver.find_element(by=By.ID, value="article")
    textArea.send_keys(Keys.TAB)
    combined_audio = AudioSegment.empty()
    for text_block in split_text(text):
        time.sleep(1)
        textArea.click()
        time.sleep(5)
        textArea.clear()
        time.sleep(1)
        textArea.send_keys(text_block)
        time.sleep(15)
        playButton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ttso-iframe-play"))
        )
        playButton.click()
        time.sleep(1)
        WebDriverWait(driver, 1000).until(element_has_changed(playButton))
        logs_raw = driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        for index, log in enumerate(filter(log_filter, logs)):
            resp_url = log["params"]["response"]["url"]
            resp_type = log["params"]["response"]["headers"]["content-type"]
            if (
                "https://audio.api.speechify.dev/generateAudioFiles" not in resp_url
                or resp_type != "application/json; charset=utf-8"
            ):
                continue
            request_id = log["params"]["requestId"]
            print(f"Caught {resp_url} at index {index}")
            response = driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )
            body = json.loads(response["body"])
            audio_data = base64.b64decode(body["audioStream"])
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
            combined_audio += audio_segment
            # Get words and their timings
            words += [
                Word(
                    word_chunk["value"],
                    math.floor((int(word_chunk["startTime"]) / 1000 + start_time) * 100)
                    / 100,
                    math.floor((int(word_chunk["endTime"]) / 1000 + start_time) * 100)
                    / 100,
                )
                for sentence_chunk in body["speechMarks"]["chunks"]
                for word_chunk in sentence_chunk["chunks"]
            ]
            start_time += math.floor((len(audio_segment) / 1000) * 100) / 100
        content = driver.find_element(by=By.ID, value="pdf-reader-content")
        driver.execute_script(
            "arguments[0].setAttribute('style',arguments[1])", content, "display: none;"
        )
        time.sleep(1)
        driver.execute_script(
            "arguments[0].setAttribute('style',arguments[1])", textArea, ""
        )
    combined_audio.export(f"{output_path}/{output_filename}", format="wav")
    AudioSegment.from_wav(f"{output_path}/{output_filename}").export(
        f"{output_path}/{output_filename.replace('.wav', '.mp3')}", format="mp3"
    )
    time.sleep(10)
    driver.quit()
    driver.stop_client()
    return words
