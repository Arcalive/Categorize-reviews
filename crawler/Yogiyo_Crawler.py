import sys
import pandas as pd
from selenium import webdriver

import time

from tqdm import tqdm
from tqdm import trange

###################################################################################################

### Check if selenium exists ###
try :
    from selenium import webdriver
except (ImportError, ModuleNotFoundError) :
    print("Selenium isn't installed.")
    print("Selenium will be installed.")
    import subprocess
    if(float(sys.version[:3]) >= 3.5 ) :
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'selenium'])
    else :
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'selenium'])
finally :
    from selenium import webdriver

###################################################################################################

# Put the chromedriver.exe for your version of Chrome browser in this folder.
driver = webdriver.Chrome("./crawler/chromedriver.exe")

# In window minimized mode, the category is not visible, so maximize the window
driver.maximize_window()

# Website address to access (in my case: Yogiyo)
url = "https://www.yogiyo.co.kr/mobile/#/"
driver.get(url)


# Address to search
location = "서울"

# Time interval: 2 seconds
interval = 2

# Click on a related search term in the address
print(location +'으로 위치 설정 하는중...')
driver.find_element_by_css_selector('#search > div > form > input').click()
driver.find_element_by_css_selector('#button_search_address > button.btn-search-location-cancel.btn-search-location.btn.btn-default > span').click()
driver.find_element_by_css_selector('#search > div > form > input').send_keys(location)
driver.find_element_by_css_selector('#button_search_address > button.btn.btn-default.ico-pick').click()
time.sleep(interval)
driver.find_element_by_css_selector('#search > div > form > ul > li:nth-child(3) > a').click()
time.sleep(interval)
print(location+'으로 위치 설정 완료!')

###################################################################################################

# Define Element Number Dictionary of Yogiyo category page.
food_dict = { '치킨':5, '피자&양식':6,
              '중국집':7, '한식':8, '일식&돈까스':9,
              '족발&보쌈':10, '야식':11,
              '분식':12, '카페&디저트':13 }

###################################################################################################

for category in food_dict:
    print(category+' 카테고리 페이지 로드중...')
    driver.find_element_by_xpath('//*[@id="category"]/ul/li[{}]/span'.format(food_dict.get(category))).click()
    time.sleep(interval)
    print(category+' 카테고리 페이지 로드 완료!')

    prev_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    
        time.sleep(interval)

        curr_height = driver.execute_script("return document.body.scrollHeight")

        if curr_height == prev_height:
            break

        prev_height = curr_height

    print("스크롤 완료")

###################################################################################################

    # Create a list of restaurants
    restaurant_list=[]

    # Setting it as a Yogiyo-registered-restaurant, not our Neighborhood-Plus or Super-Red-Week-recommendation
    restaurants = driver.find_elements_by_css_selector('#content > div > div:nth-child(4) > div > div.restaurant-list > div.col-sm-6.contract')
    
    #  Get the name of the restaurants
    for restaurant in restaurants:
        restaurant_list.append(restaurant.find_element_by_css_selector('div > table > tbody > tr > td:nth-child(2) > div > div.restaurant-name.ng-binding').text)
        
    for restaurant_name in restaurant_list:
        # Click the restaurant search button
        driver.find_element_by_xpath('//*[@id="category"]/ul/li[1]/a').click()

        # Input the restaurant's name to search box
        driver.find_element_by_xpath('//*[@id="category"]/ul/li[15]/form/div/input').send_keys(restaurant_name)

        # Click the button
        driver.find_element_by_xpath('//*[@id="category_search_button"]').click()

        time.sleep(interval)

        # Click the first restaurant among the searched restaurants
        driver.find_element_by_css_selector('#content > div > div:nth-child(5) > div > div > div:nth-child(1) > div').click()
        
        time.sleep(interval)

        # Click the Clean-review
        driver.find_element_by_xpath('//*[@id="content"]/div[2]/div[1]/ul/li[2]/a').click()

        time.sleep(interval)

        # Take the number(str) of reviews and convert it to type of Int
        review_count = int(driver.find_element_by_xpath('//*[@id="content"]/div[2]/div[1]/ul/li[2]/a/span').text)

        click_count = int((review_count/10))

        # Load all review pages
        print('모든 리뷰 불러오는 중...')
        for _ in trange(click_count):
            try:
                driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
                
                driver.find_element_by_class_name('btn-more').click()

                time.sleep(2)
        
            except Exception as e:
                print(e)
                print('페이지 돌아가기중...')
                driver.execute_script("window.history.go(-1)")
                time.sleep(interval)
                print('페이지 돌아가기 완료!\n')
                continue

        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        print('모든 리뷰 불러오기 완료!')

###################################################################################################

        # Start crawling

        reviews = driver.find_elements_by_css_selector('#review > li.list-group-item.star-point.ng-scope')

        print('리뷰 저장하는 중...')
        df = pd.DataFrame(columns=['Category','Location','Restaurant','UserID','Menu','Review','Date','Total','Taste','Quantity','Delivery'])
        
        for review in tqdm(reviews):
            try:
                df.loc[len(df)] = {
                    'Category':category,
                    'Location':location,
                    'Restaurant':driver.find_element_by_class_name('restaurant-name').text,
                    'UserID':review.find_element_by_css_selector('span.review-id.ng-binding').text,
                    'Menu':review.find_element_by_css_selector('div.order-items.default.ng-binding').text,
                    'Review':review.find_element_by_css_selector('p').text,
                    'Date':review.find_element_by_css_selector('div:nth-child(1) > span.review-time.ng-binding').text,
                    'Total':str(len(review.find_elements_by_css_selector('div > span.total > span.full.ng-scope'))),
                    'Taste':review.find_element_by_css_selector('div:nth-child(2) > div > span.category > span:nth-child(3)').text,
                    'Quantity':review.find_element_by_css_selector('div:nth-child(2) > div > span.category > span:nth-child(6)').text,
                    'Delivery':review.find_element_by_css_selector('div:nth-child(2) > div > span.category > span:nth-child(9)').text,
                    }
                
            except Exception as e:
                print('리뷰 페이지 에러')
                print(e)
                print('페이지 돌아가기중...')
                driver.execute_script("window.history.go(-1)")
                time.sleep(interval)
                print('페이지 돌아가기 완료!\n')
                continue
        try:
            df.to_csv('./data/yogiyo/' + df.Restaurant[0] + '.csv')
            print('리뷰 저장하는 완료!')
        except:
            pass
        
        print('페이지 돌아가기중...')
        driver.execute_script("window.history.go(-1)")
        time.sleep(interval)
        print('페이지 돌아가기 완료!\n')
