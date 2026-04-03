// app/(tabs)/profile.tsx  — Profile screen
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  SafeAreaView, StatusBar, TouchableOpacity, Switch,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '@/constants/theme';
import { useAuthStore } from '@/store/authStore';
import ScreenWrapper from '@/components/ui/ScreenWrapper';

// Mock exercise breakdown — replace with real data from your API
const EXERCISE_STATS = [
  { emoji: '🏋️', name: 'Bicep Curl',  detail: '48 reps · 12 sessions', score: 92, tier: 'hi'  },
  { emoji: '🦵', name: 'Squat',        detail: '60 reps · 8 sessions',  score: 78, tier: 'mid' },
  { emoji: '🧘', name: 'Plank',        detail: '4m 20s total',          score: 95, tier: 'hi'  },
];

const SCORE_COLORS: Record<string, string> = {
  hi:  Colors.green,
  mid: Colors.yellow,
  lo:  Colors.red,
};

export default function ProfileScreen() {
  const router  = useRouter();
  const user    = useAuthStore((s) => s.user);
  const logout  = useAuthStore((s) => s.logout);

  const [haptic, setHaptic] = useState(true);

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  const displayName  = user?.name  ?? 'Guest';
  const displayEmail = user?.email ?? 'Training Mode';

  return (
    <ScreenWrapper>
      <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />

      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
        <TouchableOpacity>
          <Text style={styles.settingsIcon}>⚙</Text>
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Avatar + name */}
        <View style={styles.hero}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.avatarUrl ? '🖼' : '👤'}
            </Text>
          </View>
          <View>
            <Text style={styles.name}>{displayName}</Text>
            <Text style={styles.email}>{displayEmail}</Text>
            {user && (
              <TouchableOpacity>
                <Text style={styles.editLink}>Edit profile →</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* Stats */}
        <View style={styles.stats}>
          <View style={[styles.statItem, styles.statAccent]}>
            <Text style={[styles.statVal, { color: Colors.orange }]}>6</Text>
            <Text style={styles.statLbl}>Streak</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statVal}>142</Text>
            <Text style={styles.statLbl}>Reps</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statVal}>87%</Text>
            <Text style={styles.statLbl}>Form</Text>
          </View>
        </View>

        {/* Exercise breakdown */}
        <Text style={styles.secLabel}>EXERCISE BREAKDOWN</Text>
        {EXERCISE_STATS.map((ex) => (
          <View key={ex.name} style={styles.exRow}>
            <Text style={styles.exEmoji}>{ex.emoji}</Text>
            <View style={styles.exInfo}>
              <Text style={styles.exName}>{ex.name}</Text>
              <Text style={styles.exDet}>{ex.detail}</Text>
            </View>
            <Text style={[styles.exScore, { color: SCORE_COLORS[ex.tier] }]}>
              {ex.score}%
            </Text>
          </View>
        ))}

        {/* Settings */}
        <Text style={styles.secLabel}>SETTINGS</Text>
        <View style={styles.settingsBlock}>

          {/* Haptic toggle */}
          <View style={styles.settingRow}>
            <View style={styles.settingIcon}>
              <Text>📳</Text>
            </View>
            <Text style={styles.settingLbl}>Haptic feedback</Text>
            <Switch
              value={haptic}
              onValueChange={setHaptic}
              trackColor={{ false: Colors.border, true: Colors.blue }}
              thumbColor="#fff"
            />
          </View>

          {/* About */}
          <TouchableOpacity style={styles.settingRow}>
            <View style={styles.settingIcon}><Text>ℹ️</Text></View>
            <Text style={styles.settingLbl}>About RepRight</Text>
            <Text style={styles.settingChevron}>›</Text>
          </TouchableOpacity>

          {/* Log out */}
          <TouchableOpacity style={[styles.settingRow, styles.settingRowLast]} onPress={handleLogout}>
            <View style={[styles.settingIcon, styles.settingIconDanger]}><Text>🚪</Text></View>
            <Text style={[styles.settingLbl, styles.settingLblDanger]}>Log out</Text>
            <Text style={styles.settingChevron}>›</Text>
          </TouchableOpacity>

        </View>

      </ScrollView>
    </View>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1 },
  scroll: { paddingBottom: 32 },

  header: {
    flexDirection:     'row',
    alignItems:        'center',
    justifyContent:    'space-between',
    paddingHorizontal: 22,
    paddingVertical:   18,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontFamily: Font.display,
    fontSize:  30,
    fontWeight: '800',
    color:      Colors.text,
  },
  settingsIcon: {
    fontSize: 20,
    color:    Colors.text2,
  },

  hero: {
    flexDirection:     'row',
    alignItems:        'center',
    gap:               16,
    paddingHorizontal: 22,
    paddingVertical:   24,
  },
  avatar: {
    width:           68,
    height:          68,
    borderRadius:    34,
    backgroundColor: Colors.blueLt,
    borderWidth:     2.5,
    borderColor:     Colors.blue,
    alignItems:      'center',
    justifyContent:  'center',
    flexShrink:      0,
  },
  avatarText: { fontSize: 26 },
  name: {
    fontFamily: Font.display,
    fontSize:   21,
    fontWeight: '800',
    color:      Colors.text,
  },
  email: {
    fontSize:   12,
    color:      Colors.text2,
    marginTop:   3,
    fontFamily: Font.bodyMd,
  },
  editLink: {
    fontSize:   12,
    color:      Colors.blue,
    fontWeight: '700',
    marginTop:   6,
    fontFamily: Font.bodySm,
  },

  stats: {
    flexDirection:     'row',
    gap:               10,
    paddingHorizontal: 22,
  },
  statItem: {
    flex:            1,
    backgroundColor: Colors.surface,
    borderWidth:     1,
    borderColor:     Colors.border,
    borderRadius:    Radius.sm,
    padding:         13,
    alignItems:      'center',
    ...Shadow.sm,
  },
  statAccent: {},
  statVal: {
    fontFamily: Font.display,
    fontSize:   24,
    fontWeight: '800',
    color:      Colors.blueDk,
  },
  statLbl: {
    fontSize:      10,
    color:         Colors.text3,
    marginTop:     2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontFamily:    Font.bodySm,
  },

  secLabel: {
    fontFamily:        Font.bodySm,
    fontSize:          12,
    fontWeight:        '700',
    color:             Colors.text2,
    letterSpacing:     0.7,
    paddingHorizontal: 22,
    paddingTop:        16,
    paddingBottom:     6,
    textTransform:     'uppercase',
  },

  exRow: {
    flexDirection:     'row',
    alignItems:        'center',
    paddingHorizontal: 22,
    paddingVertical:   11,
    gap:               12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  exEmoji: { fontSize: 18, width: 28, textAlign: 'center' },
  exInfo:  { flex: 1 },
  exName: {
    fontSize:   13,
    fontWeight: '700',
    fontFamily: Font.display,
    color:      Colors.text,
  },
  exDet: {
    fontSize:   11,
    color:      Colors.text2,
    marginTop:   1,
    fontFamily: Font.bodyMd,
  },
  exScore: {
    fontFamily: Font.display,
    fontSize:   15,
    fontWeight: '800',
  },

  settingsBlock: {
    marginHorizontal: 22,
    backgroundColor:  Colors.surface,
    borderRadius:     Radius.sm,
    borderWidth:      1,
    borderColor:      Colors.border,
    overflow:         'hidden',
    ...Shadow.sm,
  },
  settingRow: {
    flexDirection:  'row',
    alignItems:     'center',
    gap:            12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  settingRowLast: { borderBottomWidth: 0 },
  settingIcon: {
    width:           34,
    height:          34,
    backgroundColor: Colors.bg2,
    borderRadius:    9,
    borderWidth:     1,
    borderColor:     Colors.border,
    alignItems:      'center',
    justifyContent:  'center',
    fontSize:        15,
    flexShrink:      0,
  },
  settingIconDanger: {
    backgroundColor: Colors.redLt,
    borderColor:     'rgba(239,68,68,0.2)',
  },
  settingLbl: {
    flex:       1,
    fontSize:   14,
    fontWeight: '600',
    color:      Colors.text,
    fontFamily: Font.bodySm,
  },
  settingLblDanger: { color: Colors.red },
  settingChevron: {
    fontSize:   13,
    color:      Colors.text3,
    fontWeight: '600',
  },
});
