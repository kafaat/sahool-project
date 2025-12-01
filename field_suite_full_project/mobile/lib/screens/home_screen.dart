import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/field_provider.dart';
import '../widgets/field_map.dart';
import '../widgets/tool_drawer.dart';
import '../widgets/field_list_sheet.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    return Consumer<FieldProvider>(
      builder: (context, provider, child) {
        return Scaffold(
          key: _scaffoldKey,
          appBar: AppBar(
            title: const Text('Field Suite'),
            leading: IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => _scaffoldKey.currentState?.openDrawer(),
            ),
            actions: [
              // API Connection Status
              Container(
                margin: const EdgeInsets.only(right: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: provider.isApiConnected
                      ? Colors.green.shade100
                      : Colors.red.shade100,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: provider.isApiConnected ? Colors.green : Colors.red,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      provider.isApiConnected ? 'Online' : 'Offline',
                      style: TextStyle(
                        fontSize: 12,
                        color: provider.isApiConnected
                            ? Colors.green.shade700
                            : Colors.red.shade700,
                      ),
                    ),
                  ],
                ),
              ),
              // Refresh Button
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: provider.isLoading
                    ? null
                    : () async {
                        await provider.checkApiConnection();
                        await provider.loadFields();
                      },
              ),
            ],
          ),
          drawer: const ToolDrawer(),
          body: Stack(
            children: [
              // Map
              const FieldMap(),

              // Loading Indicator
              if (provider.isLoading)
                const Positioned(
                  top: 16,
                  left: 0,
                  right: 0,
                  child: Center(
                    child: Card(
                      child: Padding(
                        padding: EdgeInsets.all(12),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            SizedBox(width: 12),
                            Text('Loading...'),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

              // Drawing Info Bar
              if (provider.isDrawing)
                Positioned(
                  bottom: 100,
                  left: 16,
                  right: 16,
                  child: Card(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(
                            Icons.edit_location_alt,
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Drawing ${provider.activeTool.name} • ${provider.drawingPoints.length} points',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.onPrimaryContainer,
                              ),
                            ),
                          ),
                          if (provider.drawingPoints.length >= 3)
                            TextButton(
                              onPressed: () => _showNameDialog(context, provider),
                              child: const Text('Finish'),
                            ),
                          TextButton(
                            onPressed: provider.clearDrawing,
                            child: const Text('Cancel'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

              // Error Snackbar
              if (provider.errorMessage != null)
                Positioned(
                  bottom: 16,
                  left: 16,
                  right: 16,
                  child: Material(
                    elevation: 4,
                    borderRadius: BorderRadius.circular(8),
                    color: Colors.red.shade700,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: Colors.white),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              provider.errorMessage!,
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, color: Colors.white),
                            onPressed: provider.clearError,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
          floatingActionButton: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              // Auto Detect Button
              FloatingActionButton.small(
                heroTag: 'autoDetect',
                onPressed: provider.isLoading ? null : provider.autoDetect,
                tooltip: 'Auto Detect Fields',
                child: const Icon(Icons.auto_fix_high),
              ),
              const SizedBox(height: 8),
              // Field List Button
              FloatingActionButton(
                heroTag: 'fieldList',
                onPressed: () => _showFieldListSheet(context),
                tooltip: 'View Fields',
                child: Badge(
                  label: Text('${provider.fields.length}'),
                  isLabelVisible: provider.fields.isNotEmpty,
                  child: const Icon(Icons.layers),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showNameDialog(BuildContext context, FieldProvider provider) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Name Your Field'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Field Name',
            hintText: 'Enter a name for this field',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                provider.finishDrawing(controller.text.trim());
                Navigator.pop(context);
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _showFieldListSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => FieldListSheet(
          scrollController: scrollController,
        ),
      ),
    );
  }
}
