// app/workout/[id].tsx  — Workout Detail screen
import React from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  SafeAreaView, StatusBar, TouchableOpacity,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '@/constants/theme';
import { Button } from '@/components/ui/Button';
import { Tag } from '@/components/ui/Tag';
import { WORKOUT_PLANS, EXERCISES } from '@/constants/exercises';
import ScreenWrapper from '@/components/ui/ScreenWrapper';

export default function WorkoutDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const plan   = WORKOUT_PLANS.find((p) => p.id === id);

  if (!plan) {
    return (
      <SafeAreaView style={styles.root}>
        <Text style={{ padding: 24, color: Colors.text }}>Workout not found.</Text>
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
        <View style={styles.headerInfo}>
          <Text style={styles.headerName}>{plan.name}</Text>
          <Text style={styles.headerMeta}>
            {plan.exercises.length} exercises · ~{plan.duration} min · 2–3 sets each
          </Text>
        </View>
        <Tag label={plan.tag} color={plan.tagColor} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Note */}
        <View style={styles.note}>
          <Text style={styles.noteText}>
            Warm up before you start and cool down after. Rest 60 seconds between sets — hydration matters.
          </Text>
        </View>

        {/* Exercise list */}
        <View style={styles.list}>
          {plan.exercises.map((item, i) => {
            const ex = EXERCISES[item.key];
            return (
              <View key={item.key} style={styles.item}>
                <View style={styles.itemNum}>
                  <Text style={styles.itemNumText}>{i + 1}</Text>
                </View>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{ex.name}</Text>
                  <Text style={styles.itemDet}>
                    {ex.isHold
                      ? `${item.reps}s · ${item.sets} sets`
                      : `${item.reps} reps · ${item.sets} sets`
                    }
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* CTA */}
        <View style={styles.cta}>
          <Button
            label="Begin Workout"
            onPress={() =>
              router.push({
                pathname: "/correct-form/[exercise]",
                params: {
                  exercise: plan.exercises[0].key,
                  planId: plan.id,
                },
              })
            }
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
    gap:               12,
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
    flexShrink:      0,
    ...Shadow.sm,
  },
  backArrow: {
    fontSize:   20,
    color:      Colors.text,
    lineHeight: 22,
    fontFamily: Font.display,
  },
  headerInfo: { flex: 1 },
  headerName: {
    fontFamily: Font.display,
    fontSize:   19,
    fontWeight: '800',
    color:      Colors.text,
  },
  headerMeta: {
    fontSize:   12,
    color:      Colors.text2,
    marginTop:   3,
    fontFamily: Font.bodyMd,
  },

  note: {
    margin:          14,
    backgroundColor: Colors.blueLt,
    borderLeftWidth: 3,
    borderLeftColor: Colors.blue,
    borderRadius:    Radius.sm,
    padding:         12,
  },
  noteText: {
    fontSize:   12,
    color:      Colors.blueDk,
    lineHeight: 18,
    fontFamily: Font.bodyMd,
  },

  list: {
    paddingHorizontal: 22,
    gap:               9,
  },
  item: {
    backgroundColor: Colors.surface,
    borderWidth:     1,
    borderColor:     Colors.border,
    borderRadius:    Radius.sm,
    padding:         13,
    flexDirection:   'row',
    alignItems:      'center',
    gap:             12,
    ...Shadow.sm,
  },
  itemNum: {
    width:           28,
    height:          28,
    backgroundColor: Colors.blueLt,
    borderRadius:    7,
    alignItems:      'center',
    justifyContent:  'center',
    flexShrink:      0,
  },
  itemNumText: {
    fontFamily: Font.display,
    fontSize:   13,
    fontWeight: '800',
    color:      Colors.blueDk,
  },
  itemInfo:  { flex: 1 },
  itemName: {
    fontSize:   14,
    fontWeight: '700',
    fontFamily: Font.display,
    color:      Colors.text,
  },
  itemDet: {
    fontSize:   11,
    color:      Colors.text2,
    marginTop:   2,
    fontFamily: Font.bodyMd,
  },
  itemEmoji: { fontSize: 18 },

  cta: {
    paddingHorizontal: 22,
    marginTop:         18,
  },
});