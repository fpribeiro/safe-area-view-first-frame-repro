import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import {
  SafeAreaProvider,
  SafeAreaView,
  useSafeAreaInsets,
} from 'react-native-safe-area-context';

type Screen = 'home' | 'safe-area-view' | 'hook';

export default function App() {
  const [screen, setScreen] = useState<Screen>('home');
  const back = () => setScreen('home');
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      {screen === 'home' ? (
        <Home open={setScreen} />
      ) : screen === 'safe-area-view' ? (
        <SafeAreaViewPage back={back} />
      ) : (
        <HookPage back={back} />
      )}
    </SafeAreaProvider>
  );
}

// Each button fills half the screen, so a script can tap it at a quarter
// and three quarters of the screen's height.
function Home({ open }: { open: (screen: Screen) => void }) {
  return (
    <View style={styles.fill}>
      <Pressable style={[styles.fill, styles.center, styles.top]} onPress={() => open('safe-area-view')}>
        <Text style={styles.label}>Open the SafeAreaView page</Text>
      </Pressable>
      <Pressable style={[styles.fill, styles.center, styles.bottom]} onPress={() => open('hook')}>
        <Text style={styles.label}>Open the useSafeAreaInsets page</Text>
      </Pressable>
    </View>
  );
}

// The red bar marks the page's top edge and the blue bar its bottom edge:
// laid out with the insets, the red bar starts below the status bar and the
// blue bar ends above the navigation bar.
function PageBody({ back, name }: { back: () => void; name: string }) {
  return (
    <>
      <View style={styles.red} />
      <Pressable style={[styles.fill, styles.center]} onPress={back}>
        <Text style={styles.label}>{name}</Text>
        <Text style={styles.hint}>Tap to go back</Text>
      </Pressable>
      <View style={styles.blue} />
    </>
  );
}

function SafeAreaViewPage({ back }: { back: () => void }) {
  return (
    <SafeAreaView style={styles.page} edges={['top', 'bottom']}>
      <PageBody back={back} name="SafeAreaView page" />
    </SafeAreaView>
  );
}

function HookPage({ back }: { back: () => void }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.page, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      <PageBody back={back} name="useSafeAreaInsets page" />
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  center: { alignItems: 'center', justifyContent: 'center' },
  top: { backgroundColor: '#dddddd' },
  bottom: { backgroundColor: '#bbbbbb' },
  page: { flex: 1, backgroundColor: '#ffffff' },
  red: { height: 48, backgroundColor: '#ff0000' },
  blue: { height: 48, backgroundColor: '#0000ff' },
  label: { fontSize: 20, color: '#000000' },
  hint: { fontSize: 14, color: '#555555', marginTop: 8 },
});
