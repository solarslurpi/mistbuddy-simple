import asyncio

from fastapi import  FastAPI, Form

from power_code import get_power_topics_for_tent, turn_on_power
from settings_model import Settings

misting_task = None

app = FastAPI()

@app.post("/api/v1/mistbuddy-lite/start")
async def mistbuddy_lite_start(tent_name: str = Form(...), duration_on: int = Form(...)):
    global misting_task
    # Get the mqtt topics based on the tent name. Each tent has their own mistbuddy.  Send POWER ON for duration_on seconds.
    settings = Settings.load()
    power_topics = get_power_topics_for_tent(tent_name, settings)
    misting_task = asyncio.create_task(mist_duration_every_minute(duration_on, power_topics))
    return {"tent_name": tent_name}

@app.get("/api/v1/mistbuddy-lite/stop")
async def mistbuddy_lite_stop():
    global misting_task
    if misting_task:

        misting_task.cancel()
        misting_task = None
    return {"status": "stopped"}

@app.post("/api/v1/mistbuddy-lite/duration_on")
async def mistbuddy_lite_duration_on(duration_on: int = Form(...)):
    duration_on = duration_on
    return {"duration_on": duration_on}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

async def mist_duration_every_minute(duration_on, power_topics):
    try:
        while True:
            asyncio.create_task(turn_on_power(duration_on, power_topics))
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        cleanup()
    except Exception as e: # unexpected.
        raise e
