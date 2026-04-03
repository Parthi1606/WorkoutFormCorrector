// constants/exercises.ts
// Metadata for every exercise RepRight supports.
// The `key` must match the WebSocket route on the FastAPI backend:
//   ws://host:8000/session/{key}

export type ExerciseKey =
  | 'bicep_curl'
  | 'squat'
  | 'shoulder_press'
  | 'lunge'
  | 'pushup'
  | 'bent_over_row'
  | 'plank';

export interface Exercise {
  key:        ExerciseKey;
  name:       string;
  emoji:      string;
  category:   string;        // e.g. "Arms · Unilateral"
  bgVariant:  'orange' | 'blue' | 'teal' | 'purple' | 'green';
  isHold:     boolean;       // plank = true, rest = false
  formTips:   string[];      // shown on Correct Form screen
  cameraHint: string;        // positioning tip shown before session
}

export const EXERCISES: Record<ExerciseKey, Exercise> = {
  bicep_curl: {
    key:       'bicep_curl',
    name:      'Bicep Curl',
    emoji:     '🏋️',
    category:  'Arms · Unilateral',
    bgVariant: 'orange',
    isHold:    false,
    formTips: [
      'Stand upright — keep your back straight and core engaged throughout.',
      'Pin your elbow to your side — don\'t let it drift forward or flare out.',
      'Full range of motion — curl until forearm is vertical, then lower fully.',
      'Keep your wrist neutral — no bending toward or away from you.',
      'Slow and controlled beats fast every time — no swinging.',
    ],
    cameraHint: 'Stand side-on to the camera so your full body is visible for best detection.',
  },

  squat: {
    key:       'squat',
    name:      'Squat',
    emoji:     '🦵',
    category:  'Legs · Bilateral',
    bgVariant: 'teal',
    isHold:    false,
    formTips: [
      'Feet shoulder-width apart, toes slightly turned out.',
      'Keep your chest up and your gaze forward throughout.',
      'Push your hips back before bending your knees.',
      'Knees track over your toes — don\'t let them cave inward.',
      'Drive through your heels to stand, squeezing your glutes at the top.',
    ],
    cameraHint: 'Stand facing the camera with your full body visible — step back if needed.',
  },

  shoulder_press: {
    key:       'shoulder_press',
    name:      'Shoulder Press',
    emoji:     '🙌',
    category:  'Shoulders · Bilateral',
    bgVariant: 'blue',
    isHold:    false,
    formTips: [
      'Start with elbows at shoulder height, weights at ear level.',
      'Press straight up — don\'t flare elbows forward.',
      'Avoid arching your lower back — keep core tight.',
      'Full extension at the top, then control on the way down.',
      'Keep your wrists stacked over your elbows throughout.',
    ],
    cameraHint: 'Stand facing the camera with your arms fully visible.',
  },

  lunge: {
    key:       'lunge',
    name:      'Lunge',
    emoji:     '🚶',
    category:  'Legs · Unilateral',
    bgVariant: 'purple',
    isHold:    false,
    formTips: [
      'Step forward with one foot, keeping your torso upright.',
      'Lower your back knee toward the floor — don\'t let it slam down.',
      'Front knee stays above your ankle — not past your toes.',
      'Push through your front heel to return to standing.',
      'Keep your shoulders back and core engaged throughout.',
    ],
    cameraHint: 'Stand side-on to the camera so your full stride is visible.',
  },

  pushup: {
    key:       'pushup',
    name:      'Push-up',
    emoji:     '💪',
    category:  'Chest · Bilateral',
    bgVariant: 'orange',
    isHold:    false,
    formTips: [
      'Hands slightly wider than shoulder-width, fingers forward.',
      'Keep your body in a straight line from head to heels.',
      'Lower your chest to just above the floor — full range.',
      'Elbows at roughly 45° — don\'t flare them out wide.',
      'No sagging hips or raised glutes — stay plank-tight.',
    ],
    cameraHint: 'Position camera to the side so your full body is visible.',
  },

  bent_over_row: {
    key:       'bent_over_row',
    name:      'Bent-Over Row',
    emoji:     '🔄',
    category:  'Back · Bilateral',
    bgVariant: 'blue',
    isHold:    false,
    formTips: [
      'Hinge at the hips until your torso is roughly 45° to the floor.',
      'Keep your back flat — no rounding at the lower back.',
      'Pull the weight to your lower chest, leading with your elbows.',
      'Squeeze your shoulder blades together at the top.',
      'Control the descent — don\'t let the weight drop.',
    ],
    cameraHint: 'Stand side-on to the camera so your torso angle is clearly visible.',
  },

  plank: {
    key:       'plank',
    name:      'Plank',
    emoji:     '🧘',
    category:  'Core · Hold',
    bgVariant: 'blue',
    isHold:    true,
    formTips: [
      'Forearms on the floor, elbows directly below your shoulders.',
      'Keep your body in a straight line — no sagging or piking.',
      'Squeeze your core, glutes, and quads — full body tension.',
      'Breathe steadily — don\'t hold your breath.',
      'Keep your neck neutral — don\'t drop or crane your head.',
    ],
    cameraHint: 'Position camera to the side so your full body line is visible.',
  },
};

export const EXERCISE_LIST: Exercise[] = Object.values(EXERCISES);

// Workout plans shown on the Workout tab
export interface WorkoutPlan {
  id:        string;
  name:      string;
  duration:  number;   // minutes
  accent:    'orange' | 'blue' | 'teal';
  tag:       string;
  tagColor:  'orange' | 'blue' | 'green';
  exercises: { key: ExerciseKey; reps: number; sets: number; }[];
}

export const WORKOUT_PLANS: WorkoutPlan[] = [
  {
    id:       'full-body',
    name:     'Full Body',
    duration: 35,
    accent:   'orange',
    tag:      'Popular',
    tagColor: 'orange',
    exercises: [
      { key: 'squat',          reps: 15, sets: 2 },
      { key: 'bicep_curl',     reps: 10, sets: 3 },
      { key: 'plank',          reps: 60, sets: 2 },
      { key: 'lunge',          reps: 20, sets: 3 },
      { key: 'pushup',         reps: 12, sets: 3 },
      { key: 'shoulder_press', reps: 10, sets: 3 },
    ],
  },
  {
    id:       'upper-body',
    name:     'Upper Body',
    duration: 20,
    accent:   'blue',
    tag:      'Upper',
    tagColor: 'blue',
    exercises: [
      { key: 'bicep_curl',     reps: 10, sets: 3 },
      { key: 'shoulder_press', reps: 10, sets: 3 },
      { key: 'bent_over_row',  reps: 12, sets: 3 },
    ],
  },
  {
    id:       'lower-body',
    name:     'Lower Body',
    duration: 25,
    accent:   'teal',
    tag:      'Lower',
    tagColor: 'green',
    exercises: [
      { key: 'squat',  reps: 15, sets: 2 },
      { key: 'lunge',  reps: 20, sets: 3 },
      { key: 'plank',  reps: 60, sets: 2 },
    ],
  },
];
