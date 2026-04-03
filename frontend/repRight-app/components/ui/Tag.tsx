// components/ui/Tag.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Radius, Font } from '../../constants/theme';

type TagColor = 'orange' | 'blue' | 'green' | 'red';

interface TagProps {
  label:  string;
  color?: TagColor;
}

const TAG_COLORS: Record<TagColor, { bg: string; text: string }> = {
  orange: { bg: Colors.orangeLt,  text: Colors.orange  },
  blue:   { bg: Colors.blueLt,    text: Colors.blueDk  },
  green:  { bg: Colors.greenLt,   text: '#16A34A'      },
  red:    { bg: Colors.redLt,     text: Colors.red     },
};

export function Tag({ label, color = 'orange' }: TagProps) {
  const c = TAG_COLORS[color];
  return (
    <View style={[styles.tag, { backgroundColor: c.bg }]}>
      <Text style={[styles.text, { color: c.text }]}>{label.toUpperCase()}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: {
    paddingHorizontal: 10,
    paddingVertical:    4,
    borderRadius:       Radius.full,
  },
  text: {
    fontSize:      11,
    fontWeight:    '700',
    fontFamily:    Font.bodySm,
    letterSpacing: 0.5,
  },
});
