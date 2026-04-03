// app/(tabs)/index.tsx  — Home / Training tab
import React from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, SafeAreaView, StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Radius, Font, Shadow } from '@/constants/theme';
import { EXERCISE_LIST, Exercise } from '@/constants/exercises';
import { useAuthStore } from '@/store/authStore';
import  ScreenWrapper  from '@/components/ui/ScreenWrapper';
import { Image } from 'react-native';

const EXERCISE_IMAGES: Record<string, any> = {
  squat: require('../../assets/exercise-thumbnails/squat.png'),
  lunge: require('../../assets/exercise-thumbnails/lunge.png'),
  plank: require('../../assets/exercise-thumbnails/plank.png'),
  bicep_curl: require('../../assets/exercise-thumbnails/bicep_curl.png'),
  pushup: require('../../assets/exercise-thumbnails/pushup.png'),
  bent_over_row: require('../../assets/exercise-thumbnails/bent_over_row.png'),
  shoulder_press: require('../../assets/exercise-thumbnails/shoulder_press.png'), 
};

const BG_COLORS: Record<string, string> = {
  orange: '#FFF7F3',
  blue:   '#EFF6FF',
  teal:   '#F0FDFA',
  purple: '#F5F3FF',
  green:  '#F0FDF4',
};

function ExerciseCard({ ex, onPress }: { ex: Exercise; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.exCard} onPress={onPress} activeOpacity={0.85}>
      <View style={[styles.exCardTop, { backgroundColor: BG_COLORS[ex.bgVariant] }]}>
        {EXERCISE_IMAGES[ex.key] ? (
          <Image source={EXERCISE_IMAGES[ex.key]} style={styles.exImage} resizeMode="cover" />
        ) : (
          <View style={styles.fallback}>
            <Text style={styles.fallbackText}>?</Text>
          </View>
        )}
      </View>
      <View style={styles.exCardBtm}>
        <Text style={styles.exName}>{ex.name}</Text>
        <Text style={styles.exSub}>{ex.category}</Text>
      </View>
    </TouchableOpacity>
  );
}

export default function TrainingScreen() {
  const router = useRouter();
  const user   = useAuthStore((s) => s.user);
  const name   = user?.name?.split(' ')[0] ?? 'there';

  // Mock stats — replace with real data from your API/store
  const stats = { reps: 142, form: 87, sessions: 12, streak: 6 };

  return (
    <ScreenWrapper>
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={Colors.bg} />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Top bar */}
        <View style={styles.topBar}>
          <View>
            <Text style={styles.greeting}>
              Hello, <Text style={styles.greetingAccent}>{name}</Text> 
            </Text>
            <Text style={styles.greetingSub}>Ready to train smart today?</Text>
          </View>
          
        </View>

        {/* Stats row
        <View style={styles.statsRow}>
          <View style={[styles.statCard, styles.statCardAccent]}>
            <Text style={[styles.statVal, { color: Colors.orange }]}>{stats.reps}</Text>
            <Text style={styles.statLbl}>TOTAL REPS</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statVal}>{stats.form}%</Text>
            <Text style={styles.statLbl}>FORM SCORE</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statVal}>{stats.sessions}</Text>
            <Text style={styles.statLbl}>SESSIONS</Text>
          </View>
        </View> */}

 
        

        {/* Exercise grid */}
        <View style={styles.secHdr}>
          <Text style={styles.secTitle}>Exercises</Text>
        </View>

        <View style={styles.exGrid}>
        {EXERCISE_LIST.map((ex) => (
          <ExerciseCard
            key={ex.key}
            ex={ex}
            onPress={() => router.push(`/correct-form/${ex.key}`)}
          />
        ))}
      </View>

      </ScrollView>
      </View>
    </ScreenWrapper>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1 },
  scroll: { paddingBottom: 32 },
  
  exImage: {
    width: '100%',
    height: '100%',
  },
  
  fallback: {
    width: 60,
    height: 60,
    backgroundColor: '#E5E7EB', // light grey
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },

  fallbackText: {
    fontSize: 18,
    color: '#9CA3AF',
    fontWeight: '700',
  },

  topBar: {
    paddingHorizontal: 22,
    paddingTop:        16,
    paddingBottom:     8,
    flexDirection:     'row',
    justifyContent:    'space-between',
    alignItems:        'center',
  },
  greeting: {
    fontFamily:    Font.display,
    fontSize:      55,
    fontWeight:    '800',
    letterSpacing: -0.5,
    color:         Colors.text,
    lineHeight:    65,
  },
  greetingAccent: { color: Colors.orange },
  greetingSub: {
    fontSize:   18,
    color:      Colors.text2,
    marginTop:   4,
    fontFamily: Font.bodyMd,
  },
  streakChip: {
    backgroundColor: Colors.orangeLt,
    borderWidth:     1,
    borderColor:     Colors.orangeMid,
    borderRadius:    Radius.full,
    paddingHorizontal: 12,
    paddingVertical:    7,
  },
  streakText: {
    fontSize:   13,
    fontWeight: '700',
    color:      Colors.orange,
    fontFamily: Font.display,
  },

  statsRow: {
    flexDirection:     'row',
    gap:               10,
    paddingHorizontal: 22,
    marginTop:         4,
  },
  statCard: {
    flex:            1,
    backgroundColor: Colors.surface,
    borderWidth:     1,
    borderColor:     Colors.border,
    borderRadius:    Radius.sm,
    padding:         13,
    ...Shadow.sm,
  },
  statCardAccent: {},
  statVal: {
    fontFamily: Font.display,
    fontSize:   22,
    fontWeight: '800',
    color:      Colors.blueDk,
  },
  statLbl: {
    fontSize:      10,
    color:         Colors.text3,
    marginTop:     2,
    letterSpacing: 0.5,
    fontFamily:    Font.bodySm,
    textTransform: 'uppercase',
  },

  secHdr: {
    flexDirection:     'row',
    justifyContent:    'space-between',
    alignItems:        'center',
    paddingHorizontal: 22,
    paddingTop:        20,
    paddingBottom:     12,
  },
  secTitle: {
    fontFamily: Font.display,
    fontSize:   30,
    fontWeight: '700',
    color:      Colors.text,
  },
  seeAll: {
    fontSize:   13,
    color:      Colors.blue,
    fontWeight: '700',
    fontFamily: Font.bodySm,
  },

  exGrid: {
    flexDirection:     'row',
    flexWrap:          'wrap',
    gap:               12,
    paddingHorizontal: 22,
  },
  exCard: {
    width:           '47%',
    borderRadius:    Radius.md,
    overflow:        'hidden',
    borderWidth:     1,
    borderColor:     Colors.border,
    backgroundColor: Colors.surface,
    ...Shadow.sm,
  },
  exCardTop: {
    width: '100%',
    aspectRatio: 1,        // square, adjust to 4/3 or 16/9 if you prefer
    alignItems: 'center',
    justifyContent: 'center',
  },
  exEmoji:    { fontSize: 38 },
  exCardBtm:  { padding: 10 },
  exName: {
    fontFamily: Font.display,
    fontSize:   14,
    fontWeight: '700',
    color:      Colors.text,
  },
  exSub: {
    fontSize:   11,
    color:      Colors.text2,
    marginTop:   2,
    fontFamily: Font.bodyMd,
  },
});
