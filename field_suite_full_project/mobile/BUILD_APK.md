# Field Suite Mobile - APK Build Guide

## Professional Agricultural Application
Inspired by John Deere Operations Center and leading agricultural platforms.

## Prerequisites

1. **Flutter SDK** (3.10.0 or higher)
   ```bash
   flutter --version
   ```

2. **Android SDK** with:
   - Android SDK Build-Tools 33.0.0+
   - Android SDK Platform 33
   - Android SDK Command-line Tools

3. **Java Development Kit (JDK)** 11 or 17

## Build Commands

### Debug APK (for testing)
```bash
cd field_suite_full_project/mobile
flutter pub get
flutter build apk --debug
```
Output: `build/app/outputs/flutter-apk/app-debug.apk`

### Release APK (for distribution)
```bash
cd field_suite_full_project/mobile
flutter pub get
flutter build apk --release
```
Output: `build/app/outputs/flutter-apk/app-release.apk`

### Split APKs (smaller size per architecture)
```bash
flutter build apk --split-per-abi --release
```
Outputs:
- `app-armeabi-v7a-release.apk` (32-bit ARM)
- `app-arm64-v8a-release.apk` (64-bit ARM)
- `app-x86_64-release.apk` (x86_64 emulators)

### App Bundle (for Play Store)
```bash
flutter build appbundle --release
```
Output: `build/app/outputs/bundle/release/app-release.aab`

## Configuration

### 1. Update App Version
Edit `pubspec.yaml`:
```yaml
version: 2.0.0+1  # format: major.minor.patch+buildNumber
```

### 2. Configure Signing (for release)
Create `android/key.properties`:
```properties
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=YOUR_KEY_ALIAS
storeFile=/path/to/your/keystore.jks
```

Then update `android/app/build.gradle` to use this keystore.

### 3. App Icon
Place your app icon in:
- `android/app/src/main/res/mipmap-hdpi/` (72x72)
- `android/app/src/main/res/mipmap-mdpi/` (48x48)
- `android/app/src/main/res/mipmap-xhdpi/` (96x96)
- `android/app/src/main/res/mipmap-xxhdpi/` (144x144)
- `android/app/src/main/res/mipmap-xxxhdpi/` (192x192)

## Features Included

- **John Deere-inspired design** with green (#367C2B) and yellow (#FFDE00) color scheme
- **Dark mode support** for field use in low-light conditions
- **Professional agricultural UI** inspired by leading platforms
- **MapLibre GL integration** for offline-capable mapping
- **AG-UI protocol support** for AI-assisted field management

## APK Size Optimization

The release build includes:
- ProGuard/R8 code shrinking
- Resource shrinking
- ABI splits for smaller per-device APKs

Typical sizes:
- Debug APK: ~80-100 MB
- Release APK (universal): ~40-60 MB
- Release APK (single ABI): ~25-35 MB

## Troubleshooting

### Build fails with "SDK not found"
```bash
flutter doctor
flutter doctor --android-licenses
```

### Gradle sync issues
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
```

### MapLibre not loading
Ensure `android:usesCleartextTraffic="true"` is in AndroidManifest.xml for local development.

## Quick Build Script

```bash
#!/bin/bash
# build_apk.sh

echo "Building Field Suite APK..."
cd "$(dirname "$0")"

# Clean previous builds
flutter clean

# Get dependencies
flutter pub get

# Build release APK
flutter build apk --release

# Show output
echo ""
echo "Build complete!"
echo "APK location: build/app/outputs/flutter-apk/app-release.apk"
ls -lh build/app/outputs/flutter-apk/*.apk 2>/dev/null
```

## Support

For issues, visit: https://github.com/kafaat/sahool-project
