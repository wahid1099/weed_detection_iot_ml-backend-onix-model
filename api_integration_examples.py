"""
API Integration Examples for Flutter App
This file shows how to integrate the YOLOv8 weed detection API
"""

# =============================================================================
# 1. FLUTTER HTTP CLIENT EXAMPLE
# =============================================================================

flutter_http_example = '''
// pubspec.yaml dependencies
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  image_picker: ^1.0.4
  camera: ^0.10.5+5
  path_provider: ^2.1.1

// lib/services/weed_detection_service.dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class WeedDetectionService {
  static const String baseUrl = 'https://weed-detection-iot-ml-backend-onix-model.onrender.com/';
  
  // Upload image for detection
  static Future<Map<String, dynamic>> detectWeeds(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/predict'),
      );
      
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
        ),
      );
      
      var response = await request.send();
      var responseData = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        return json.decode(responseData);
      } else {
        throw Exception('Detection failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }
  
  // Get detection results with image
  static Future<DetectionResult> getDetectionResult(File imageFile) async {
    var result = await detectWeeds(imageFile);
    return DetectionResult.fromJson(result);
  }
}

// lib/models/detection_result.dart
class DetectionResult {
  final List<Detection> detections;
  final int detectionCount;
  final String imageBase64;
  final Size originalSize;
  final Size processedSize;
  
  DetectionResult({
    required this.detections,
    required this.detectionCount,
    required this.imageBase64,
    required this.originalSize,
    required this.processedSize,
  });
  
  factory DetectionResult.fromJson(Map<String, dynamic> json) {
    return DetectionResult(
      detections: (json['detections'] as List)
          .map((d) => Detection.fromJson(d))
          .toList(),
      detectionCount: json['detection_count'],
      imageBase64: json['image_base64'],
      originalSize: Size(
        json['original_size']['width'].toDouble(),
        json['original_size']['height'].toDouble(),
      ),
      processedSize: Size(
        json['processed_size']['width'].toDouble(),
        json['processed_size']['height'].toDouble(),
      ),
    );
  }
}

class Detection {
  final double x1, y1, x2, y2;
  final double confidence;
  final int classId;
  final String className;
  
  Detection({
    required this.x1,
    required this.y1,
    required this.x2,
    required this.y2,
    required this.confidence,
    required this.classId,
    required this.className,
  });
  
  factory Detection.fromJson(Map<String, dynamic> json) {
    final classNames = ["Clover", "Crabgrass", "Gamochaeta", "Sphagneticola", "Syndrella"];
    
    return Detection(
      x1: json['x1'].toDouble(),
      y1: json['y1'].toDouble(),
      x2: json['x2'].toDouble(),
      y2: json['y2'].toDouble(),
      confidence: json['confidence'].toDouble(),
      classId: json['class_id'],
      className: classNames[json['class_id']] ?? 'Unknown',
    );
  }
}
'''

# =============================================================================
# 2. FLUTTER UI EXAMPLE
# =============================================================================

flutter_ui_example = '''
// lib/screens/weed_detection_screen.dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'dart:convert';

class WeedDetectionScreen extends StatefulWidget {
  @override
  _WeedDetectionScreenState createState() => _WeedDetectionScreenState();
}

class _WeedDetectionScreenState extends State<WeedDetectionScreen> {
  File? _selectedImage;
  DetectionResult? _detectionResult;
  bool _isLoading = false;
  final ImagePicker _picker = ImagePicker();
  
  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );
      
      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _detectionResult = null;
        });
      }
    } catch (e) {
      _showError('Failed to pick image: $e');
    }
  }
  
  Future<void> _detectWeeds() async {
    if (_selectedImage == null) return;
    
    setState(() {
      _isLoading = true;
    });
    
    try {
      final result = await WeedDetectionService.getDetectionResult(_selectedImage!);
      setState(() {
        _detectionResult = result;
      });
    } catch (e) {
      _showError('Detection failed: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('🌿 Weed Detection'),
        backgroundColor: Colors.green,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            // Image Selection Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: Icon(Icons.camera_alt),
                  label: Text('Camera'),
                ),
                ElevatedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: Icon(Icons.photo_library),
                  label: Text('Gallery'),
                ),
              ],
            ),
            
            SizedBox(height: 20),
            
            // Selected Image Display
            if (_selectedImage != null) ...[
              Container(
                height: 300,
                width: double.infinity,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Image.file(
                  _selectedImage!,
                  fit: BoxFit.contain,
                ),
              ),
              
              SizedBox(height: 20),
              
              // Detect Button
              ElevatedButton(
                onPressed: _isLoading ? null : _detectWeeds,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                ),
                child: _isLoading
                    ? CircularProgressIndicator(color: Colors.white)
                    : Text('🔍 Detect Weeds', style: TextStyle(fontSize: 16)),
              ),
            ],
            
            SizedBox(height: 20),
            
            // Detection Results
            if (_detectionResult != null) ...[
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Detection Results',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 10),
                      Text('Found ${_detectionResult!.detectionCount} weed(s)'),
                      
                      // Results Image
                      if (_detectionResult!.imageBase64.isNotEmpty) ...[
                        SizedBox(height: 10),
                        Container(
                          height: 300,
                          width: double.infinity,
                          child: Image.memory(
                            base64Decode(_detectionResult!.imageBase64.split(',')[1]),
                            fit: BoxFit.contain,
                          ),
                        ),
                      ],
                      
                      // Detection List
                      ...._detectionResult!.detections.map((detection) => 
                        ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getClassColor(detection.classId),
                            child: Text('${detection.classId}'),
                          ),
                          title: Text(detection.className),
                          subtitle: Text('Confidence: ${(detection.confidence * 100).toStringAsFixed(1)}%'),
                          trailing: Text(
                            '${detection.x1.toInt()}, ${detection.y1.toInt()}',
                            style: TextStyle(fontSize: 12),
                          ),
                        ),
                      ).toList(),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  Color _getClassColor(int classId) {
    final colors = [Colors.red, Colors.green, Colors.blue, Colors.yellow, Colors.purple];
    return colors[classId % colors.length];
  }
}
'''

print("Flutter integration examples created!")
print("Check the flutter_http_example and flutter_ui_example variables above.")