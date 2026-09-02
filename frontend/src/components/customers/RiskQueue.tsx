import { useMemo, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { ChevronLeft, ChevronRight, HelpCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { RiskBadge } from '@/components/ui/risk-badge'
import { NIVEIS, formatBrl, formatPercent } from '@/lib/format'
import type { LinhaRisco } from '@/api/queries'

interface RiskQueueProps {
  linhas: LinhaRisco[]
  onSelect: (linha: LinhaRisco) => void
}

function ColumnHeaderWithTooltip({ label, tooltip }: { label: string; tooltip: string }) {
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center gap-1 cursor-help hover:text-foreground transition-colors group">
            <span>{label}</span>
            <HelpCircle size={12} className="opacity-40 group-hover:opacity-100 text-muted-foreground transition-opacity" />
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs text-xs p-2.5 leading-relaxed font-normal normal-case">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

const colunas: ColumnDef<LinhaRisco>[] = [
  {
    accessorKey: 'customerId',
    header: () => (
      <ColumnHeaderWithTooltip
        label="Cliente"
        tooltip="Identificador único do contrato ou assinante na base de dados da operadora."
      />
    ),
    cell: ({ getValue }) => (
      <span className="font-medium">{getValue<string>()}</span>
    ),
  },
  {
    accessorKey: 'tenure',
    header: () => (
      <ColumnHeaderWithTooltip
        label="Tenure"
        tooltip="Tempo de permanência do cliente na operadora em meses (tempo de casa / fidelidade acumulada)."
      />
    ),
    cell: ({ getValue }) => (
      <span className="font-mono tabular-nums">{getValue<number>()} m</span>
    ),
  },
  {
    accessorKey: 'contract',
    header: () => (
      <ColumnHeaderWithTooltip
        label="Contrato"
        tooltip="Tipo de vigência contratual do plano: Mês a Mês (Month-to-month), 1 Ano (One year) ou 2 Anos (Two year)."
      />
    ),
  },
  {
    accessorKey: 'monthlyCharges',
    header: () => (
      <ColumnHeaderWithTooltip
        label="Mensalidade"
        tooltip="Valor bruto recorrente cobrado mensalmente na fatura do cliente em Reais (R$)."
      />
    ),
    cell: ({ getValue }) => (
      <span className="font-mono tabular-nums">{formatBrl(getValue<number>())}</span>
    ),
  },
  {
    accessorKey: 'probabilidade',
    header: () => (
      <ColumnHeaderWithTooltip
        label="p(churn)"
        tooltip="Probabilidade percentual (%) estimada pelo modelo de Machine Learning de o cliente cancelar o plano nos próximos 30 dias."
      />
    ),
    cell: ({ getValue }) => (
      <span className="font-mono tabular-nums">{formatPercent(getValue<number>())}</span>
    ),
  },
  {
    accessorKey: 'nivel',
    header: () => (
      <ColumnHeaderWithTooltip
        label="Nível"
        tooltip="Faixa de classificação de risco de cancelamento: Baixo (< 30%), Médio (30-50%), Alto (50-70%) ou Crítico (≥ 70%)."
      />
    ),
    filterFn: 'equals',
    cell: ({ getValue }) => <RiskBadge nivel={getValue<string>()} />,
  },
  {
    accessorKey: 'mrrEmRisco',
    header: () => (
      <ColumnHeaderWithTooltip
        label="MRR em risco"
        tooltip="A sigla MRR vem de Monthly Recurring Revenue (Receita Recorrente Mensal). Por ser uma métrica financeira de faturamento, o MRR em Risco representa o valor monetário esperado em Reais (R$) que a empresa pode perder por mês com aquele cliente (calculado como Mensalidade × p(churn))."
      />
    ),
    cell: ({ getValue }) => (
      <span className="font-mono tabular-nums">{formatBrl(getValue<number>())}</span>
    ),
  },
]

export function RiskQueue({ linhas, onSelect }: RiskQueueProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'probabilidade', desc: true }])
  const [busca, setBusca] = useState('')
  const [nivelFiltro, setNivelFiltro] = useState<string>('todos')

  const table = useReactTable({
    data: linhas,
    columns: colunas,
    state: { sorting, globalFilter: busca },
    onSortingChange: setSorting,
    onGlobalFilterChange: setBusca,
    globalFilterFn: 'includesString',
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  })

  useMemo(() => {
    table.getColumn('nivel')?.setFilterValue(nivelFiltro === 'todos' ? undefined : nivelFiltro)
  }, [nivelFiltro, table])

  const pagina = table.getState().pagination.pageIndex + 1
  const totalPaginas = table.getPageCount()

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <Input
          value={busca}
          onChange={(evento) => setBusca(evento.target.value)}
          placeholder="Buscar por cliente…"
          aria-label="Buscar por cliente"
          className="max-w-xs"
        />
        <Select value={nivelFiltro} onValueChange={setNivelFiltro}>
          <SelectTrigger className="w-44" aria-label="Filtrar por nível de risco">
            <SelectValue placeholder="Nível de risco" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos os níveis</SelectItem>
            {NIVEIS.map((nivel) => (
              <SelectItem key={nivel} value={nivel}>
                {nivel}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="ml-auto text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} clientes
        </span>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader className="sticky top-0 bg-background">
            {table.getHeaderGroups().map((grupo) => (
              <TableRow key={grupo.id}>
                {grupo.headers.map((cabecalho) => (
                  <TableHead
                    key={cabecalho.id}
                    onClick={cabecalho.column.getToggleSortingHandler()}
                    className="cursor-pointer select-none"
                  >
                    {flexRender(cabecalho.column.columnDef.header, cabecalho.getContext())}
                    {{ asc: ' ↑', desc: ' ↓' }[cabecalho.column.getIsSorted() as string] ?? null}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((linha) => (
              <TableRow
                key={linha.id}
                onClick={() => onSelect(linha.original)}
                className="cursor-pointer"
              >
                {linha.getVisibleCells().map((celula) => (
                  <TableCell key={celula.id}>
                    {flexRender(celula.column.columnDef.cell, celula.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            {table.getRowModel().rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={colunas.length} className="h-24 text-center text-muted-foreground">
                  Nenhum cliente corresponde aos filtros.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <Button
          variant="outline"
          size="icon"
          aria-label="Página anterior"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <ChevronLeft />
        </Button>
        <span className="text-sm tabular-nums text-muted-foreground">
          Página {pagina} de {Math.max(1, totalPaginas)}
        </span>
        <Button
          variant="outline"
          size="icon"
          aria-label="Próxima página"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}
