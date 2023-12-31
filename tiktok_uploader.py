import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def suppress_exception_in_del(uc):
    old_del = uc.Chrome.__del__

    def new_del(self) -> None:
        try:
            old_del(self)
        except:
            pass

    setattr(uc.Chrome, "__del__", new_del)


def upload_tiktok_video(
    token: str,
    session_id: str,
    caption: str,
    path: str = "output",
    file_name: str = "output.mp4",
):
    suppress_exception_in_del(uc)

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    driver.execute_cdp_cmd(
        "Network.setCookie",
        {
            "domain": ".tiktok.com",
            "path": "/",
            "name": "msToken",
            "value": token,
            "secure": True,
        },
    )
    driver.execute_cdp_cmd(
        "Network.setCookie",
        {
            "domain": ".tiktok.com",
            "path": "/",
            "name": "sessionid",
            "value": session_id,
            "httpOnly": True,
            "secure": True,
        },
    )

    driver.get("https://www.tiktok.com/creator-center/upload?from=upload")

    time.sleep(20)
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it(
            (
                By.XPATH,
                "//iframe[@src='https://www.tiktok.com/creator#/upload?scene=creator_center']",
            )
        )
    )
    time.sleep(20)
    driver.find_element(by=By.XPATH, value='//input[@accept="video/*"]').send_keys(
        os.getcwd() + f"/{path}/{file_name}"
    )
    time.sleep(60)
    textInput = driver.find_element(by=By.XPATH, value='//div[@contenteditable="true"]')
    textInput.click()
    time.sleep(5)
    text = file_name.split(".")[0]
    for char in text:
        textInput = driver.find_element(
            by=By.XPATH, value='//div[@contenteditable="true"]'
        )
        textInput.send_keys(Keys.BACKSPACE)
        time.sleep(0.025)
    time.sleep(5)
    text = caption
    for char in text:
        textInput = driver.find_element(
            by=By.XPATH, value='//div[@contenteditable="true"]'
        )
        textInput.send_keys(char)
        time.sleep(0.025)
    time.sleep(10)
    driver.find_element(by=By.XPATH, value='//div[text()="Post"]').click()
    time.sleep(100)

    driver.quit()
