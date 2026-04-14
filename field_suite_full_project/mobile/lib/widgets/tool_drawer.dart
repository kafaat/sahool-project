import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/field_provider.dart';

class ToolDrawer extends StatelessWidget {
  const ToolDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<FieldProvider>(
      builder: (context, provider, child) {
        return Drawer(
          child: SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(context).colorScheme.primary,
                        Theme.of(context).colorScheme.primaryContainer,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.agriculture,
                        size: 48,
                        color: Theme.of(context).colorScheme.onPrimary,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Field Suite',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Theme.of(context).colorScheme.onPrimary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        'Drawing Tools',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Theme.of(context).colorScheme.onPrimary.withOpacity(0.8),
                        ),
                      ),
                    ],
                  ),
                ),

                // Drawing Tools Section
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'DRAWING TOOLS',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),

                _ToolTile(
                  icon: Icons.near_me,
                  label: 'Select',
                  isActive: provider.activeTool == DrawingTool.select,
                  onTap: () {
                    provider.setTool(DrawingTool.select);
                    Navigator.pop(context);
                  },
                ),
                _ToolTile(
                  icon: Icons.pentagon_outlined,
                  label: 'Polygon',
                  isActive: provider.activeTool == DrawingTool.polygon,
                  onTap: () {
                    provider.setTool(DrawingTool.polygon);
                    Navigator.pop(context);
                  },
                ),
                _ToolTile(
                  icon: Icons.crop_square,
                  label: 'Rectangle',
                  isActive: provider.activeTool == DrawingTool.rectangle,
                  onTap: () {
                    provider.setTool(DrawingTool.rectangle);
                    Navigator.pop(context);
                  },
                ),
                _ToolTile(
                  icon: Icons.circle_outlined,
                  label: 'Circle',
                  isActive: provider.activeTool == DrawingTool.circle,
                  onTap: () {
                    provider.setTool(DrawingTool.circle);
                    Navigator.pop(context);
                  },
                ),
                _ToolTile(
                  icon: Icons.rotate_right,
                  label: 'Pivot',
                  isActive: provider.activeTool == DrawingTool.pivot,
                  onTap: () {
                    provider.setTool(DrawingTool.pivot);
                    Navigator.pop(context);
                  },
                ),

                const Divider(height: 32),

                // Actions Section
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text(
                    'ACTIONS',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
                const SizedBox(height: 8),

                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: FilledButton.icon(
                    onPressed: provider.isLoading
                        ? null
                        : () {
                            provider.autoDetect();
                            Navigator.pop(context);
                          },
                    icon: const Icon(Icons.auto_fix_high),
                    label: const Text('Auto Detect Fields'),
                  ),
                ),

                const Spacer(),

                // Footer
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    'Tap on map to add points\nFinish with 3+ points',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _ToolTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _ToolTile({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(
        icon,
        color: isActive
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).colorScheme.onSurfaceVariant,
      ),
      title: Text(
        label,
        style: TextStyle(
          fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
          color: isActive
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.onSurface,
        ),
      ),
      selected: isActive,
      selectedTileColor: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      onTap: onTap,
    );
  }
}
