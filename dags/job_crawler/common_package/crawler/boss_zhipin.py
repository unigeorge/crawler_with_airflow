import argparse
import json
import os
import re
import sys
import time
import traceback

from fake_useragent import UserAgent
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from sqlalchemy import Column, String
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from selenium.webdriver.chrome.service import Service

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
import base_util, db_util, config
from db_util import Base

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

'''DDL
create database if not exists job_crawler;
drop table if exists job_info;
create table job_crawler.job_info (
  job_name varchar(40) NOT NULL,
  company_name varchar(40) NOT NULL,
  hr varchar(40) NOT NULL,
  job_area varchar(40) NOT NULL,
  salary varchar(40) NOT NULL,
  experience varchar(40) NOT NULL,
  degree varchar(40) DEFAULT NULL,
  job_industry varchar(40) DEFAULT NULL,
  funding_stage varchar(40) DEFAULT NULL,
  company_scale varchar(40) DEFAULT NULL,
  href mediumtext NOT NULL,
  platform varchar(20) NOT NULL,
  target_job varchar(40) NOT NULL,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (job_name, company_name, hr, job_area)
) default charset=utf8;

drop view if exists job_crawler.job_info_new_arrival;
create view job_crawler.job_info_new_arrival as
select
    *
from
    job_crawler.job_info
where
    to_days(create_time)=to_days(now());
'''


class Job(Base):
    __tablename__ = 'job_info'
    __mapper_args__ = {"eager_defaults": True}

    job_name = Column(String(40), primary_key=True)
    company_name = Column(String(40), primary_key=True)
    hr = Column(String(40), primary_key=True)
    job_area = Column(String(40), primary_key=True)
    salary = Column(String(40))
    experience = Column(String(40))
    degree = Column(String(40))
    job_industry = Column(String(40))
    funding_stage = Column(String(40))
    company_scale = Column(String(40))
    href = Column(String)
    platform = Column(String(20))
    target_job = Column(String(40))


def add_cookies(driver, target_job, regenerate=False):
    if regenerate:
        base_util.generate_cookies(target_job)

    # load cookies into driver
    driver.delete_all_cookies()
    with open('../utils/credentials/cookies_boss_for_%s.json' % target_job, 'r', encoding='utf-8') as f:
        list_cookies = json.loads(f.read())
    for cookie in list_cookies:
        driver.add_cookie({
            'domain': cookie['domain'],
            'name': cookie['name'],
            'value': cookie['value'],
            'path': cookie['path'],
            'expires': None
        })


def check_pop_up_security(driver, cookies=True):
    if cookies:
        try:
            pop_up_account_safe = driver.find_element(By.CSS_SELECTOR, '.dialog-wrap.dialog-account-safe')
        except NoSuchElementException:
            pass
        else:
            pop_up_account_safe.find_element(By.CSS_SELECTOR, '.icon-close').click()
            time.sleep(2)


def check_pop_up_login(driver, cookies=False):
    if not cookies:
        try:
            pop_up_login = driver.find_element(By.CSS_SELECTOR, '.login-dialog-wrapper')
        except NoSuchElementException:
            pass
        else:
            pop_up_login.find_element(By.CSS_SELECTOR, '.icon-close').click()
            time.sleep(2)


