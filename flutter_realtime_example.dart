// Flutter Real-time Weed Detection Example
// Add these dependencies to pubspec.yaml:
/*
dependencies:
  flutter:
    sdk: flutter
  camera: ^0.10.5+5
  web_socket_channel: ^2.4.0
  http: ^1.1.0
  image: ^4.1.3
  path_provider: ^2.1.1
*/

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:image/image.dart' as img;

class RealTimeWeedDetection extends StatefulWidget {
  @override
  _RealTimeWeedDetectionState createState() => _RealTimeWeedDetectionState();
}

class _RealTimeWeedDetectionState extends State<RealTimeWeedDetection> {
  CameraController? _cameraController;
  WebSocketChannel? _channel;
  List<Detection> _detections = [];
  bool _isDetecting = false;
  bool _isConnected = false;

  // Your API URL - change this to your deployed URL
  static const String API_URL = 'wss://your-app-name.onrender.com/ws';
  // For local testing: 'ws://localhost:8080/ws'

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _connectWebSocket();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    if (cameras.isNotEmpty) {
      _cameraController = CameraController(
        cameras.first,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await _cameraController!.initialize();
      setState(() {});

      // Start continuous detection
      _startContinuousDetection();
    }
  }

  void _connectWebSocket() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(API_URL));

      _channel!.stream.listen(
        (data) {
          final response = json.decode(data);
          if (response['type'] == 'detection_result') {
            setState(() {
              _detections = (response['detections'] as List)
                  .map((d) => Detection.fromJson(d))
                  .toList();
            });
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
          setState(() {
            _isConnected = false;
          });
        },
        onDone: () {
          setState(() {
            _isConnected = false;
          });
        },
      );

      setState(() {
        _isConnected = true;
      });
    } catch (e) {
      print('Failed to connect WebSocket: $e');
    }
  }

  void _startContinuousDetection() {
    if (_cameraController == null || !_cameraController!.value.isInitialized)
      return;

    // Capture and process frames every 2 seconds
    Timer.periodic(Duration(seconds: 2), (timer) async {
      if (!_isDetecting && _isConnected && mounted) {
        await _captureAndDetect();
      }
    });
  }

  Future<void> _captureAndDetect() async {
    if (_isDetecting || _channel == null) return;

    setState(() {
      _isDetecting = true;
    });

    try {
      final XFile imageFile = await _cameraController!.takePicture();
      final Uint8List imageBytes = await imageFile.readAsBytes();

      // Resize image for faster processing
      img.Image? image = img.decodeImage(imageBytes);
      if (image != null) {
        // Resize to max 640px for faster processing
        if (image.width > 640 || image.height > 640) {
          image = img.copyResize(image, width: 640);
        }

        final resizedBytes = img.encodeJpg(image, quality: 70);
        final base64Image = base64Encode(resizedBytes);

        // Send to WebSocket
        final message = {
          'image': 'data:image/jpeg;base64,$base64Image',
          'timestamp': DateTime.now().millisecondsSinceEpoch.toString(),
        };

        _channel!.sink.add(json.encode(message));
      }
    } catch (e) {
      print('Error capturing image: $e');
    } finally {
      setState(() {
        _isDetecting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('🌿 Real-time Weed Detection'),
        backgroundColor: Colors.green,
        actions: [
          Icon(
            _isConnected ? Icons.wifi : Icons.wifi_off,
            color: _isConnected ? Colors.white : Colors.red,
          ),
          SizedBox(width: 16),
        ],
      ),
      body: Stack(
        children: [
          // Camera Preview
          CameraPreview(_cameraController!),

          // Detection Overlays
          ..._detections
              .map(
                (detection) => Positioned(
                  left: detection.x1,
                  top: detection.y1,
                  child: Container(
                    width: detection.x2 - detection.x1,
                    height: detection.y2 - detection.y1,
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: _getClassColor(detection.classId),
                        width: 3,
                      ),
                    ),
                    child: Container(
                      padding: EdgeInsets.all(4),
                      color: _getClassColor(detection.classId).withOpacity(0.8),
                      child: Text(
                        '${detection.className}\n${(detection.confidence * 100).toInt()}%',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
              )
              .toList(),

          // Status Overlay
          Positioned(
            top: 16,
            left: 16,
            child: Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Status: ${_isConnected ? "Connected" : "Disconnected"}',
                    style: TextStyle(color: Colors.white),
                  ),
                  Text(
                    'Detections: ${_detections.length}',
                    style: TextStyle(color: Colors.white),
                  ),
                  if (_isDetecting)
                    Text(
                      'Processing...',
                      style: TextStyle(color: Colors.yellow),
                    ),
                ],
              ),
            ),
          ),

          // Detection List
          if (_detections.isNotEmpty)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Container(
                height: 120,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _detections.length,
                  itemBuilder: (context, index) {
                    final detection = _detections[index];
                    return Container(
                      width: 150,
                      margin: EdgeInsets.only(right: 8),
                      padding: EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.black87,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            detection.className,
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Confidence: ${(detection.confidence * 100).toInt()}%',
                            style: TextStyle(color: Colors.white70),
                          ),
                          Text(
                            'Position: (${detection.x1.toInt()}, ${detection.y1.toInt()})',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _captureAndDetect,
        backgroundColor: Colors.green,
        child: Icon(_isDetecting ? Icons.hourglass_empty : Icons.camera_alt),
      ),
    );
  }

  Color _getClassColor(int classId) {
    final colors = [
      Colors.red, // Clover
      Colors.orange, // Crabgrass
      Colors.blue, // Gamochaeta
      Colors.purple, // Sphagneticola
      Colors.pink, // Syndrella
    ];
    return colors[classId % colors.length];
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _channel?.sink.close();
    super.dispose();
  }
}

// Detection model class
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
    return Detection(
      x1: json['x1'].toDouble(),
      y1: json['y1'].toDouble(),
      x2: json['x2'].toDouble(),
      y2: json['y2'].toDouble(),
      confidence: json['confidence'].toDouble(),
      classId: json['class_id'],
      className: json['class_name'] ?? 'Unknown',
    );
  }
}
