// Simple Flutter HTTP Client for Weed Detection
// Add to pubspec.yaml:
/*
dependencies:
  http: ^1.1.0
  image_picker: ^1.0.4
*/

import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

class SimpleWeedDetector extends StatefulWidget {
  @override
  _SimpleWeedDetectorState createState() => _SimpleWeedDetectorState();
}

class _SimpleWeedDetectorState extends State<SimpleWeedDetector> {
  File? _selectedImage;
  Map<String, dynamic>? _result;
  bool _isLoading = false;

  // Change this to your deployed API URL
  static const String API_URL = 'https://your-app-name.onrender.com';
  // For local testing: 'http://localhost:8080'

  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera, // or ImageSource.gallery
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _result = null;
        });
      }
    } catch (e) {
      _showSnackBar('Failed to pick image: $e');
    }
  }

  Future<void> _detectWeeds() async {
    if (_selectedImage == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$API_URL/predict_fast'), // Use fast endpoint for mobile
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', _selectedImage!.path),
      );

      var response = await request.send();
      var responseData = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        setState(() {
          _result = json.decode(responseData);
        });
      } else {
        _showSnackBar('Detection failed: ${response.statusCode}');
      }
    } catch (e) {
      _showSnackBar('Network error: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('🌿 Weed Detector'),
        backgroundColor: Colors.green,
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            // Image Display
            Container(
              height: 300,
              width: double.infinity,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey),
                borderRadius: BorderRadius.circular(8),
              ),
              child: _selectedImage != null
                  ? Image.file(_selectedImage!, fit: BoxFit.contain)
                  : Center(
                      child: Text(
                        'No image selected',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ),
            ),

            SizedBox(height: 20),

            // Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _pickImage,
                  icon: Icon(Icons.camera_alt),
                  label: Text('Take Photo'),
                ),
                ElevatedButton.icon(
                  onPressed: _selectedImage != null && !_isLoading
                      ? _detectWeeds
                      : null,
                  icon: _isLoading
                      ? SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(Icons.search),
                  label: Text('Detect'),
                ),
              ],
            ),

            SizedBox(height: 20),

            // Results
            if (_result != null) ...[
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Results',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text('Found ${_result!['detection_count']} weed(s)'),
                      SizedBox(height: 16),

                      // Detection List
                      if (_result!['detections'] != null)
                        ...(_result!['detections'] as List).map((detection) {
                          final classNames = [
                            "Clover",
                            "Crabgrass",
                            "Gamochaeta",
                            "Sphagneticola",
                            "Syndrella",
                          ];
                          final className =
                              classNames[detection['class_id']] ?? 'Unknown';

                          return ListTile(
                            leading: CircleAvatar(
                              backgroundColor: _getClassColor(
                                detection['class_id'],
                              ),
                              child: Text('${detection['class_id']}'),
                            ),
                            title: Text(className),
                            subtitle: Text(
                              'Confidence: ${(detection['confidence'] * 100).toStringAsFixed(1)}%',
                            ),
                            trailing: Text(
                              '(${detection['x1'].toInt()}, ${detection['y1'].toInt()})',
                              style: TextStyle(fontSize: 12),
                            ),
                          );
                        }).toList(),
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
    final colors = [
      Colors.red,
      Colors.green,
      Colors.blue,
      Colors.orange,
      Colors.purple,
    ];
    return colors[classId % colors.length];
  }
}

// Usage in main.dart:
/*
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Weed Detection App',
      theme: ThemeData(primarySwatch: Colors.green),
      home: SimpleWeedDetector(),
    );
  }
}
*/
