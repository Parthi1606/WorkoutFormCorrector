// app/(tabs)/_layout.tsx
// Bottom tab navigator. Three tabs: Training, Workout, Profile.
// Icons are inline SVG paths rendered via Text — replace with
// react-native-svg or @expo/vector-icons if you prefer.

import React from 'react';
import { Tabs } from 'expo-router';
import { Colors, Font } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown:     false,
        tabBarActiveTintColor:   Colors.blue,
        tabBarInactiveTintColor: Colors.text3,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          fontFamily: Font.bodySm,
          marginBottom: 4,
        },
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopColor:  Colors.border,
          borderTopWidth:  1,
          height:          80,     // 👈 slightly taller
          paddingTop:      8,
          paddingBottom:   10,     // 👈 KEY FIX
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title:    'Training',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="barbell-outline" color={color} size={28} />
            ),
            //<TabIcon color={color} type="training" />
          
        }}
      />
      <Tabs.Screen
        name="workout"
        options={{
          title: 'Workout',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="fitness-outline" color={color} size={28} />
          ),
        }}
      />

      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-outline" color={color} size={28} />
          ),
        }}
      />
    </Tabs>
  );
}

// Simple emoji icons as placeholders — swap with @expo/vector-icons
function TabIcon({ color, type }: { color: string; type: string }) {
  const icons: Record<string, string> = {
    training: '🏃',
    workout:  '🏋️',
    profile:  '👤',
  };
  return null; // icon handled by tabBarIcon label emoji above
  // To use real icons: import { Ionicons } from '@expo/vector-icons';
  // return <Ionicons name="barbell-outline" color={color} size={22} />;
}
