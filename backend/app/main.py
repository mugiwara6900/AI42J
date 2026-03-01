from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
  return {"Hello" : "World"}


if __name__ == "__main__":
    import uvicorn
    # Change port and host here directly
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)