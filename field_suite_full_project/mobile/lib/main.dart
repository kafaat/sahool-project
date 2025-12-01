import 'package:flutter/material.dart';
import 'field_map_page.dart';

void main() {
  runApp(const FieldSuiteApp());
}

class FieldSuiteApp extends StatelessWidget {
  const FieldSuiteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Field Suite Mobile',
      home: const FieldMapPage(),
    );
  }
}
