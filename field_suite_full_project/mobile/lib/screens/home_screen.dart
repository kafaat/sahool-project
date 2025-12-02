import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/field_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/field_map.dart';
import '../widgets/tool_drawer.dart';
import '../widgets/field_list_sheet.dart';
import '../widgets/analytics_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  late AnimationController _fabAnimationController;

  @override
  void initState() {
    super.initState();
    _fabAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _fabAnimationController.forward();
  }

  @override
  void dispose() {
    _fabAnimationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Consumer<FieldProvider>(
      builder: (context, provider, child) {
        return Scaffold(
          key: _scaffoldKey,
          appBar: _buildAppBar(context, provider),
          drawer: const ToolDrawer(),
          body: Stack(
            children: [
              // Map
              const FieldMap(),

              // Quick Stats Overlay
              Positioned(
                top: 16,
                left: 16,
                child: _buildQuickStats(context, provider),
              ),

              // Loading Indicator
              if (provider.isLoading)
                Positioned(
                  top: 80,
                  left: 0,
                  right: 0,
                  child: _buildLoadingIndicator(context),
                ),

              // Drawing Info Bar
              if (provider.isDrawing)
                Positioned(
                  bottom: 100,
                  left: 16,
                  right: 16,
                  child: _buildDrawingBar(context, provider),
                ),

              // Error Snackbar
              if (provider.errorMessage != null)
                Positioned(
                  bottom: 16,
                  left: 16,
                  right: 16,
                  child: _buildErrorBar(context, provider),
                ),
            ],
          ),
          floatingActionButton: _buildFAB(context, provider),
        );
      },
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context, FieldProvider provider) {
    return AppBar(
      elevation: 0,
      title: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: AppTheme.accentYellow.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text(
              '🌾',
              style: TextStyle(fontSize: 18),
            ),
          ),
          const SizedBox(width: 10),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Field Suite',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                'Agricultural Management',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w400,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ],
      ),
      leading: IconButton(
        icon: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.menu, size: 20),
        ),
        onPressed: () => _scaffoldKey.currentState?.openDrawer(),
      ),
      actions: [
        // API Connection Status
        _buildConnectionBadge(provider),
        const SizedBox(width: 8),
        // Refresh Button
        IconButton(
          icon: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            child: provider.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.refresh_rounded),
          ),
          onPressed: provider.isLoading
              ? null
              : () async {
                  await provider.checkApiConnection();
                  await provider.loadFields();
                },
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildConnectionBadge(FieldProvider provider) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 12),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: provider.isApiConnected
            ? AppTheme.successColor.withOpacity(0.2)
            : AppTheme.dangerColor.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: provider.isApiConnected
              ? AppTheme.successColor.withOpacity(0.5)
              : AppTheme.dangerColor.withOpacity(0.5),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: provider.isApiConnected
                  ? AppTheme.successColor
                  : AppTheme.dangerColor,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: provider.isApiConnected
                      ? AppTheme.successColor.withOpacity(0.5)
                      : AppTheme.dangerColor.withOpacity(0.5),
                  blurRadius: 4,
                  spreadRadius: 1,
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),
          Text(
            provider.isApiConnected ? 'API' : 'Offline',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: provider.isApiConnected
                  ? Colors.white
                  : Colors.white70,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStats(BuildContext context, FieldProvider provider) {
    return Card(
      elevation: 8,
      shadowColor: Colors.black26,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildStatItem(
              context,
              Icons.layers_rounded,
              provider.fields.length.toString(),
              'Fields',
              AppTheme.primaryGreen,
            ),
            Container(
              height: 32,
              width: 1,
              margin: const EdgeInsets.symmetric(horizontal: 12),
              color: Theme.of(context).dividerColor,
            ),
            _buildStatItem(
              context,
              Icons.square_foot_rounded,
              '${(provider.fields.length * 0.5).toStringAsFixed(1)}',
              'km²',
              AppTheme.accentYellow,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context,
    IconData icon,
    String value,
    String label,
    Color color,
  ) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color, size: 18),
        ),
        const SizedBox(width: 10),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: Theme.of(context).textTheme.bodySmall?.color,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildLoadingIndicator(BuildContext context) {
    return Center(
      child: Card(
        elevation: 8,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: AppTheme.primaryGreen,
                ),
              ),
              const SizedBox(width: 16),
              const Text(
                'Loading fields...',
                style: TextStyle(fontWeight: FontWeight.w500),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDrawingBar(BuildContext context, FieldProvider provider) {
    return Card(
      elevation: 12,
      shadowColor: AppTheme.primaryGreen.withOpacity(0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: AppTheme.accentYellow,
          width: 2,
        ),
      ),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            colors: [
              AppTheme.primaryGreen,
              AppTheme.primaryGreenDark,
            ],
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.accentYellow,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                Icons.edit_location_alt,
                color: AppTheme.primaryGreenDark,
                size: 22,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Drawing ${provider.activeTool.name}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${provider.drawingPoints.length} points placed',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            if (provider.drawingPoints.length >= 3)
              ElevatedButton.icon(
                onPressed: () => _showNameDialog(context, provider),
                icon: const Icon(Icons.check_rounded, size: 18),
                label: const Text('Finish'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.accentYellow,
                  foregroundColor: AppTheme.primaryGreenDark,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
              ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: provider.clearDrawing,
              icon: const Icon(Icons.close_rounded, color: Colors.white70),
              style: IconButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorBar(BuildContext context, FieldProvider provider) {
    return Card(
      elevation: 8,
      shadowColor: AppTheme.dangerColor.withOpacity(0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            colors: [
              AppTheme.dangerColor,
              AppTheme.dangerColor.withRed(180),
            ],
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.error_outline_rounded,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                provider.errorMessage!,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.close_rounded, color: Colors.white),
              onPressed: provider.clearError,
              style: IconButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFAB(BuildContext context, FieldProvider provider) {
    return ScaleTransition(
      scale: CurvedAnimation(
        parent: _fabAnimationController,
        curve: Curves.easeOutBack,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          // Auto Detect Button
          FloatingActionButton.small(
            heroTag: 'autoDetect',
            onPressed: provider.isLoading ? null : provider.autoDetect,
            tooltip: 'Auto Detect Fields',
            backgroundColor: AppTheme.accentYellow,
            foregroundColor: AppTheme.primaryGreenDark,
            elevation: 6,
            child: const Icon(Icons.auto_fix_high),
          ),
          const SizedBox(height: 12),
          // Field List Button
          FloatingActionButton.extended(
            heroTag: 'fieldList',
            onPressed: () => _showFieldListSheet(context),
            tooltip: 'View Fields',
            icon: const Icon(Icons.layers_rounded),
            label: Text(
              '${provider.fields.length} Fields',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  void _showNameDialog(BuildContext context, FieldProvider provider) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.primaryGreen.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                Icons.agriculture_rounded,
                color: AppTheme.primaryGreen,
              ),
            ),
            const SizedBox(width: 14),
            const Text('Name Your Field'),
          ],
        ),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            labelText: 'Field Name',
            hintText: 'e.g., North Wheat Field',
            prefixIcon: Icon(
              Icons.edit_rounded,
              color: AppTheme.primaryGreen,
            ),
          ),
          autofocus: true,
          textCapitalization: TextCapitalization.words,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton.icon(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                provider.finishDrawing(controller.text.trim());
                Navigator.pop(context);
              }
            },
            icon: const Icon(Icons.save_rounded, size: 18),
            label: const Text('Save Field'),
          ),
        ],
      ),
    );
  }

  void _showFieldListSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.15),
                blurRadius: 20,
                offset: const Offset(0, -5),
              ),
            ],
          ),
          child: FieldListSheet(scrollController: scrollController),
        ),
      ),
    );
  }
}
