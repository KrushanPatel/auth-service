from fastapi import FastAPI 
import uvicorn

app = FastAPI()

@app.get('/')
@app.get('/home')
async def home():
    return {
            'user':'root',
            'message':'Welcome to auth service'
            }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("auth-service starts...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
