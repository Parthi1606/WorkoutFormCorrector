import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';

export interface Spec extends TurboModule {
  initializePoseLandmarker(): Promise<void>;
  detectPose(frameData: string): Promise<ReadonlyArray<ReadonlyArray<number>>>;
}

export default TurboModuleRegistry.getEnforcing<Spec>('PoseLandmarker');