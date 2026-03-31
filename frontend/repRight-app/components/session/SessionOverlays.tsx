// components/session/SessionOverlays.tsx
// All overlay components rendered on top of the camera view.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Radius, Font } from '../../constants/theme';
import { FormCheck } from '../../store/sessionStore';

// ── WebSocket connected dot ────────────────────────────────────────────────

interface WsDotProps { connected: boolean; }

export function WsDot({ connected }: WsDotProps) {
  return (
    <View style={[
      styles.wsDot,
      { backgroundColor: connected ? Colors.green : Colors.red },
    ]} />
  );
}

// ── Rep bubble (top-left over camera) ─────────────────────────────────────

interface RepBubbleProps {
  repCount:  number;
  validReps: number;
  phase:     string;
  // for workout mode
  targetReps?: number;
  setLabel?:   string;
}

export function RepBubble({
  repCount, validReps, phase, targetReps, setLabel,
}: RepBubbleProps) {
  return (
    <View style={styles.repBubble}>
      <Text style={styles.repNum}>{repCount}</Text>
      {targetReps != null
        ? <Text style={styles.repLbl}>/ {targetReps} reps</Text>
        : <Text style={styles.repLbl}>REPS</Text>
      }
      {setLabel
        ? <Text style={styles.repClean}>{setLabel}</Text>
        : <Text style={styles.repClean}>{validReps} clean</Text>
      }
    </View>
  );
}

// ── Hold timer bubble ──────────────────────────────────────────────────────

interface HoldBubbleProps { seconds: number; }

export function HoldBubble({ seconds }: HoldBubbleProps) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const label = mins > 0
    ? `${mins}:${String(secs).padStart(2, '0')}`
    : `${secs}s`;

  return (
    <View style={styles.repBubble}>
      <Text style={styles.repNum}>{label}</Text>
      <Text style={styles.repLbl}>HOLD</Text>
    </View>
  );
}

// ── Error overlay (top-right, max 2 faults) ───────────────────────────────

interface ErrorOverlayProps { checks: FormCheck[]; }

