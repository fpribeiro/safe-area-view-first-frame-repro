# safe-area-view-first-frame-repro

Minimal reproduction for react-native-safe-area-context on Android: a
`SafeAreaView` that mounts draws its first frame with no insets, its content
under the status bar and the navigation bar, and moves into place on the next
frame. A `View` padded from `useSafeAreaInsets()` draws its first frame in
place.

There is no navigation library. This is a blank TypeScript project from
`create-expo-app` (Expo SDK 58) plus `react-native-safe-area-context`, installed
with `npx expo install`. `App.tsx` is the whole app: a `SafeAreaProvider` around
a home screen whose two halves are buttons, each of which swaps in a full-screen
page through state.

- The **SafeAreaView page** is `<SafeAreaView edges={['top', 'bottom']}>`.
- The **useSafeAreaInsets page** is a `View` with `paddingTop: insets.top` and
  `paddingBottom: insets.bottom`.

Both pages carry a red bar at their top edge and a blue bar at their bottom
edge. Tapping a page's middle goes back.

## Run

    npm install
    npx expo prebuild --platform android
    cd android && ./gradlew assembleRelease
    adb install app/build/outputs/apk/release/app-release.apk

A release build is what was run.

## Reproduce

By eye the wrong frame is one frame long, so record it. With the app on its home
screen:

    python3 scripts/measure.py safe-area-view
    python3 scripts/measure.py hook

Each command opens its page eight times while `adb shell screenrecord` runs. It
reads a two-pixel column of every recorded frame with ffmpeg, and reports any
frame where the red bar's top or the blue bar's bottom is not where it settles.
It needs adb, ffmpeg, ffprobe and Python 3 (standard library only). With several
devices attached, set `ANDROID_SERIAL`.

To look at the frames yourself, run `adb shell screenrecord /sdcard/r.mp4`, tap
**Open the SafeAreaView page**, stop the recording, pull the file, and split it
with `ffmpeg -i r.mp4 -fps_mode passthrough frames/%04d.png`.

## Results

| Device | SafeAreaView page | useSafeAreaInsets page |
|---|---|---|
| Pixel 7 AVD, Android 15, 1080x2400 | 8 of 8 openings: first frame with the red bar's top at 0 and the blue bar under the navigation bar; settled at 136 and 2273 | 0 of 8 |
| Pixel 9 AVD, Android 17, 1080x2424 | 8 of 8 openings: first frame with the red bar's top at 0 and the blue bar's bottom at 2423; settled at 142 and 2360 | 0 of 8 |

## What is going on

This is read from the 5.11.1 Android source and was not traced.
`SafeAreaView.kt` computes its insets once it is laid out, both on attach and in
an `OnPreDrawListener`. When they change it pushes them through
`stateWrapper.updateState`, calls `requestLayout()`, and returns `false` from
`onPreDraw()`, which cancels that one draw. With the New Architecture the
padding arrives with a later commit. At the next pre-draw nothing has changed
from the view's side, so the draw goes ahead with the layout still unpadded.
`useSafeAreaInsets()` reads the insets the provider has already measured, during
render, so the first layout already has them.

## Seen on

expo 58.0.24, react-native 0.88.1 with the New Architecture, react 19.3.0,
react-native-safe-area-context 5.11.1, release build, on Android emulators (the
Pixel 7 AVD with API 35 and the Pixel 9 AVD with API 37). It was first seen in
an app on react-native-safe-area-context 5.10.1 and react-native 0.88.0, on
screens pushed with expo-router's native stack.

## Related

react-native-safe-area-context #364, #226 and #586;
react-navigation/react-navigation#12445.
