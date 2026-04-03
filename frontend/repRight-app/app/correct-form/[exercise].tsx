// app/correct-form/[exercise].tsx
// Pre-session briefing screen. Shows form tips for the selected exercise.
// Navigates to /session/[exercise] on "Start Session".

import React from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  SafeAreaView, StatusBar, TouchableOpacity,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '../../constants/theme';
import { Button } from '../../components/ui/Button';
import { EXERCISES, ExerciseKey } from '../../constants/exercises';
import ScreenWrapper from '@/components/ui/ScreenWrapper';

export default function CorrectFormScreen() {
  const router = useRouter();
  const { exercise, planId } = useLocalSearchParams<{
      exercise: ExerciseKey;
      planId?: string;
    }>();
  //const { exercise } = useLocalSearchParams<{ exercise: ExerciseKey }>();
  const ex = exercise ? EXERCISES[exercise] : null;

  if (!ex) {
    return (
      <SafeAreaView style={styles.root}>
        <Text style={{ padding: 24, color: Colors.text }}>Exercise not found.</Text>
      </SafeAreaView>
    );
  }

  return (
    <ScreenWrapper>
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Text style={styles.backArrow}>‹</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Before you start</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Exercise banner */}
        <View style={styles.banner}>
          <View>
            <Text style={styles.bannerName}>{ex.name}</Text>
            <Text style={styles.bannerSub}>{ex.category} · {ex.isHold ? 'Hold' : 'Rep-based'}</Text>
          </View>
        </View>

        {/* Form tips */}
        <Text style={styles.tipsTitle}>KEY FORM POINTS</Text>
        {ex.formTips.map((tip, i) => (
          <View key={i} style={styles.tipRow}>
            <View style={styles.tipNum}>
              <Text style={styles.tipNumText}>{i + 1}</Text>
            </View>
            <Text style={styles.tipText}>{tip}</Text>
          </View>
        ))}

        {/* Camera positioning hint */}
        <View style={styles.hint}>
          <Text style={styles.hintText}>{ex.cameraHint}</Text>
        </View>

        {/* CTA */}
        <View style={styles.cta}>
          <Button
            label="Start Session"
            onPress={() => {
              if (planId) {
                router.push(`/session/workout/${planId}`);
              } else {
                router.push(`/session/${ex.key}`);
              }
            }}
            variant="primary"
          />
        </View>

      </ScrollView>
    </View>
  </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: Colors.bg },
  scroll: { paddingBottom: 40 },

  header: {
    flexDirection:     'row',
    alignItems:        'center',
    justifyContent:    'space-between',
    paddingHorizontal: 22,
    paddingVertical:   18,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backBtn: {
    width:           36,
    height:          36,
    backgroundColor: Colors.surface,
    borderRadius:    Radius.xs,
    borderWidth:     1,
    borderColor:     Colors.border,
    alignItems:      'center',
    justifyContent:  'center',
    ...Shadow.sm,
  },
  backArrow: {
    fontSize:   20,
    color:      Colors.text,
    lineHeight: 22,
    fontFamily: Font.display,
  },
  headerTitle: {
    fontFamily: Font.display,
    fontSize:   17,
    fontWeight: '700',
    color:      Colors.text,
  },

  banner: {
    flexDirection:   'row',
    alignItems:      'center',
    gap:             14,
    margin:          18,
    backgroundColor: Colors.orangeLt,
    borderWidth:     1,
    borderColor:     Colors.orangeMid,
    borderRadius:    Radius.md,
    padding:         18,
  },
  bannerEmoji: { fontSize: 38, lineHeight: 44 },
  bannerName: {
    fontFamily: Font.display,
    fontSize:   20,
    fontWeight: '800',
    color:      Colors.orange,
  },
  bannerSub: {
    fontSize:   12,
    color:      Colors.text2,
    marginTop:   3,
    fontFamily: Font.bodyMd,
  },

  tipsTitle: {
    fontFamily:        Font.bodySm,
    fontSize:          12,
    fontWeight:        '700',
    color:             Colors.text2,
    letterSpacing:     0.7,
    paddingHorizontal: 22,
    paddingBottom:     8,
    paddingTop:        4,
  },
  tipRow: {
    flexDirection:     'row',
    alignItems:        'flex-start',
    gap:               12,
    paddingHorizontal: 22,
    paddingVertical:    7,
  },
  tipNum: {
    width:           24,
    height:          24,
    backgroundColor: Colors.blue,
    borderRadius:    6,
    alignItems:      'center',
    justifyContent:  'center',
    flexShrink:      0,
    marginTop:       1,
  },
  tipNumText: {
    fontSize:   11,
    fontWeight: '800',
    color:      '#fff',
    fontFamily: Font.display,
  },
  tipText: {
    flex:       1,
    fontSize:   13,
    color:      Colors.text2,
    lineHeight: 20,
    fontFamily: Font.bodyMd,
  },

  hint: {
    flexDirection:     'row',
    alignItems:        'flex-start',
    gap:               8,
    margin:            22,
    marginTop:         12,
    backgroundColor:   Colors.blueLt,
    borderWidth:       1,
    borderColor:       Colors.blueMid,
    borderRadius:      Radius.sm,
    padding:           12,
  },
  hintIcon: { fontSize: 15, flexShrink: 0 },
  hintText: {
    flex:       1,
    fontSize:   12,
    color:      Colors.blueDk,
    lineHeight: 18,
    fontFamily: Font.bodyMd,
  },

  cta: {
    paddingHorizontal: 22,
    marginTop:         4,
  },
});
