import { MlopsHealth } from '@/components/mlops/MlopsHealth'
import { ModelRegistryLab } from '@/components/mlops/ModelRegistryLab'

export function MlopsPage() {
  return (
    <div className="space-y-8">
      <ModelRegistryLab />
      <div className="border-t pt-6">
        <h2 className="text-lg font-bold mb-4">Observabilidade & Saúde Operacional</h2>
        <MlopsHealth />
      </div>
    </div>
  )
}

