from fastapi import FastAPI, File, UploadFile, HTTPException, responses
from PIL import Image
from io import BytesIO
import numpy as np
from dataclasses import dataclass
from starlette.responses import StreamingResponse
import uvicorn

BLUE = (60, 70, 255)
ORANGE = (255, 110, 60)
GREEN = (81, 218, 76)
TEAL = (66, 255, 255)
YELLOW = (255, 255, 102)

COLOR_LIST = [BLUE, ORANGE, GREEN, TEAL, YELLOW]

@dataclass
class ImagePosition:
    x: int
    y: int

app = FastAPI()


def draw_color_box(img_arr, start: ImagePosition, end: ImagePosition, color: tuple[int, int, int]):
    for channel in range(0, 3):
        for i in range(start.y, end.y):
            for j in range(start.x, end.x):
                img_arr[i, j, channel] = color[channel]

    return img_arr

def draw_all_boxes(img_arr, color_list: list[tuple[int, int, int]]):
    for i, color in enumerate(color_list):
        box_start = ImagePosition(img_arr.shape[1] - (16 * (i + 1)), img_arr.shape[0] - 16)
        box_end = ImagePosition(img_arr.shape[1] - (16 * i), img_arr.shape[0])
        img_arr = draw_color_box(img_arr, box_start, box_end, color)
    return img_arr

@app.post("/convert")
async def convert(resize: bool=False, file: UploadFile = File(...)):    
    contents = await file.read()
    temp = BytesIO(contents)
    img = Image.open(temp).convert("RGB")
    if resize:
        img = img.resize((1024, 1024))

    img_arr = np.asarray(img)

    if img_arr.shape[0] < 16:
        raise HTTPException(status_code=400, detail=f"Use a bigger file.")
    
    if img_arr.shape[1] < 16:
        raise HTTPException(status_code=400, detail=f"Use a bigger file.")

    img_arr = draw_all_boxes(img_arr, COLOR_LIST)
    
    out_img = Image.fromarray(img_arr.astype('uint8'), 'RGB')
    out_bytes = BytesIO()
    out_img.save(out_bytes, format='png')
    out_img.tobytes()

    out_bytes.seek(0)
    return StreamingResponse(content=out_bytes, media_type="image/png")

@app.get("/")
async def docs_redirect():
    return responses.RedirectResponse(url='/docs')