def crawl(driver, keyword, target_job='none', cookies=False):
    driver.get('https://www.zhipin.com/shanghai/')

    if cookies:
        add_cookies(driver=driver, target_job=target_job)

    WebDriverWait(driver, 60).until(lambda x: x.find_element(By.CSS_SELECTOR, '.btn.btn-search'))
    driver.find_element(By.CSS_SELECTOR, '.ipt-search').send_keys(keyword)
    driver.find_element(By.CSS_SELECTOR, '.ipt-search').send_keys(Keys.ENTER)

    WebDriverWait(driver, 60).until(
        lambda x: x.find_element(By.CSS_SELECTOR, '.search-condition-wrapper.clearfix>div:nth-child(5)'))

    # pop-up-security check
    check_pop_up_security(driver, cookies)

    action = ActionChains(driver)
    WebDriverWait(driver, 60).until(
        lambda x: x.find_element(By.CSS_SELECTOR, '.search-condition-wrapper.clearfix>div:nth-child(5)'))
    salary_selector = driver.find_element(By.CSS_SELECTOR, '.search-condition-wrapper.clearfix>div:nth-child(5)')
    action.move_to_element(salary_selector).perform()
    driver.implicitly_wait(2)
    driver.find_element(By.CSS_SELECTOR, 'li[ka="sel-salary-406"]').click()
    driver.implicitly_wait(4)

    has_next_page = True
    page = 0
    res_list = []
    while has_next_page:
        # pop-up-login check
        check_pop_up_login(driver, cookies)

        WebDriverWait(driver, 60).until(lambda x: x.find_element(By.CSS_SELECTOR, '.job-list-box>li'))
        page += 1
        job_list = driver.find_elements(By.CSS_SELECTOR, '.job-list-box>li')
        print('fetching page %s for keyword %s' % (page, keyword))
        driver.implicitly_wait(10)
        for job in job_list:
            job_name = job.find_element(By.CSS_SELECTOR, '.job-name').text
            company_name = job.find_element(By.CSS_SELECTOR, '.company-name a').text
            hr = job.find_element(By.CSS_SELECTOR, '.info-public').text
            job_area = job.find_element(By.CSS_SELECTOR, '.job-area').text
            salary = job.find_element(By.CSS_SELECTOR, '.salary').text
            experience = job.find_element(By.CSS_SELECTOR, '.tag-list>li:nth-child(1)').text
            degree = job.find_element(By.CSS_SELECTOR, '.tag-list>li:nth-child(2)').text
            job_industry = job.find_element(By.CSS_SELECTOR, '.company-tag-list>li:nth-child(1)').text
            company_tag = job.find_element(By.CSS_SELECTOR, '.company-tag-list>li:nth-child(2)').text
            if company_tag[0].isdigit():
                funding_stage = 'none'
                company_scale = company_tag
            else:
                funding_stage = company_tag
                company_scale = job.find_element(By.CSS_SELECTOR, '.company-tag-list>li:nth-child(3)').text
            href = job.find_element(By.CSS_SELECTOR, '.job-card-body.clearfix a').get_attribute('href')
            res_list.append(
                Job(job_name=job_name, company_name=company_name, hr=hr, job_area=job_area, salary=salary,
                    experience=experience, degree=degree, job_industry=job_industry, funding_stage=funding_stage,
                    company_scale=company_scale, href=href, platform='boss_zhipin', target_job=target_job))
        next_page_button = driver.find_element(By.CSS_SELECTOR, '.options-pages>a:last-child')
        has_next_page = next_page_button.get_attribute('class') != 'disabled'
        if has_next_page:
            next_page_button.click()
    print('fetched %s pages of data for keyword %s' % (page, keyword))

    db_util.insert_and_update(res_list)


def multiple_crawler(target_job, cookies=False, headless=False, proxied=False, no_image=False):
    options = Options()

    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=%s' % UserAgent().random)

    if headless:
        options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
    if no_image:
        options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    if proxied:
        MAX_TRY = 100
        cnt = 0
        while cnt < MAX_TRY:
            try:
                proxy = base_util.get_proxy()
                print('Using proxy: %s' % proxy)
                options.add_argument(f"--proxy-server=http://{proxy}")
                driver = webdriver.Chrome(options=options, service=service)
                # driver.get('http://wtfismyip.com/text')
                driver.get('https://api.ipify.org')
                WebDriverWait(driver, 60).until(lambda x: x.find_element(By.TAG_NAME, "body"))
                ip_address = driver.find_element(By.TAG_NAME, "body").text
                if not re.match(r'^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$',
                                ip_address):
                    raise WebDriverException
                print("IP address is: %s" % ip_address)
            except WebDriverException:
                cnt += 1
                base_util.delete_proxy(proxy)
                driver.quit()
                continue
            break
        if cnt < MAX_TRY:
            print("Finally get proper proxy after trying %d times!" % cnt)
        else:
            raise Exception("Finally try to get proxy %d times but failed!")
    else:
        driver = webdriver.Chrome(options=options, service=service)

    # driver.get('https://httpbin.org/get?show_env=1')
    # time.sleep(60)

    keywords = config.JOB_KEY_WORDS_MAP[target_job]
    print("For target_job %s, keywords are %s" % (target_job, keywords))
    try:
        for keyword in keywords:
            crawl(driver, keyword, target_job, cookies)
    except Exception as e:
        print(traceback.format_exc())
        with open('./error_web.html', 'wb') as f:
            f.write(driver.page_source.encode('utf8'))
        driver.save_screenshot('./error_web.png')
        raise e
    finally:
        driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='format data')
    parser.add_argument('--headless', action='store_true', help='use headless browser')
    parser.add_argument('--cookies', action='store_true', help='add cookies')
    parser.add_argument('--proxied', action='store_true', help='use proxy')
    parser.add_argument('--target_job', choices=config.JOB_KEY_WORDS_MAP.keys(),
                        default=list(config.JOB_KEY_WORDS_MAP.keys())[0])
    args = parser.parse_args()

    multiple_crawler(args.target_job, args.cookies, args.headless, args.proxied)
