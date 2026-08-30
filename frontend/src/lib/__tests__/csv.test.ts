import { describe, expect, it } from 'vitest'

import { canonicalToClientePt, parseCsv } from '@/lib/csv'

const CSV_EXEMPLO = [
  'customerID,gender,Contract,TotalCharges',
  'A-1,Female,"Month-to-month",29.85',
  'A-2,Male,"Two year","1,253.70"',
].join('\n')

describe('parseCsv', () => {
  it('faz parse com aspas e campos vazios', () => {
    const linhas = parseCsv(CSV_EXEMPLO)
    expect(linhas).toHaveLength(2)
    expect(linhas[0].customerID).toBe('A-1')
    expect(linhas[0].Contract).toBe('Month-to-month')
    expect(linhas[1].TotalCharges).toBe('1,253.70')
  })

  it('retorna vazio para CSV sem dados', () => {
    expect(parseCsv('a,b,c\n')).toEqual([])
  })
})

const LINHA_CANONICA: Record<string, string> = {
  customerID: '7590-VHVEG',
  gender: 'Female',
  SeniorCitizen: '0',
  Partner: 'Yes',
  Dependents: 'No',
  tenure: '1',
  PhoneService: 'No',
  MultipleLines: 'No phone service',
  InternetService: 'DSL',
  OnlineSecurity: 'No',
  OnlineBackup: 'Yes',
  DeviceProtection: 'No',
  TechSupport: 'No',
  StreamingTV: 'No',
  StreamingMovies: 'No',
  Contract: 'Month-to-month',
  PaperlessBilling: 'Yes',
  PaymentMethod: 'Electronic check',
  MonthlyCharges: '29.85',
  TotalCharges: ' ',
}

describe('canonicalToClientePt', () => {
  it('é o inverso do Adapter i18n da API', () => {
    const cliente = canonicalToClientePt(LINHA_CANONICA)
    expect(cliente).toEqual({
      genero: 'Feminino',
      idoso: 0,
      tem_parceiro: 'Sim',
      tem_dependentes: 'Não',
      meses_permanencia: 1,
      servico_telefone: 'Não',
      multiplas_linhas: 'Sem serviço de telefone',
      servico_internet: 'DSL',
      seguranca_online: 'Não',
      backup_online: 'Sim',
      protecao_dispositivo: 'Não',
      suporte_tecnico: 'Não',
      streaming_tv: 'Não',
      streaming_filmes: 'Não',
      contrato: 'Mensal',
      faturamento_sem_papel: 'Sim',
      metodo_pagamento: 'Cheque eletrônico',
      cobranca_mensal: 29.85,
      cobranca_total: ' ',
    })
  })

  it('retorna null quando a linha não cobre o contrato canônico', () => {
    const incompleta = { ...LINHA_CANONICA, Contract: 'Vitalício' }
    expect(canonicalToClientePt(incompleta)).toBeNull()
  })
})
