from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AWD Backend Server Running"}