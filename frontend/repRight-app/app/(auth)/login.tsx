// app/(auth)/login.tsx
// After Google Sign-In succeeds, exchanges the Google ID token for a
// RepRight JWT via POST /auth/google, then stores both user info and token.

import React from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  StatusBar, TouchableOpacity, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import {
  GoogleSignin,
  statusCodes,
  isSuccessResponse,
  isErrorWithCode,
} from '@react-native-google-signin/google-signin';
import Constants from 'expo-constants';
import { Colors, Font } from '@/constants/theme';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/store/authStore';
import { loginWithGoogle } from '@/services/api';

GoogleSignin.configure({
  webClientId: Constants.expoConfig?.extra?.googleClientId,
});
console.log('Client ID:', Constants.expoConfig?.extra?.googleClientId);

export default function LoginScreen() {
  const router     = useRouter();
  const setUser    = useAuthStore((s) => s.setUser);
  const setLoading = useAuthStore((s) => s.setLoading);
  const isLoading  = useAuthStore((s) => s.isLoading);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      await GoogleSignin.hasPlayServices();
      const response = await GoogleSignin.signIn();

      if (isSuccessResponse(response)) {
        const { idToken } = response.data;

        if (!idToken) {
          Alert.alert('Error', 'No ID token returned from Google.');
          return;
        }

        // Exchange Google ID token for RepRight JWT
        const auth = await loginWithGoogle(idToken);

        // Store user + backend JWT in auth store
        setUser(
          {
            id:        String(auth.user_id),
            name:      auth.name,
            email:     auth.email,
            avatarUrl: null,
          },
          auth.token,   // RepRight JWT — used for all subsequent API calls
        );

        router.replace('/(tabs)');
      }
    } catch (error) {
      if (isErrorWithCode(error)) {
        if (error.code === statusCodes.SIGN_IN_CANCELLED) {
          // user cancelled — do nothing
        } else if (error.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
          Alert.alert('Error', 'Google Play Services not available.');
        } else {
          Alert.alert('Sign-in failed', 'Please try again.');
        }
      } else if (error instanceof Error) {
        // Backend call failed
        Alert.alert('Sign-in failed', error.message);
      } else {
        Alert.alert('Error', 'Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />
      <View style={styles.hero}>
        <Text style={styles.wordmark}>
          Rep<Text style={styles.accent}>Right</Text>
        </Text>
        <Text style={styles.headline}>Welcome back.</Text>
        <Text style={styles.sub}>
          Sign in to pick up where you left off and track your progress.
        </Text>
      </View>
      <View style={styles.ctas}>
        <Button
          label="Continue with Google"
          onPress={handleGoogleSignIn}
          variant="secondary"
          loading={isLoading}
          icon={<Text style={styles.googleIcon}>G</Text>}
        />
        <View style={styles.divider}>
          <View style={styles.divLine} />
          <Text style={styles.divText}>or</Text>
          <View style={styles.divLine} />
        </View>
        <Button
          label="Use Guest Mode"
          onPress={() => router.replace('/(tabs)')}
          variant="outline"
        />
        <Text style={styles.note}>
          Guest Mode does not save progress. Sign in for full features.
        </Text>
      </View>
      <TouchableOpacity style={styles.back} onPress={() => router.back()}>
        <Text style={styles.backText}>← Back</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:       { flex: 1, backgroundColor: Colors.bg },
  hero:       { paddingHorizontal: 28, paddingTop: 40, paddingBottom: 24, gap: 6 },
  wordmark:   { fontFamily: Font.display, fontSize: 30, fontWeight: '800', letterSpacing: -0.6, color: Colors.text },
  accent:     { color: Colors.orange },
  headline:   { fontFamily: Font.display, fontSize: 21, fontWeight: '700', color: Colors.text, marginTop: 14, lineHeight: 26 },
  sub:        { fontSize: 13, color: Colors.text2, marginTop: 5, lineHeight: 20, fontFamily: Font.bodyMd },
  ctas:       { paddingHorizontal: 28, gap: 10, marginTop: 8 },
  googleIcon: { fontSize: 15, fontWeight: '700', color: Colors.blueDk, fontFamily: Font.display },
  divider:    { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 4 },
  divLine:    { flex: 1, height: 1, backgroundColor: Colors.border },
  divText:    { fontSize: 11, color: Colors.text3, fontFamily: Font.body },
  note:       { textAlign: 'center', fontSize: 11, color: Colors.text3, fontFamily: Font.body, lineHeight: 16 },
  back:       { padding: 20, alignSelf: 'center' },
  backText:   { fontSize: 13, color: Colors.text2, fontFamily: Font.bodyMd },
});




//Aaliyas devide SHA1 key 5E:8F:16:06:2E:A3:CD:2C:4A:0D:54:78:76:BA:A6:F3:8C:AB:F6:25
//Parthis device SHA1 key B6:5E:E5:C5:EE:DC:C6:8F:BE:44:64:95:DA:3E:13:D6:98:28:3C:C5