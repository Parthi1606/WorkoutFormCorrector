// components/ui/Button.tsx
import React from 'react';
import {
  TouchableOpacity, Text, StyleSheet, ActivityIndicator,
  ViewStyle, TextStyle,
} from 'react-native';
import { Colors, Radius, Font } from '../../constants/theme';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost';

interface ButtonProps {
  label:      string;
  onPress:    () => void;
  variant?:   Variant;
  loading?:   boolean;
  disabled?:  boolean;
  style?:     ViewStyle;
  textStyle?: TextStyle;
  icon?:      React.ReactNode;
}

export function Button({
  label, onPress, variant = 'primary',
  loading, disabled, style, textStyle, icon,
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      style={[styles.base, styles[variant], isDisabled && styles.disabled, style]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.82}
    >
      {loading
        ? <ActivityIndicator color={variant === 'primary' ? '#fff' : Colors.blue} />
        : <>
            {icon}
            <Text style={[styles.label, styles[`${variant}Text`], textStyle]}>
              {label}
            </Text>
          </>
      }
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'center',
    gap:            8,
    borderRadius:   Radius.md,
    paddingVertical: 17,
    paddingHorizontal: 20,
    width: '100%',
  },
  primary:   { backgroundColor: Colors.orange },
  secondary: { backgroundColor: Colors.blueLt },
  outline:   { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: Colors.blue },
  ghost:     { backgroundColor: 'transparent' },
  disabled:  { opacity: 0.5 },

  label: {
    fontSize:      15,
    fontWeight:    '700',
    letterSpacing: 0.6,
    fontFamily:    Font.display,
  },
  primaryText:   { color: '#fff' },
  secondaryText: { color: Colors.blueDk },
  outlineText:   { color: Colors.blue },
  ghostText:     { color: Colors.text2 },
});
