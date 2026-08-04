const cash = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' })

export function formatAmount(chips, display) {
  return display === 'cash' ? cash.format(chips / 100) : String(chips)
}