export function ErrorOverlay({ checks }: ErrorOverlayProps) {
  const failing = checks.filter((c) => !c.ok).slice(0, 2);
  if (failing.length === 0) return null;

  return (
    <View style={styles.errOverlay}>
      {failing.map((c) => (
        <View key={c.label} style={styles.errPill}>
          <View style={styles.errDot} />
          <View>
            <Text style={styles.errLabel}>{c.label.toUpperCase()}</Text>
            <Text style={styles.errText}>{c.message}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Form strip (bottom panel, Training Mode) ───────────────────────────────

interface FormStripProps { checks: FormCheck[]; }

export function FormStrip({ checks }: FormStripProps) {
  const shown = checks.slice(0, 3);

  return (
    <View style={styles.strip}>
      {shown.map((c) => {
        const pct   = Math.min(100, Math.max(0, c.ok ? 88 + Math.random() * 12 : 30 + Math.random() * 40));
        const color = c.ok ? Colors.green : pct > 60 ? Colors.yellow : Colors.red;
        return (
          <View key={c.label} style={styles.stripRow}>
            <Text style={styles.stripLbl} numberOfLines={1}>{c.label}</Text>
            <View style={styles.stripTrack}>
              <View style={[styles.stripFill, { width: `${pct}%`, backgroundColor: color }]} />
            </View>
            <Text style={[styles.stripVal, { color }]}>{Math.round(pct)}%</Text>
          </View>
        );
      })}
    </View>
  );
}

// ── Workout bottom strip ───────────────────────────────────────────────────

interface WorkoutStripProps {
  exerciseName: string;
  setLabel:     string;
  repCount:     number;
  targetReps:   number;
  formPct:      number;
  onSkip:       () => void;
}

export function WorkoutStrip({
  exerciseName, setLabel, repCount, targetReps, formPct, onSkip,
}: WorkoutStripProps) {
  const progress = targetReps > 0 ? repCount / targetReps : 0;

  return (
    <View style={styles.wstrip}>
      <Text style={styles.wstripTitle}>{exerciseName} — {setLabel}</Text>
      <View style={styles.wstripMeta}>
        <View style={styles.wstripPillBlue}>
          <Text style={styles.wstripPillBlueTxt}>{repCount} / {targetReps} reps</Text>
        </View>
        <View style={styles.wstripPillOrange}>
          <Text style={styles.wstripPillOrangeTxt}>Form {formPct}%</Text>
        </View>
      </View>
      <View style={styles.wstripProg}>
        <View style={styles.wstripTrack}>
          <View style={[styles.wstripFill, { width: `${Math.min(100, progress * 100)}%` }]} />
        </View>
        <Text style={styles.wstripSkip} onPress={onSkip}>Skip set ›</Text>
      </View>
    </View>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  // WsDot
  wsDot: {
    width: 8, height: 8,
    borderRadius: 4,
  },

  // RepBubble
  repBubble: {
    position:       'absolute',
    top:            68,
    left:           12,
    backgroundColor:'rgba(10,8,6,0.78)',
    borderRadius:   12,
    padding:        12,
    alignItems:     'center',
    borderWidth:    1,
    borderColor:    'rgba(255,255,255,0.1)',
  },
  repNum: {
    fontFamily: Font.display,
    fontSize:   38,
    fontWeight: '800',
    color:      Colors.orange,
    lineHeight: 40,
  },
  repLbl: {
    fontSize:      9,
    color:         'rgba(255,255,255,0.38)',
    letterSpacing: 0.8,
    marginTop:     2,
    fontFamily:    Font.bodySm,
  },
  repClean: {
    fontSize:   10,
    color:      Colors.green,
    fontWeight: '700',
    marginTop:   3,
    fontFamily: Font.bodySm,
  },

  // ErrorOverlay
  errOverlay: {
    position:  'absolute',
    top:       68,
    right:     12,
    gap:       6,
    maxWidth:  160,
    zIndex:    11,
  },
  errPill: {
    backgroundColor: 'rgba(12,8,6,0.82)',
    borderRadius:    10,
    borderWidth:     1,
    borderColor:     'rgba(239,68,68,0.4)',
    padding:         10,
    flexDirection:   'row',
    alignItems:      'flex-start',
    gap:             7,
  },
  errDot: {
    width:           7,
    height:          7,
    borderRadius:    4,
    backgroundColor: Colors.red,
    marginTop:       3,
    flexShrink:      0,
  },
  errLabel: {
    fontSize:      9,
    color:         'rgba(239,68,68,0.75)',
    letterSpacing: 0.5,
    fontWeight:    '700',
    fontFamily:    Font.bodySm,
  },
  errText: {
    fontSize:   11,
    color:      '#fff',
    lineHeight: 15,
    fontWeight: '600',
    fontFamily: Font.bodyBold,
  },

  // FormStrip
  strip: {
    position:        'absolute',
    bottom:          0,
    left:            0,
    right:           0,
    height:          '20%',
    backgroundColor: Colors.surface,
    borderTopWidth:  1,
    borderTopColor:  Colors.border,
    justifyContent:  'center',
    paddingHorizontal: 18,
    gap:             8,
  },
  stripRow: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           10,
  },
  stripLbl: {
    fontSize:      11,
    fontWeight:    '700',
    color:         Colors.text2,
    letterSpacing: 0.3,
    width:         72,
    flexShrink:    0,
    fontFamily:    Font.bodySm,
    textTransform: 'uppercase',
  },
  stripTrack: {
    flex:            1,
    height:          5,
    backgroundColor: Colors.bg2,
    borderRadius:    3,
    overflow:        'hidden',
  },
  stripFill: {
    height:       '100%',
    borderRadius: 3,
  },
  stripVal: {
    fontSize:   11,
    width:      32,
    textAlign:  'right',
    fontWeight: '700',
    fontFamily: Font.bodySm,
  },

  // WorkoutStrip
  wstrip: {
    position:        'absolute',
    bottom:          0,
    left:            0,
    right:           0,
    height:          '20%',
    backgroundColor: Colors.surface,
    borderTopWidth:  1,
    borderTopColor:  Colors.border,
    paddingHorizontal: 18,
    justifyContent:  'center',
    gap:             7,
  },
  wstripTitle: {
    fontFamily: Font.display,
    fontSize:   13,
    fontWeight: '700',
    color:      Colors.text,
  },
  wstripMeta: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           8,
  },
  wstripPillBlue: {
    backgroundColor: Colors.blueLt,
    borderRadius:    Radius.full,
    paddingHorizontal: 10,
    paddingVertical:   4,
  },
  wstripPillBlueTxt: {
    fontSize:   11,
    fontWeight: '700',
    color:      Colors.blueDk,
    fontFamily: Font.display,
  },
  wstripPillOrange: {
    backgroundColor: Colors.orangeLt,
    borderRadius:    Radius.full,
    paddingHorizontal: 10,
    paddingVertical:   4,
  },
  wstripPillOrangeTxt: {
    fontSize:   11,
    fontWeight: '700',
    color:      Colors.orange,
    fontFamily: Font.display,
  },
  wstripProg: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           8,
  },
  wstripTrack: {
    flex:            1,
    height:          5,
    backgroundColor: Colors.bg2,
    borderRadius:    3,
    overflow:        'hidden',
  },
  wstripFill: {
    height:       '100%',
    borderRadius: 3,
    // gradient approximated as two-color linear — real gradient needs expo-linear-gradient
    backgroundColor: Colors.blue,
  },
  wstripSkip: {
    fontSize:   11,
    color:      Colors.text3,
    fontWeight: '600',
    fontFamily: Font.bodySm,
  },
});
