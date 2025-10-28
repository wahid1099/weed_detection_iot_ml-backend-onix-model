#!/usr/bin/env python3
"""
Test script to verify ONNX Runtime works in the current environment
"""
import sys

def test_imports():
    """Test if all required packages can be imported"""
    try:
        print("Testing imports...")
        
        import fastapi
        print("✅ FastAPI imported successfully")
        
        import uvicorn
        print("✅ Uvicorn imported successfully")
        
        import numpy as np
        print("✅ NumPy imported successfully")
        
        import cv2
        print("✅ OpenCV imported successfully")
        
        from PIL import Image
        print("✅ Pillow imported successfully")
        
        # Test ONNX Runtime last as it's the problematic one
        import onnxruntime as ort
        print("✅ ONNX Runtime imported successfully")
        
        # Test ONNX Runtime functionality
        providers = ort.get_available_providers()
        print(f"✅ Available providers: {providers}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🧪 Testing Docker Environment")
    print("=" * 40)
    
    success = test_imports()
    
    print("=" * 40)
    if success:
        print("✅ All tests passed! Environment is ready.")
        sys.exit(0)
    else:
        print("❌ Tests failed! Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()