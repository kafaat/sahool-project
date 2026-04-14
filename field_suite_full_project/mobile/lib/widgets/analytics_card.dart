import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Analytics Card Widget
/// Displays field statistics in a professional agricultural style
class AnalyticsCard extends StatelessWidget {
  final String title;
  final String value;
  final String? unit;
  final IconData icon;
  final Color? color;
  final double? change;
  final bool isHighlighted;

  const AnalyticsCard({
    super.key,
    required this.title,
    required this.value,
    this.unit,
    required this.icon,
    this.color,
    this.change,
    this.isHighlighted = false,
  });

  @override
  Widget build(BuildContext context) {
    final cardColor = color ?? AppTheme.primaryGreen;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isHighlighted
            ? cardColor.withOpacity(0.1)
            : Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isHighlighted
              ? cardColor.withOpacity(0.3)
              : Theme.of(context).dividerColor,
          width: 1.5,
        ),
        boxShadow: isHighlighted
            ? [
                BoxShadow(
                  color: cardColor.withOpacity(0.15),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ]
            : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: cardColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              icon,
              color: cardColor,
              size: 22,
            ),
          ),
          const SizedBox(height: 14),

          // Label
          Text(
            title.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.5,
              color: Theme.of(context).textTheme.bodySmall?.color,
            ),
          ),
          const SizedBox(height: 6),

          // Value
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                value,
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: Theme.of(context).textTheme.bodyLarge?.color,
                ),
              ),
              if (unit != null) ...[
                const SizedBox(width: 4),
                Text(
                  unit!,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                ),
              ],
            ],
          ),

          // Change indicator
          if (change != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(
                  change! >= 0
                      ? Icons.trending_up_rounded
                      : Icons.trending_down_rounded,
                  size: 16,
                  color: change! >= 0
                      ? AppTheme.successColor
                      : AppTheme.dangerColor,
                ),
                const SizedBox(width: 4),
                Text(
                  '${change! >= 0 ? '+' : ''}${change!.toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: change! >= 0
                        ? AppTheme.successColor
                        : AppTheme.dangerColor,
                  ),
                ),
                Text(
                  ' this month',
                  style: TextStyle(
                    fontSize: 11,
                    color: Theme.of(context).textTheme.bodySmall?.color,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// Weather Card Widget
/// Displays current weather conditions for field work
class WeatherCard extends StatelessWidget {
  final int temperature;
  final String condition;
  final int humidity;
  final int windSpeed;
  final String forecast;

  const WeatherCard({
    super.key,
    required this.temperature,
    required this.condition,
    required this.humidity,
    required this.windSpeed,
    required this.forecast,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryGreen,
            AppTheme.primaryGreenDark,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryGreen.withOpacity(0.3),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'FIELD CONDITIONS',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.5,
                  color: Colors.white.withOpacity(0.8),
                ),
              ),
              Icon(
                Icons.wb_sunny_rounded,
                color: AppTheme.accentYellow,
                size: 22,
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Main temperature
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$temperature',
                style: const TextStyle(
                  fontSize: 52,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                  height: 1,
                ),
              ),
              const Text(
                '°C',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w500,
                  color: Colors.white70,
                ),
              ),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    condition,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      _buildWeatherDetail(Icons.water_drop_outlined, '$humidity%'),
                      const SizedBox(width: 12),
                      _buildWeatherDetail(Icons.air, '$windSpeed km/h'),
                    ],
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Forecast
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.check_circle_rounded,
                  color: AppTheme.accentYellow,
                  size: 18,
                ),
                const SizedBox(width: 10),
                Text(
                  forecast,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeatherDetail(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, size: 14, color: Colors.white60),
        const SizedBox(width: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.white70,
          ),
        ),
      ],
    );
  }
}

/// Quick Stats Row Widget
class QuickStatsRow extends StatelessWidget {
  final int activeCrops;
  final int autoDetected;
  final int manual;

  const QuickStatsRow({
    super.key,
    required this.activeCrops,
    required this.autoDetected,
    required this.manual,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).dividerColor,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(context, 'Active Crops', activeCrops.toString()),
          _buildDivider(context),
          _buildStatItem(context, 'Auto-Detected', autoDetected.toString()),
          _buildDivider(context),
          _buildStatItem(context, 'Manual', manual.toString()),
        ],
      ),
    );
  }

  Widget _buildStatItem(BuildContext context, String label, String value) {
    return Column(
      children: [
        Text(
          label.toUpperCase(),
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.3,
            color: Theme.of(context).textTheme.bodySmall?.color,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          value,
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: AppTheme.primaryGreen,
          ),
        ),
      ],
    );
  }

  Widget _buildDivider(BuildContext context) {
    return Container(
      width: 1,
      height: 40,
      color: Theme.of(context).dividerColor,
    );
  }
}
