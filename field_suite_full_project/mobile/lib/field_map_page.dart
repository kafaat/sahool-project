import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

enum Tool { select, polygon }

class FieldMapPage extends StatefulWidget {
  const FieldMapPage({super.key});
  @override
  State<FieldMapPage> createState() => _FieldMapPageState();
}

class _FieldMapPageState extends State<FieldMapPage> {
  Tool tool = Tool.select;
  List<LatLng> pts = [];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Field Tools (Mobile)")),
      body: Stack(
        children: [
          MaplibreMap(
            styleString: "https://demotiles.maplibre.org/style.json",
            initialCameraPosition:
                const CameraPosition(target: LatLng(15, 45), zoom: 5),
            onMapClick: (p, c) {
              if (tool == Tool.polygon) {
                setState(() => pts.add(c));
              }
            },
          ),
          Positioned(
            left: 10,
            top: 10,
            child: Column(children: [
              ElevatedButton(
                  onPressed: () => setState(() => tool = Tool.select),
                  child: const Text("Select")),
              ElevatedButton(
                  onPressed: () => setState(() => tool = Tool.polygon),
                  child: const Text("Polygon")),
            ]),
          ),
        ],
      ),
    );
  }
}
