from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def retry_connection(driver, url, fails):
    # Recursive function to re-connect to URL
    if fails <= 5:
        try:
            driver.get(url)
        except TimeoutException:
            fails += 1
            retry_connection(driver, url, fails)
    else:
        driver.quit()
    return


def retry_keys(driver, email_xpath, email, fails):
    # Recursive function to retry entering email
    if fails <= 5:
        try:
            driver.find_element(By.XPATH, email_xpath).send_keys(email)
        except StaleElementReferenceException:
            fails += 1
            retry_keys(driver, email_xpath, email, fails)
    else:
        driver.quit()
    return


def retry_click(driver, xpath, fails):
    # Recursive function to retry clicking button
    if fails <= 5:
        try:
            driver.find_element(By.XPATH, xpath).click()
        except StaleElementReferenceException:
            fails += 1
            retry_click(driver, xpath, fails)
    else:
        driver.quit()
    return


if __name__ == '__main__':
    # Store the date that the sweepstakes ends
    sweeps_end_date = datetime(year=2021, month=2, day=17)

    # If the sweepstakes is still ongoing, enter the sweepstakes
    if datetime.today() <= sweeps_end_date + timedelta(days=1):
        data_dir = '/home/ec2-user/hgtv_sweeps/data'

        # Read the file that has all entrants' email addresses
        with open(f'{data_dir}/emails.txt') as f:
            emails = f.read().splitlines()

        # The entry form is stored in an iFrame and each of the participating sites uses a different iFrame
        # Store the sites and the respective iFrames
        iframe_dict = dict()
        hgtv_url = 'https://www.hgtv.com/sweepstakes/hgtv-dream-home/sweepstakes'
        iframe_dict[hgtv_url] = 'ngxFrame186475'

        food_network_url = 'https://www.foodnetwork.com/sponsored/sweepstakes/hgtv-dream-home-sweepstakes'
        iframe_dict[food_network_url] = 'ngxFrame186481'

        # Store the sites in a list
        urls = [hgtv_url, food_network_url]

        # Store the xpaths of the necessary elements
        email_xpath = '/html/body/div[1]/div/main/section/div/div/div/div/div/div[1]/div/form/div[1]/fieldset/div/div[2]/div[1]/input'
        advance_xpath = '/html/body/div[1]/div/main/section/div/div/div/div/div/div[1]/div/form/div[2]/button'
        submit_xpath = '/html/body/div[1]/div/main/section/div/div/div/div/div/div[1]/div/div[2]/form[2]/div[2]/div/button/span'

        # Set the webdriver options and launch the webdriver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("enable-automation")
        options.add_argument("start-maximized")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        wait = WebDriverWait(driver, 5)

        # Enter all of the email addresses in all of the participating sites
        for url in urls:
            for email in emails:
                fails = 0
                retry_connection(driver, url, fails)

                # Move into the iFrame
                wait.until(EC.presence_of_element_located((By.ID, iframe_dict[url])))
                driver.switch_to.frame(iframe_dict[url])

                # Enter the email
                wait.until(EC.presence_of_element_located((By.XPATH, email_xpath)))
                fails = 0
                retry_keys(driver, email_xpath, email, fails)

                # Click 'Begin Entry'
                wait.until(EC.element_to_be_clickable((By.XPATH, advance_xpath)))
                fails = 0
                retry_click(driver, advance_xpath, fails)

                # If the email hasn't already entered today, click Submit
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, submit_xpath)))
                    fails = 0
                    retry_click(driver, submit_xpath, fails)

                    # Need to click submit twice
                    wait.until(EC.element_to_be_clickable((By.XPATH, submit_xpath)))
                    fails = 0
                    retry_click(driver, submit_xpath, fails)

                    print(f'successfully submitted for {email}')

                except TimeoutException:
                    pass

        driver.quit()