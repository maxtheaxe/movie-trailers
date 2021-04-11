# trailer_server by max, built for redflag

import uvicorn
from fastapi import FastAPI
import trailer_scraper
import asyncio

app = FastAPI()


@app.get("/")
async def get_preview(source: str, movie_title: str):
	driver = trailer_scraper.start_driver()
	video_list = trailer_scraper.search_movie(driver, source, movie_title)
	return video_list


if __name__ == "__main__":
	asyncio.run(uvicorn.run(app, host="0.0.0.0", port=8000))
