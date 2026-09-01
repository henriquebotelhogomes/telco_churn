import { ContinuousTrainingPanel } from '@/components/mlops/ContinuousTrainingPanel'
import { FeatureCatalogPanel } from '@/components/features/FeatureCatalogPanel'
import { K8sClusterTopology } from '@/components/ops/K8sClusterTopology'
import { MlopsHealth } from '@/components/mlops/MlopsHealth'
import { ModelRegistryLab } from '@/components/mlops/ModelRegistryLab'
import { SafetyObservatoryPanel } from '@/components/safety/SafetyObservatoryPanel'
import { StreamingControlPanel } from '@/components/streaming/StreamingControlPanel'
import { StreamingWindowInspector } from '@/components/streaming/StreamingWindowInspector'

export function MlopsPage() {
  return (
    <div className="space-y-8">
      <StreamingControlPanel />
      <StreamingWindowInspector />
      <FeatureCatalogPanel />
      <SafetyObservatoryPanel />
      <ModelRegistryLab />
      <ContinuousTrainingPanel />
      <K8sClusterTopology />
      <div className="border-t pt-6">
        <h2 className="text-lg font-bold mb-4">Observabilidade & Saúde Operacional</h2>
        <MlopsHealth />
      </div>
    </div>
  )
}





