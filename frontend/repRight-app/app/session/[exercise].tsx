// app/session/[exercise].tsx
// Live training session screen (solo / Training Mode).
// Camera feed (raw, no pose overlay yet) + WebSocket form feedback.
//
// TEMPORARY: Mock frame sender added for WebSocket testing.
// Remove sendMockFrame and the test button once WebSocket is confirmed working.

import React, { useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  StatusBar, TouchableOpacity, Dimensions,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Colors, Font } from '@/constants/theme';
import { EXERCISES, ExerciseKey } from '@/constants/exercises';
import {
  RepBubble, HoldBubble, ErrorOverlay, FormStrip, WsDot,
} from '@/components/session/SessionOverlays';
import { useSessionStore } from '@/store/sessionStore';
import { useWebSocket } from '@/hooks/useWebSocket';

const { height: SCREEN_H } = Dimensions.get('window');

export default function SessionScreen() {
  const router   = useRouter();
  const { exercise } = useLocalSearchParams<{ exercise: ExerciseKey }>();
  const ex = exercise ? EXERCISES[exercise] : null;

  // Session state from Zustand
  const phase       = useSessionStore((s) => s.phase);
  const repCount    = useSessionStore((s) => s.rep_count);
  const validReps   = useSessionStore((s) => s.valid_reps);
  const checks      = useSessionStore((s) => s.checks);
  const holdSeconds = useSessionStore((s) => s.hold_seconds);
  const isConnected = useSessionStore((s) => s.isConnected);
  const startSession  = useSessionStore((s) => s.startSession);
  const resetSession  = useSessionStore((s) => s.resetSession);

  // WebSocket + mock sender
  const { sendLandmarks } = useWebSocket(exercise ?? null);

  // Camera permission
  const [permission, requestPermission] = useCameraPermissions();

  // Init session
  useEffect(() => {
    if (exercise) startSession(exercise);
    return () => resetSession();
  }, [exercise]);

  // ── TEMPORARY: mock frame for WebSocket testing ───────────────────
  const sendMockFrame = () => {
    const mockLandmarks = Array.from({ length: 33 }, () => ({
      x:          Math.random(),
      y:          Math.random(),
      z:          Math.random() * -0.1,
      visibility: 0.99,
    }));
    sendLandmarks(mockLandmarks);
  };
  // ─────────────────────────────────────────────────────────────────

  // Phase label shown in topbar
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

  if (!ex) {
    return (
      <View style={styles.root}>
        <Text style={{ color: '#fff', padding: 24 }}>Exercise not found.</Text>
      </View>
    );
  }

  if (!permission) {
    return <View style={styles.root} />;
  }

  if (!permission.granted) {
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

      {/* Camera — takes 80% of screen height */}
      <View style={styles.camArea}>

        {/* Raw camera feed */}
        <CameraView style={StyleSheet.absoluteFill} facing="front" />

        {/* Top bar overlay */}
        <View style={styles.topBar}>
          <TouchableOpacity
            style={styles.backBtn}
            onPress={() => router.back()}
          >
            <Text style={styles.backArrow}>‹</Text>
          </TouchableOpacity>
          <View style={styles.titleBlock}>
            <Text style={styles.camTitle}>{ex.name}</Text>
            <Text style={styles.camPhase}>{phaseLabel}</Text>
          </View>
          <WsDot connected={isConnected} />
        </View>

        {/* Rep / hold counter */}
        {ex.isHold
          ? <HoldBubble seconds={holdSeconds ?? 0} />
          : <RepBubble repCount={repCount} validReps={validReps} phase={phase} />
        }

        {/* Form fault pills (max 2) */}
        <ErrorOverlay checks={checks} />

        {/* ── TEMPORARY: WebSocket test button ─────────────────────
            Remove this block once WebSocket is confirmed working.  */}
        {/* <TouchableOpacity
          style={styles.testBtn}
          onPress={sendMockFrame}
        >
          <Text style={styles.testBtnText}>
            {isConnected ? '● Send Mock Frame' : '○ Not Connected'}
          </Text>
        </TouchableOpacity> */}
        {/* ─────────────────────────────────────────────────────── */}

      </View>

      {/* Form quality strip — bottom 20% */}
      <FormStrip checks={checks} />
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
    position:          'absolute',
    top:               0,
    left:              0,
    right:             0,
    paddingHorizontal: 16,
    paddingTop:        14,
    paddingBottom:     12,
    flexDirection:     'row',
    alignItems:        'center',
    justifyContent:    'space-between',
    zIndex:            10,
    backgroundColor:   'rgba(0,0,0,0.0)',
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
  titleBlock: { alignItems: 'center' },
  camTitle: {
    fontFamily: Font.display,
    fontSize:   15,
    fontWeight: '700',
    color:      '#fff',
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

  // ── TEMPORARY test button styles ──────────────────────────────────
  testBtn: {
    position:        'absolute',
    bottom:          20,
    alignSelf:       'center',
    backgroundColor: Colors.orange,
    paddingHorizontal: 20,
    paddingVertical:   10,
    borderRadius:    10,
    zIndex:          20,
  },
  testBtnText: {
    color:      '#fff',
    fontSize:   13,
    fontWeight: '700',
    fontFamily: Font.display,
  },
  // ─────────────────────────────────────────────────────────────────

  // Permissions
  permText: {
    color:             '#fff',
    fontSize:          15,
    fontFamily:        Font.bodyMd,
    textAlign:         'center',
    paddingHorizontal: 32,
  },
  permBtn: {
    backgroundColor:   Colors.orange,
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