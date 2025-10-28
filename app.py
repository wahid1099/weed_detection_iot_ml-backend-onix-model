from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, io, base64
from PIL import Image, ImageDraw
import numpy as np
import onnxruntime as ort
import cv2

app = FastAPI(title="YOLOv8 Weed Detection API + UI")

# Load ONNX model
session = ort.InferenceSession("./model_quantized.onnx", providers=['CPUExecutionProvider'])

@app.get("/", response_class=HTMLResponse)
def main():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

def preprocess(image: Image.Image):
    img = np.array(image)
    img = cv2.resize(img, (640, 640))
    img = img.transpose(2, 0, 1)  # HWC → CHW
    img = img[np.newaxis, :, :, :].astype(np.float32) / 255.0
    return img

def draw_boxes(image, boxes):
    draw = ImageDraw.Draw(image)
    for box in boxes:
        x1, y1, x2, y2, conf, cls = box
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
    return image

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        # Read and preprocess image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        input_tensor = preprocess(image)

        # Run inference
        inputs = {session.get_inputs()[0].name: input_tensor}
        outputs = session.run(None, inputs)
        preds = np.array(outputs[0])

        # Post-process (for simplicity assume YOLO output: [x1,y1,x2,y2,conf,cls])
        boxes = preds.tolist()

        # Draw boxes
        image_with_boxes = draw_boxes(image.copy(), boxes)
        buffer = io.BytesIO()
        image_with_boxes.save(buffer, format="JPEG")
        encoded_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return JSONResponse({
            "detections": boxes,
            "image_base64": f"data:image/jpeg;base64,{encoded_img}"
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080)
