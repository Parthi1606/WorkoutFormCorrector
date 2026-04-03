// app/index.tsx  — Splash screen
import React from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '@/constants/theme';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';

export default function SplashScreen() {
  const router = useRouter();
  const user   = useAuthStore((s) => s.user);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />

      {/* Top — logo */}
      <View style={styles.top}>
        <View style={styles.ring}>
          <View style={styles.ringInner}>
            <Text style={styles.ringEmoji}>🏃</Text>
          </View>
        </View>
        <Text style={styles.wordmark}>
          Rep<Text style={styles.accent}>Right</Text>
        </Text>
        <Text style={styles.tagline}>TRAIN SMART · MOVE BETTER</Text>
      </View>

      {/* Bottom — CTAs */}
      <View style={styles.bottom}>
        {user ? (
          <>
            <Button
              label={`Continue as ${user.name.split(' ')[0]}`}
              onPress={() => router.replace('/')}
              variant="primary"
            />
            <View style={styles.divider}>
              <View style={styles.divLine} />
              <Text style={styles.divText}>or</Text>
              <View style={styles.divLine} />
            </View>
          </>
        ) : null}

        <Button
          label="Log in / Sign up"
          onPress={() => router.push('/(auth)/login')}
          variant="outline"
        />

        {user && (
          <Text style={styles.note}>
            Signed in as {user.email}
          </Text>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex:            1,
    backgroundColor: Colors.bg,
    justifyContent:  'space-between',
    alignItems:      'center',
  },
  top: {
    flex:           1,
    alignItems:     'center',
    justifyContent: 'center',
    gap:            10,
  },
  ring: {
    width:        80,
    height:       80,
    borderRadius: 40,
    borderWidth:  3,
    borderColor:  Colors.orangeLt,
    alignItems:   'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  ringInner: {
    width:           56,
    height:          56,
    borderRadius:    28,
    backgroundColor: Colors.orangeLt,
    alignItems:      'center',
    justifyContent:  'center',
  },
  ringEmoji: { fontSize: 26 },
  wordmark: {
    fontFamily: Font.display,
    fontSize:   52,
    fontWeight: '800',
    letterSpacing: -1.5,
    color:      Colors.text,
    lineHeight: 56,
  },
  accent:  { color: Colors.orange },
  tagline: {
    fontSize:      12,
    color:         Colors.text2,
    letterSpacing: 1.8,
    fontFamily:    Font.bodySm,
  },

  bottom: {
    width:           '100%',
    paddingHorizontal: 28,
    paddingBottom:   48,
    gap:             10,
  },
  divider: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           10,
    paddingVertical: 2,
  },
  divLine: {
    flex:   1,
    height: 1,
    backgroundColor: Colors.border,
  },
  divText: {
    fontSize:   12,
    color:      Colors.text3,
    fontFamily: Font.body,
  },
  note: {
    textAlign:  'center',
    fontSize:   11,
    color:      Colors.text3,
    fontFamily: Font.body,
    marginTop:  2,
  },
});
