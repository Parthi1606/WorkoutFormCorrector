import { SafeAreaView, StyleSheet } from 'react-native';
import { Colors } from '@/constants/theme';

export default function ScreenWrapper({ children }) {
  return (
    <SafeAreaView style={styles.container}>
      {children}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg,   
    paddingHorizontal: 4,
    paddingTop: 50,
    paddingBottom: 0,
  },
});