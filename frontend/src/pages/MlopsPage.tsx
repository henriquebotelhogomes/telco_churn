import { ContinuousTrainingPanel } from '@/components/mlops/ContinuousTrainingPanel'
import { MlopsHealth } from '@/components/mlops/MlopsHealth'
import { ModelRegistryLab } from '@/components/mlops/ModelRegistryLab'
import { StreamingControlPanel } from '@/components/streaming/StreamingControlPanel'
import { StreamingWindowInspector } from '@/components/streaming/StreamingWindowInspector'

export function MlopsPage() {
  return (
    <div className="space-y-8">
      <StreamingControlPanel />
      <StreamingWindowInspector />
      <ModelRegistryLab />
      <ContinuousTrainingPanel />
      <div className="border-t pt-6">
        <h2 className="text-lg font-bold mb-4">Observabilidade & Saúde Operacional</h2>
        <MlopsHealth />
      </div>
    </div>
  )
}



