# trailer_server by max, built for redflag

import uvicorn
from fastapi import FastAPI

app = FastAPI()


# @app.get("/")
# def root():
#     return {"message": "Hello World"}

@app.get("/")
def get_preview(movie_title: str = "Batman Begins"):
    return {"trailer_link": "https://www.imdb.com/video/vi2992219161"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)