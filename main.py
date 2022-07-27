from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from bs4 import BeautifulSoup
import unicodedata
import pandas as pd
import os
from tqdm import tqdm
import time
from datetime import datetime
import getpass

# 검색 함수
def insta_searching(word):
    url = 'https://www.instagram.com/explore/tags/' + word
    return url
def select_first(driver):
    first = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='_aabd _aa8k _aanf']")))
    first.click()
    time.sleep(3)

def move_next(driver):
    right = driver.find_element(By.XPATH,"//button[@class='_abl-']//*[@aria-label='Next']" )
    right.click()
    time.sleep(3)


def get_content(driver):
    try:  # 게시글이 표시될때까지 대기. 최대 20초. 게시글이 표시 될 경우 즉시 이하의 코드를 실행
        element = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='_a9zs']")))
    except:
        print('게시글이 로드되지 않았습니다. 다음 게시글로 넘어갑니다.',
              datetime.today().strftime("%Y/%m/%d %H:%M:%S"))  # 20초 동안 게시글이 표시 되지 않으면 다음으로 넘어감
        # 몇몇 게시글이 로드되지 않는 경우가 발생하고 이때 적절한 시간을 두지 않고 넘겨버리면 이후의 게시글도 로드가 되지 않는 문제를 방지하고
        # 인스타그램 서버에서 크롤링 계정을 차단 하는 것을 방지하기 위해 추가되었습니다.
    # ① 현재 페이지 html 정보 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # ② 본문 내용 가져오기
    try:
        content = soup.select('div._a9zs > span')[0].text
        content = unicodedata.normalize('NFC', content)
    except:
        content = ' '
    # ③ 본문 내용에서 해시태그 가져오기(정규식 활용)
    tags = re.findall(r'#[^\s#,\\]+', content)
    # ④ 작성일자 정보 가져오기
    date = soup.select('time')[0]['datetime'][:10]
    # ⑤ 좋아요 수 가져오기
    try:
        like = soup.select('div._aacl._aaco._aacw._aacx._aada._aade > span')[0].text
        like = int(like.replace(',', ''))
    except:
        like = 0
    # ⑥ 위치정보 가져오기
    try:
        place = soup.select('div._aaqm')[0].text
        place = unicodedata.normalize('NFC', place)
    except:
        place = ''
    data = [content, date, like, place, tags]
    return data


def crawl_insta():
    print('시작시간', datetime.today().strftime("%Y/%m/%d %H:%M:%S"))
    print('------인스타그램 로그인------')
    email = input('Username, or email: ')
    pw = getpass.getpass("Password:")

    # 인스타그램 페이지 연결
    driver = webdriver.Chrome(service= Service(ChromeDriverManager().install()))
    driver.get("https://www.instagram.com")
    time.sleep(2)
    # 로그인
    # input_id = driver.find_element(By.CSS_SELECTOR, 'input._2hvTZ.pexuQ.zyHYP'[0])
    input_id = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='username']")))
    input_id.clear()
    input_id.send_keys(email)
    # input_pw = driver.find_element(By.CSS_SELECTOR, 'input._2hvTZ.pexuQ.zyHYP'[1])
    input_pw = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
    input_pw.clear()
    input_pw.send_keys(pw)
    input_pw.submit()

    # "Not Now" 버튼 무시
    not_now1 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))).click()
    not_now2 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Not Now")]'))).click()

    word = input('키워드를 입력해주세요: ')  # 검색어
    url = insta_searching(word)
    target = input('몇개의 게시글을 크롤링할까요? (숫자만 입력 가능합니다): ')

    # ③ 검색페이지 접속하기
    driver.get(url)
    time.sleep(4)  # 대기시간

    # ④ 첫 번째 게시글 열기
    select_first(driver)

    # ⑤ 비어있는 변수(results)만들기
    results = []
    # ⑥→⑦→⑧ 여러 게시물 수집하기

    for i in tqdm(range(int(target)), desc="크롤링 진행상황"):
        # 게시글 수집에 오류 발생시(네트워크 문제 등의 이유로)  2초 대기 후, 다음 게시글로 넘어가도록 try, except 구문 활용
        try:
            data = get_content(driver)  # 게시글 정보 가져오기
            results.append(data)
            move_next(driver)
        except:
            time.sleep(2)
            move_next(driver)
    driver.quit()

    # 엑셀로 저장
    results_df = pd.DataFrame(results)
    results_df.columns = ['content', 'date', 'like', 'place', 'tags']
    results_df.drop_duplicates(subset='content', inplace=True)  # 중복 게시글 제거
    results_df.reset_index(drop=True, inplace=True)  # 인덱스 재설정
    if not os.path.exists('./files'):
        os.makedirs('./files')
    if not os.path.exists('./files/' + word + '.xlsx'):
        with pd.ExcelWriter('./files/' + word + '.xlsx', mode='w', engine='openpyxl') as writer:  # 엑셀 파일 없으면 생성
            results_df.to_excel(writer, sheet_name=word)
    else:
        with pd.ExcelWriter('./files/' + word + '.xlsx', mode='w', engine='openpyxl') as writer:  # 엑셀 파일 있으면 덮어씌우기
            results_df.to_excel(writer, sheet_name=word)
    print('완료', datetime.today().strftime("%Y/%m/%d %H:%M:%S"))

if __name__ == "__main__":
    crawl_insta()
