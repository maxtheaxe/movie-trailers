# trailer_scraper by max, built for redflag
import typing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import chromedriver_autoinstaller as cda  # handle chromedriver for new installs
from bs4 import BeautifulSoup
import time


def start_driver(headless: bool = True) -> webdriver.Chrome:
	'''
	Starts the webdriver (dls if needed) and returns it.
	
	Args:
		headless (bool): Whether chrome should be visualized or not
	Returns:
		webdriver.Chrome
	'''
	# if chromedriver doesn't exist, dl it, then set path to it
	cda.install()
	# setup webdriver settings
	options = webdriver.ChromeOptions()
	# can add ublock origin to reduce impact, block stuff
	# options.add_extension("ublock_origin.crx")
	# other settings
	options.headless = headless  # headless or not, passed as arg (true by default)
	options.add_experimental_option('excludeSwitches', ['enable-logging'])  # clean up console
	return webdriver.Chrome(options=options)  # return set up driver


def youtube_search(driver: webdriver.Chrome, movie_title: str, num_results: int = 100) -> list:
	'''
	Scrapes videos associated with a given movie from youtube.

	Args:
		driver (webdriver.Chrome): Chrome Driver to be used
		movie_title (str): Title of Movie

	Returns:
		list
	'''
	driver.get("https://www.youtube.com/")  # load page
	driver.find_element_by_id("search").send_keys(movie_title)  # type search string
	driver.find_element_by_id("search-icon-legacy").click()  # click search button
	# load appropriate number of results (keep scrolling while num results < desired)
	while len(driver.find_elements_by_xpath(
			"//ytd-video-renderer//a[@id='video-title']")) < num_results:
		driver.execute_script("window.scrollBy(0,300)", "")  # scroll down w JS
	# save all results once desired number loaded (at least partially)
	results = driver.find_elements_by_xpath("//ytd-video-renderer//a[@id='video-title']")
	# wait for the last element to load fully
	try:  # look for filters menu as indicator of load (we know it will always be there)
		wait = WebDriverWait(driver, 10)  # wait a maximum of 10 seconds for load
		# feature used below doesn't exist yet, but I've implemented it my local version
		# and submitted a pull request to the main repo on github:
		# https://github.com/SeleniumHQ/selenium/pull/9374
		element = wait.until(EC.element_to_be_clickable(results[-1]))  # target last video
	except NoSuchElementException as Error:  # page didn't load in a reasonable amount of time
		print("\n\tError: Page didn't load in a reasonable amount of time; try again.\n")
		print("\n\t{}\n".format(str(Error)))
	# grab the source of the page and parse it, build list of video links
	soup = BeautifulSoup(driver.page_source, features='html.parser')
	video_links = []  # list to track collected links
	videos = soup.find_all('ytd-video-renderer')  # find all container boxes for videos
	for i in range(len(videos)):
		title = videos[i].find('a', id='video-title')  # find link items with video title
		video_links.append(f"https://www.youtube.com{title['href']}")
	# print('number collected: ', len(video_links), '\n\n', video_links)
	return video_links[:100]  # return the first 100 video links


def imdb_search(driver: webdriver.Chrome, movie_title: str, num_results: int = 100) -> list:
	'''
	Scrapes videos associated with a given movie from imdb.

	Args:
		driver (webdriver.Chrome): Chrome Driver to be used
		movie_title (str): Title of Movie

	Returns:
		list
	'''
	driver.get("https://www.imdb.com/")  # load page
	driver.find_element_by_id("suggestion-search").send_keys(movie_title)  # type title
	# driver.find_element_by_id("suggestion-search-button").click()  # click search button
	# wait for first suggestion to load, click first one (react-autowhatever-1--item-0)
	try:  # wait for first suggestion to load
		wait = WebDriverWait(driver, 10)  # wait a maximum of 10 seconds for load
		first_suggestion = wait.until(EC.element_to_be_clickable(
			(By.ID, "react-autowhatever-1--item-0")))  # id of first item is consistent
		first_suggestion.click() # navigate to suggested page
	except NoSuchElementException as Error:  # page didn't load in a reasonable amount of time
		print("\n\tError: Page didn't load in a reasonable amount of time; try again.\n")
		print("\n\t{}\n".format(str(Error)))
	driver.find_element_by_xpath(
		"//span[@class='show_more quicklink']").click() # open "more" menu
	driver.find_element_by_xpath(
		"//a[text()='Trailers and Videos']").click() # open videos page
	# for desired number of results, collect video links
	video_links = []
	while len(video_links) < num_results:
		try: # wait for first video to be clickable as indicator of page load
			wait = WebDriverWait(driver, 10)  # wait a maximum of 10 seconds for load
			element = wait.until(EC.element_to_be_clickable(
				(By.XPATH, "//h2/a[@class='video-modal']")))  # first video clickable
		except NoSuchElementException as Error:  # page didn't load in a reasonable amount of time
			print("\n\tError: Page didn't load in a reasonable amount of time; try again.\n")
			print("\n\t{}\n".format(str(Error)))
		# grab the source of the page and parse it, build list of video links
		soup = BeautifulSoup(driver.page_source, features="html.parser")
		videos = soup.find_all("a", class_="video-modal")  # find all video instances (two each vid)
		for i in range(len(videos)):
			if videos[i].has_attr("data-video"): # only one of two sects for each has id
				video_links.append(
					f"https://www.imdb.com/video/{videos[i]['data-video']}") # save link
		# move onto next page if it exists
		try: # try clicking the "next page" button
			driver.find_element_by_xpath("//a[text()='Next »']").click()
		except NoSuchElementException: # button no longer exist--must be on last page
			break # no more results left
	print('number collected: ', len(video_links), '\n\n', video_links)
	return video_links[:100] # return the first 100 video links


def search_movie(driver: webdriver.Chrome, site_name: str, movie_title: str) -> list:
	'''
	Scrapes videos associated with a given movie from the selected source.

	Args:
		driver (webdriver.Chrome): Chrome Driver to be used
		site_name (str): Selected source; either IMDB or YouTube
		movie_title (str): Title of Movie

	Returns:
		list

	'''
	if site_name == "imdb":
		return imdb_search(driver, movie_title)
	elif site_name == "youtube":
		return youtube_search(driver, movie_title)
	else:
		raise NameError("Invalid source name: use either 'imdb' or 'youtube'")
	return  # return empty list for invalid input


def main():
	# display title
	print("\n\t--- Trailer Scraper by Max ---\n")
	# start, track driver
	driver = start_driver()
	# search for a given movie
	search_movie(driver, "youtube", "Batman Begins")


if __name__ == '__main__':
	main()
