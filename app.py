from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn, io, base64
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import onnxruntime as ort
import cv2

app = FastAPI(title="YOLOv8 Weed Detection API + UI")

# Load ONNX model - use quantized model if available
try:
    session = ort.InferenceSession("./model_quantized.onnx", providers=['CPUExecutionProvider'])
    print("Loaded quantized ONNX model")
except:
    try:
        session = ort.InferenceSession("./model.onnx", providers=['CPUExecutionProvider'])
        print("Loaded regular ONNX model")
    except Exception as e:
        print(f"Error loading model: {e}")
        session = None

# Maximum display size for output images
MAX_DISPLAY_SIZE = 1024

@app.get("/", response_class=HTMLResponse)
def main():
    """Return simple upload UI"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h3>index.html not found. Please create it.</h3>"

# -------------------------------
# Preprocess Image for YOLOv8 ONNX
# -------------------------------
def preprocess(image: Image.Image, input_size=640):
    """Preprocess image for YOLOv8 ONNX model"""
    # Convert PIL to numpy array (RGB format)
    img = np.array(image)
    
    # Resize to model input size
    img = cv2.resize(img, (input_size, input_size))
    
    # Normalize to [0, 1]
    img = img.astype(np.float32) / 255.0
    
    # Transpose to CHW format (channels first)
    img = img.transpose(2, 0, 1)
    
    # Add batch dimension
    img = np.expand_dims(img, axis=0)
    
    return img

# -------------------------------
# Non-Maximum Suppression
# -------------------------------
def nms(boxes, scores, iou_threshold=0.5):
    """Apply Non-Maximum Suppression"""
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    
    # Get indices sorted by scores (descending)
    indices = np.argsort(scores)[::-1]
    
    keep = []
    while len(indices) > 0:
        current = indices[0]
        keep.append(current)
        
        if len(indices) == 1:
            break
            
        # Calculate IoU with remaining boxes
        current_box = boxes[current]
        remaining_boxes = boxes[indices[1:]]
        
        # Calculate intersection
        x1 = np.maximum(current_box[0], remaining_boxes[:, 0])
        y1 = np.maximum(current_box[1], remaining_boxes[:, 1])
        x2 = np.minimum(current_box[2], remaining_boxes[:, 2])
        y2 = np.minimum(current_box[3], remaining_boxes[:, 3])
        
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        
        # Calculate union
        current_area = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
        remaining_areas = (remaining_boxes[:, 2] - remaining_boxes[:, 0]) * (remaining_boxes[:, 3] - remaining_boxes[:, 1])
        union = current_area + remaining_areas - intersection
        
        # Calculate IoU
        iou = intersection / union
        
        # Keep boxes with IoU less than threshold
        indices = indices[1:][iou < iou_threshold]
    
    return keep

# -------------------------------
# Draw Boxes on Original Image
# -------------------------------
def draw_boxes(image: Image.Image, detections):
    """
    Draws YOLO boxes on the original image
    """
    draw = ImageDraw.Draw(image)
    
    # Class names for weed detection - matching your model's actual classes
    class_names = ["Clover", "Crabgrass", "Gamochaeta", "Sphagneticola", "Syndrella"]
    
    # Colors for different classes
    colors = ["red", "green", "blue", "yellow", "purple", "orange"]
    
    for detection in detections:
        x1, y1, x2, y2, conf, cls_id = detection
        
        # Get class name and color
        cls_name = class_names[cls_id] if cls_id < len(class_names) else f"class_{cls_id}"
        color = colors[cls_id % len(colors)]
        
        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # Draw label
        label = f"{cls_name}: {conf:.2f}"
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw label background
        label_y = max(0, y1 - text_height - 5)
        draw.rectangle([x1, label_y, x1 + text_width + 10, label_y + text_height + 5], 
                      fill=color, outline=color)
        
        # Draw label text
        draw.text((x1 + 5, label_y + 2), label, fill="white", font=font)
    
    return image

# -------------------------------
# Prediction Endpoint
# -------------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if session is None:
        return JSONResponse(content={"error": "Model not loaded"}, status_code=500)
    
    try:
        # Read and preprocess image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = image.size
        
        # Preprocess image
        input_tensor = preprocess(image)

        # Run inference
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_tensor})
        
        # Process YOLOv8 output
        predictions = outputs[0]  # Shape: (1, 84, 8400) for YOLOv8
        predictions = predictions[0]  # Remove batch dimension: (84, 8400)
        predictions = predictions.T  # Transpose to (8400, 84)
        
        # Extract boxes, scores, and class predictions
        boxes = []
        scores = []
        class_ids = []
        
        confidence_threshold = 0.25
        
        for prediction in predictions:
            # YOLOv8 format: [x_center, y_center, width, height, class_scores...]
            x_center, y_center, width, height = prediction[:4]
            class_scores = prediction[4:]
            
            # Get the class with highest score
            max_score = np.max(class_scores)
            
            if max_score > confidence_threshold:
                class_id = np.argmax(class_scores)
                
                # Convert center format to corner format
                x1 = x_center - width / 2
                y1 = y_center - height / 2
                x2 = x_center + width / 2
                y2 = y_center + height / 2
                
                boxes.append([x1, y1, x2, y2])
                scores.append(max_score)
                class_ids.append(class_id)
        
        # Apply Non-Maximum Suppression
        if len(boxes) > 0:
            keep_indices = nms(boxes, scores, iou_threshold=0.5)
            
            # Filter detections
            final_detections = []
            for i in keep_indices:
                detection = [
                    boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3],  # x1, y1, x2, y2
                    scores[i],  # confidence
                    class_ids[i]  # class_id
                ]
                final_detections.append(detection)
        else:
            final_detections = []

        # Scale detections back to original image size
        input_size = 640
        scaled_detections = []
        for detection in final_detections:
            x1, y1, x2, y2, conf, cls_id = detection
            
            # Scale coordinates from model input size to original image size
            x1_scaled = int(x1 * orig_w / input_size)
            y1_scaled = int(y1 * orig_h / input_size)
            x2_scaled = int(x2 * orig_w / input_size)
            y2_scaled = int(y2 * orig_h / input_size)
            
            # Ensure coordinates are within image bounds
            x1_scaled = max(0, min(x1_scaled, orig_w))
            y1_scaled = max(0, min(y1_scaled, orig_h))
            x2_scaled = max(0, min(x2_scaled, orig_w))
            y2_scaled = max(0, min(y2_scaled, orig_h))
            
            scaled_detections.append([x1_scaled, y1_scaled, x2_scaled, y2_scaled, conf, cls_id])

        # Draw boxes on image
        image_with_boxes = draw_boxes(image.copy(), scaled_detections)
        
        # Resize for display if too large
        if max(image_with_boxes.size) > MAX_DISPLAY_SIZE:
            image_with_boxes.thumbnail((MAX_DISPLAY_SIZE, MAX_DISPLAY_SIZE), Image.Resampling.LANCZOS)

        # Encode image to base64
        buffer = io.BytesIO()
        image_with_boxes.save(buffer, format="JPEG", quality=90)
        encoded_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Convert detections to JSON-serializable format
        detections_json = []
        for det in final_detections:
            detections_json.append({
                "x1": float(det[0]),
                "y1": float(det[1]), 
                "x2": float(det[2]),
                "y2": float(det[3]),
                "confidence": float(det[4]),
                "class_id": int(det[5])
            })

        return JSONResponse({
            "detections": detections_json,
            "detection_count": len(final_detections),
            "image_base64": f"data:image/jpeg;base64,{encoded_img}",
            "original_size": {"width": orig_w, "height": orig_h},
            "processed_size": {"width": image_with_boxes.size[0], "height": image_with_boxes.size[1]}
        })

    except Exception as e:
        print(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

# -------------------------------
# Run locally
# -------------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
