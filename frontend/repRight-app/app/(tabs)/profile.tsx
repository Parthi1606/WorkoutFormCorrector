// app/(tabs)/profile.tsx
// Profile screen — pulls real stats from the backend via useStats hook.
// Falls back gracefully to zeros for guest users.

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  SafeAreaView, StatusBar, TouchableOpacity,
  Switch, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '@/constants/theme';
import { useAuthStore } from '@/store/authStore';
import { useStats } from '@/hooks/useStats';
import ScreenWrapper from '@/components/ui/ScreenWrapper';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';

// Tier colour by accuracy band
function scoreTier(score: number): string {
  if (score >= 85) return Colors.green;
  if (score >= 65) return Colors.yellow;
  return Colors.red;
}

export default function ProfileScreen() {
  const router  = useRouter();
  const user    = useAuthStore((s) => s.user);
  const logout  = useAuthStore((s) => s.logout);
  const [haptic, setHaptic] = useState(true);

  // Real stats from API
  const { stats, breakdown, loading, error, refresh } = useStats();

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  const displayName  = user?.name  ?? 'Guest';
  const displayEmail = user?.email ?? 'Guest Mode';
  const isGuest      = !user?.id;

  // Header stat values — fallback to 0 for guests or while loading
  const streak       = stats?.streak         ?? 0;
  const totalReps    = stats?.total_reps      ?? 0;
  const avgForm      = stats?.avg_form        ?? 0;

  return (
    <ScreenWrapper>
      <View style={styles.root}>
        <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />

        <View style={styles.header}>
          <Text style={styles.title}>Profile</Text>
          <TouchableOpacity onPress={refresh}>
            <Text style={styles.settingsIcon}>⚙</Text>
          </TouchableOpacity>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scroll}
        >
          {/* Avatar + name */}
          <View style={styles.hero}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>👤</Text>
            </View>
            <View>
              <Text style={styles.name}>{displayName}</Text>
              <Text style={styles.email}>{displayEmail}</Text>
            </View>
          </View>

          {/* Aggregate stats */}
          <View style={styles.stats}>
            <View style={[styles.statItem, styles.statAccent]}>
              <Text style={[styles.statVal, { color: Colors.orange }]}>
                {streak}
              </Text>
              <Text style={styles.statLbl}>Streak</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statVal}>{totalReps}</Text>
              <Text style={styles.statLbl}>Reps</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statVal}>{avgForm}%</Text>
              <Text style={styles.statLbl}>Form</Text>
            </View>
          </View>

          {/* Exercise breakdown */}
          <Text style={styles.secLabel}>EXERCISE BREAKDOWN</Text>

          {isGuest ? (
            <Text style={styles.guestNote}>
              Sign in to track your progress across sessions.
            </Text>
          ) : loading ? (
            <ActivityIndicator
              color={Colors.blue}
              style={{ marginVertical: 20 }}
            />
          ) : error ? (
            <TouchableOpacity onPress={refresh} style={styles.errorRow}>
              <Text style={styles.errorText}>Could not load stats. Tap to retry.</Text>
            </TouchableOpacity>
          ) : breakdown.length === 0 ? (
            <Text style={styles.guestNote}>
              Complete a session to see your breakdown here.
            </Text>
          ) : (
            breakdown.map((ex) => (
              <View key={ex.exercise_key} style={styles.exRow}>
                <View style={styles.exInfo}>
                  <Text style={styles.exName}>{ex.exercise_name}</Text>
                  <Text style={styles.exDet}>
                    {ex.total_reps} reps · {ex.total_sessions} session
                    {ex.total_sessions !== 1 ? 's' : ''}
                  </Text>
                </View>
                <Text style={[styles.exScore, { color: scoreTier(ex.avg_accuracy) }]}>
                  {ex.avg_accuracy}%
                </Text>
              </View>
            ))
          )}

          {/* Settings */}
          <Text style={styles.secLabel}>SETTINGS</Text>
          <View style={styles.settingsBlock}>
            <View style={styles.settingRow}>
              <View style={styles.settingIcon}>
                <Ionicons name="phone-portrait-outline" size={20} color="#555" />
              </View>
              <Text style={styles.settingLbl}>Haptic feedback</Text>
              <Switch
                value={haptic}
                onValueChange={setHaptic}
                trackColor={{ false: Colors.border, true: Colors.blue }}
                thumbColor="#fff"
              />
            </View>

            <TouchableOpacity style={styles.settingRow}>
              <View style={styles.settingIcon}>
                <Ionicons name="information-circle-outline" size={20} color="#555" />
              </View>
              <Text style={styles.settingLbl}>About RepRight</Text>
              <Text style={styles.settingChevron}>›</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.settingRow, styles.settingRowLast]}
              onPress={handleLogout}
            >
              <View style={[styles.settingIcon, styles.settingIconDanger]}>
                <MaterialIcons name="logout" size={20} color="#d9534f" />
              </View>
              <Text style={[styles.settingLbl, styles.settingLblDanger]}>
                Log out
              </Text>
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
    fontSize:   30,
    fontWeight: '800',
    color:      Colors.text,
  },
  settingsIcon: { fontSize: 20, color: Colors.text2 },
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
  },
  avatarText: { fontSize: 26 },
  name:  { fontFamily: Font.display, fontSize: 21, fontWeight: '800', color: Colors.text },
  email: { fontSize: 12, color: Colors.text2, marginTop: 3, fontFamily: Font.bodyMd },
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
    marginTop:  1,
    fontFamily: Font.bodyMd,
  },
  exScore: {
    fontFamily: Font.display,
    fontSize:   15,
    fontWeight: '800',
  },
  guestNote: {
    paddingHorizontal: 22,
    paddingVertical:   12,
    fontSize:          13,
    color:             Colors.text3,
    fontFamily:        Font.bodyMd,
    lineHeight:        20,
  },
  errorRow: {
    paddingHorizontal: 22,
    paddingVertical:   12,
  },
  errorText: {
    fontSize:   13,
    color:      Colors.red,
    fontFamily: Font.bodyMd,
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
    flexDirection:     'row',
    alignItems:        'center',
    gap:               12,
    paddingVertical:   12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  settingRowLast:     { borderBottomWidth: 0 },
  settingIcon: {
    width:           34,
    height:          34,
    backgroundColor: Colors.bg2,
    borderRadius:    9,
    borderWidth:     1,
    borderColor:     Colors.border,
    alignItems:      'center',
    justifyContent:  'center',
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
