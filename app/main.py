from fastapi import FastAPI

app = FastAPI(title="Order Service")

@app.get("/home")
async def get_home():
    return {"status": "ok"}