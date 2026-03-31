// app/(tabs)/workout.tsx  — Workout tab
import React from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView, StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '../../constants/theme';
import { Tag } from '../../components/ui/Tag';
import { WORKOUT_PLANS, WorkoutPlan, EXERCISES } from '../../constants/exercises';
import ScreenWrapper from '@/components/ui/ScreenWrapper';

const ACCENT_COLORS: Record<string, string> = {
  orange: Colors.orange,
  blue:   Colors.blue,
  teal:   '#14B8A6',
};

function WorkoutCard({ plan, onPress }: { plan: WorkoutPlan; onPress: () => void }) {
  const exerciseNames = plan.exercises
    .slice(0, 3)
    .map((e) => EXERCISES[e.key].name);
  const extra = plan.exercises.length - 3;

  return (

    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.88}>
      <View style={[styles.cardAccent, { backgroundColor: ACCENT_COLORS[plan.accent] }]} />
      <View style={styles.cardBody}>
        <View style={styles.cardRow}>
          <View>
            <Text style={styles.cardName}>{plan.name}</Text>
            <View style={styles.cardMeta}>
              <Text style={styles.cardMetaTxt}>⏱ {plan.duration} min</Text>
              <Text style={styles.cardMetaTxt}>{plan.exercises.length} exercises</Text>
            </View>
          </View>
          <Tag label={plan.tag} color={plan.tagColor} />
        </View>
        <View style={styles.pills}>
          {exerciseNames.map((n) => (
            <View key={n} style={styles.pill}>
              <Text style={styles.pillTxt}>{n}</Text>
            </View>
          ))}
          {extra > 0 && (
            <View style={styles.pill}>
              <Text style={styles.pillTxt}>+{extra} more</Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function WorkoutScreen() {
  const router = useRouter();

  return (
    <ScreenWrapper>
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />

      <View style={styles.header}>
        <Text style={styles.title}>Workouts</Text>
        <TouchableOpacity>
          {/* Search icon placeholder */}
          <Text style={styles.searchIcon}>⌕</Text>
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        {WORKOUT_PLANS.map((plan) => (
          <WorkoutCard
            key={plan.id}
            plan={plan}
            onPress={() => router.push(`/workout/${plan.id}`)}
          />
        ))}
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
  searchIcon: {
    fontSize: 28,
    color:    Colors.text2,
  },

  card: {
    marginHorizontal: 22,
    marginTop:        14,
    backgroundColor:  Colors.surface,
    borderWidth:      1,
    borderColor:      Colors.border,
    borderRadius:     Radius.md,
    overflow:         'hidden',
    ...Shadow.sm,
  },
  cardAccent: { height: 4 },
  cardBody:   { padding: 14 },
  cardRow: {
    flexDirection:  'row',
    alignItems:     'flex-start',
    justifyContent: 'space-between',
  },
  cardName: {
    fontFamily: Font.display,
    fontSize:   18,
    fontWeight: '700',
    color:      Colors.text,
  },
  cardMeta: {
    flexDirection: 'row',
    gap:           10,
    marginTop:     4,
  },
  cardMetaTxt: {
    fontSize:   12,
    color:      Colors.text2,
    fontFamily: Font.bodyMd,
  },

  pills: {
    flexDirection: 'row',
    flexWrap:      'wrap',
    gap:           6,
    marginTop:     10,
  },
  pill: {
    backgroundColor: Colors.bg2,
    borderWidth:     1,
    borderColor:     Colors.border,
    borderRadius:    Radius.full,
    paddingHorizontal: 9,
    paddingVertical:   3,
  },
  pillTxt: {
    fontSize:   11,
    color:      Colors.text2,
    fontWeight: '600',
    fontFamily: Font.bodySm,
  },
});
