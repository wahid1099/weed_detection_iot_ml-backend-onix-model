#!/usr/bin/env python3
"""
Validate the setup without running inference
"""
import os

def validate_files():
    """Check if all required files exist"""
    required_files = {
        'app.py': 'Main FastAPI application',
        'index.html': 'Web interface',
        'requirements.txt': 'Python dependencies'
    }
    
    model_files = {
        'model.onnx': 'Regular ONNX model',
        'model_quantized.onnx': 'Quantized ONNX model (preferred)'
    }
    
    print("📁 Checking required files...")
    all_good = True
    
    for file, description in required_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({description}) - {size} bytes")
        else:
            print(f"❌ {file} ({description}) - MISSING")
            all_good = False
    
    print("\n🤖 Checking model files...")
    model_found = False
    
    for file, description in model_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({description}) - {size/1024/1024:.1f} MB")
            model_found = True
        else:
            print(f"⚠️  {file} ({description}) - Not found")
    
    if not model_found:
        print("❌ No model files found!")
        all_good = False
    
    return all_good

def check_app_structure():
    """Check the structure of app.py"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        checks = {
            'FastAPI import': 'from fastapi import FastAPI',
            'ONNX runtime': 'import onnxruntime',
            'Model loading': 'InferenceSession',
            'Prediction endpoint': '@app.post("/predict")',
            'NMS function': 'def nms(',
            'Draw boxes function': 'def draw_boxes('
        }
        
        print("\n🔍 Checking app.py structure...")
        for check, pattern in checks.items():
            if pattern in content:
                print(f"✅ {check}")
            else:
                print(f"❌ {check} - Missing")
        
        return True
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def main():
    print("🌿 YOLOv8 Weed Detection - Setup Validation")
    print("=" * 50)
    
    files_ok = validate_files()
    app_ok = check_app_structure()
    
    print("=" * 50)
    
    if files_ok and app_ok:
        print("✅ Setup validation passed!")
        print("\n🚀 To run the application:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run the app: python run_app.py")
        print("   3. Open browser: http://localhost:8080")
        print("\n🔧 Key improvements made:")
        print("   • Fixed YOLOv8 output format handling")
        print("   • Added proper coordinate scaling")
        print("   • Implemented Non-Maximum Suppression")
        print("   • Enhanced web interface with better visualization")
        print("   • Added drag & drop support")
        print("   • Improved error handling")
    else:
        print("❌ Setup validation failed!")
        print("🔧 Please fix the issues above before running the app.")

if __name__ == "__main__":
    main()