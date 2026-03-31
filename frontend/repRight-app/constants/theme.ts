// constants/theme.ts
// Single source of truth for all design tokens.
// Mirrors the CSS variables in repright_v2.html exactly.

export const Colors = {
  orange:     '#F5651D',
  orangeLt:   '#FEE9DE',
  orangeMid:  '#FBBFA0',

  blue:       '#3B82C4',
  blueLt:     '#DBEAFE',
  blueMid:    '#93C5FD',
  blueDk:     '#1D4E89',

  bg:         '#FAF9F7',
  bg2:        '#F2F0EC',
  surface:    '#FFFFFF',
  surface2:   '#F7F6F3',

  border:     '#E8E5DF',
  border2:    '#D4D0C8',

  text:       '#1A1916',
  text2:      '#6B6760',
  text3:      '#AAA89F',

  green:      '#22C55E',
  greenLt:    '#DCFCE7',
  red:        '#EF4444',
  redLt:      '#FEE2E2',
  yellow:     '#F59E0B',

  // Session screen (dark)
  camBg:      '#0a0a0c',
  camSurface: '#111115',
} as const;

export const Radius = {
  xs:   8,
  sm:   12,
  md:   18,
  full: 999,
} as const;

export const Shadow = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10,
    shadowRadius: 12,
    elevation: 4,
  },
} as const;

// Font families — add to app.json / expo-font as needed
// Using system fonts that closely match Syne + Nunito feel
// Replace with actual font keys once expo-font is loaded
export const Font = {
  display: 'Syne_800ExtraBold',   // headings, numbers
  body:    'Nunito_400Regular',   // body text
  bodyMd:  'Nunito_500Medium',
  bodySm:  'Nunito_600SemiBold',
  bodyBold:'Nunito_700Bold',
} as const;

export const WS_BASE = 'ws://192.168.1.18:8000';
