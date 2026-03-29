import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import * as AuthSession from 'expo-auth-session';
import { useEffect } from 'react';
import { useRouter } from 'expo-router';

WebBrowser.maybeCompleteAuthSession();

export default function Login() {
  const router = useRouter();

  const redirectUri = "https://auth.expo.io/@aaliyadesousa/repRight-app";
  console.log("REDIRECT URI:", redirectUri);

  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: '597817830458-07ognj6gmmljt7a2v62akc4j7bqiqjas.apps.googleusercontent.com',
    redirectUri,
  });

  useEffect(() => {
    if (response?.type === 'success') {
      console.log("FULL RESPONSE:", response);
      const idToken = response.authentication?.idToken;

      console.log("ID TOKEN:", idToken);

      router.replace('/(tabs)');
    }
  }, [response]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Train Smart</Text>
      <Text style={styles.subtitle}>Move Better</Text>

      <TouchableOpacity
        style={styles.button}
        onPress={() => promptAsync()}
        disabled={!request}
      >
        <Text style={styles.buttonText}>Continue with Google</Text>
      </TouchableOpacity>
    </View>
  );
}
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 36,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 16,
    color: '#888',
    marginBottom: 50,
  },
  button: {
    backgroundColor: '#000',
    paddingVertical: 16,
    paddingHorizontal: 40,
    borderRadius: 25,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
});