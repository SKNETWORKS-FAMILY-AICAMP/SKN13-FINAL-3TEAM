from fastapi import FastAPI
from pydantic import BaseModel
from handler import rp_handler

app = FastAPI()

class RunSyncIn(BaseModel):
    input: dict

@app.post("/runsync")
def runsync(inp: RunSyncIn):
    # Serverless 없이 로컬 라우팅 디버깅
    return rp_handler({"input": inp.input})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
