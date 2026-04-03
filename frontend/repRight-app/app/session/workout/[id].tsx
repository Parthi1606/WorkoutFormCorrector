// app/session/workout/[id].tsx
// Workout session screen — runs exercises in sequence from a WorkoutPlan.
// Uses the same WebSocket + session infrastructure as the solo session.

import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Dimensions, StatusBar,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Colors, Font } from '@/constants/theme';
import { WORKOUT_PLANS, EXERCISES, ExerciseKey } from '@/constants/exercises';
import {
  RepBubble, HoldBubble, ErrorOverlay, WorkoutStrip, WsDot,
} from '@/components/session/SessionOverlays';
import { useSessionStore } from '@/store/sessionStore';
import { useWebSocket } from '@/hooks/useWebSocket';

const { height: SCREEN_H } = Dimensions.get('window');

export default function WorkoutSessionScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const plan   = WORKOUT_PLANS.find((p) => p.id === id);

  // Current position in the exercise queue
  const [exIdx,   setExIdx]   = useState(0);
  const [setNum,  setSetNum]  = useState(1);

  const currentItem = plan?.exercises[exIdx];
  const currentEx   = currentItem ? EXERCISES[currentItem.key] : null;

  // Session state
  const phase       = useSessionStore((s) => s.phase);
  const repCount    = useSessionStore((s) => s.rep_count);
  const validReps   = useSessionStore((s) => s.valid_reps);
  const checks      = useSessionStore((s) => s.checks);
  const holdSeconds = useSessionStore((s) => s.hold_seconds);
  const isConnected = useSessionStore((s) => s.isConnected);
  const startSession  = useSessionStore((s) => s.startSession);
  const resetSession  = useSessionStore((s) => s.resetSession);

  // WebSocket — reconnects whenever exercise changes
  useWebSocket(currentItem?.key ?? null);

  const [permission, requestPermission] = useCameraPermissions();

  useEffect(() => {
    if (currentItem) startSession(currentItem.key);
    return () => { if (!currentItem) resetSession(); };
  }, [exIdx]);

  // Form score approximation (% of passing checks)
  const formPct = checks.length > 0
    ? Math.round((checks.filter((c) => c.ok).length / checks.length) * 100)
    : 0;

  const setLabel = currentItem
    ? `Set ${setNum} / ${currentItem.sets}`
    : '';

  const phaseLabel = (() => {
    switch (phase) {
      case 'idle':     return '● Ready';
      case 'moving':   return '● Moving ↓';
      case 'top':      return '● Top ↑';
      case 'lowering': return '● Lowering ↓';
      case 'hold':     return '● Hold';
      default:         return '● Idle';
    }
  })();

  // ── Advance to next set / exercise ───────────────────────────────────────
  const advanceSet = () => {
    if (!plan || !currentItem) return;

    if (setNum < currentItem.sets) {
      setSetNum((n) => n + 1);
      startSession(currentItem.key);
    } else if (exIdx < plan.exercises.length - 1) {
      setExIdx((i) => i + 1);
      setSetNum(1);
    } else {
      // Workout complete
      router.replace('/(tabs)/workout');
    }
  };

  if (!plan || !currentEx || !currentItem) {
    return (
      <View style={styles.root}>
        <Text style={{ color: '#fff', padding: 24 }}>Workout not found.</Text>
      </View>
    );
  }

  if (!permission?.granted) {
    return (
      <View style={[styles.root, { justifyContent: 'center', alignItems: 'center', gap: 16 }]}>
        <Text style={styles.permText}>Camera access is needed for form detection.</Text>
        <TouchableOpacity style={styles.permBtn} onPress={requestPermission}>
          <Text style={styles.permBtnText}>Grant Access</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.camBg} />

      {/* Camera area — 80% height */}
      <View style={styles.camArea}>
        <CameraView style={StyleSheet.absoluteFill} facing="front" />

        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Text style={styles.backArrow}>‹</Text>
          </TouchableOpacity>
          <View style={styles.titleBlock}>
            <Text style={styles.camTitle}>
              {plan.name} · {currentEx.name}
            </Text>
            <Text style={styles.camPhase}>{phaseLabel}</Text>
          </View>
          <WsDot connected={isConnected} />
        </View>

        {/* Rep / hold counter */}
        {currentEx.isHold
          ? <HoldBubble seconds={holdSeconds ?? 0} />
          : (
            <RepBubble
              repCount={repCount}
              validReps={validReps}
              phase={phase}
              targetReps={currentItem.reps}
              setLabel={setLabel}
            />
          )
        }

        {/* Error pills */}
        <ErrorOverlay checks={checks} />
      </View>

      {/* Workout bottom strip */}
      <WorkoutStrip
        exerciseName={currentEx.name}
        setLabel={setLabel}
        repCount={repCount}
        targetReps={currentItem.reps}
        formPct={formPct}
        onSkip={advanceSet}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex:            1,
    backgroundColor: Colors.camBg,
  },
  camArea: {
    height:          SCREEN_H * 0.80,
    backgroundColor: Colors.camSurface,
    overflow:        'hidden',
    position:        'relative',
  },
  topBar: {
    position:       'absolute',
    top:            0,
    left:           0,
    right:          0,
    paddingHorizontal: 16,
    paddingTop:     14,
    paddingBottom:  12,
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
    zIndex:         10,
  },
  backBtn: {
    width:           34,
    height:          34,
    backgroundColor: 'rgba(255,255,255,0.14)',
    borderRadius:    9,
    borderWidth:     1,
    borderColor:     'rgba(255,255,255,0.14)',
    alignItems:      'center',
    justifyContent:  'center',
  },
  backArrow: {
    fontSize:   22,
    color:      '#fff',
    lineHeight: 24,
    fontFamily: Font.display,
  },
  titleBlock: { alignItems: 'center', flex: 1, paddingHorizontal: 8 },
  camTitle: {
    fontFamily:  Font.display,
    fontSize:    14,
    fontWeight:  '700',
    color:       '#fff',
    textAlign:   'center',
  },
  camPhase: {
    fontSize:      10,
    color:         Colors.orange,
    fontWeight:    '700',
    letterSpacing: 0.8,
    marginTop:     2,
    fontFamily:    Font.bodySm,
    textTransform: 'uppercase',
  },
  permText: {
    color:    '#fff',
    fontSize: 15,
    textAlign: 'center',
    paddingHorizontal: 32,
    fontFamily: Font.bodyMd,
  },
  permBtn: {
    backgroundColor:  Colors.orange,
    paddingHorizontal: 28,
    paddingVertical:   13,
    borderRadius:      12,
  },
  permBtnText: {
    color:      '#fff',
    fontWeight: '700',
    fontFamily: Font.display,
    fontSize:   15,
  },
});
