import { describe, it, expect } from 'vitest'
import { COUNTRIES, getDepartments, getCities, LOCATION_DATA } from '../utils/locationData'

describe('locationData', () => {
  it('Colombia es el primer país en la lista', () => {
    expect(COUNTRIES[0]).toBe('Colombia')
  })

  it('COUNTRIES tiene al menos 8 países', () => {
    expect(COUNTRIES.length).toBeGreaterThanOrEqual(8)
  })

  it('getDepartments retorna array vacío para país desconocido', () => {
    expect(getDepartments('Narnia')).toEqual([])
  })

  it('getDepartments retorna los departamentos de Colombia', () => {
    const depts = getDepartments('Colombia')
    expect(depts).toContain('Cundinamarca')
    expect(depts).toContain('Antioquia')
    expect(depts).toContain('Valle del Cauca')
    expect(depts.length).toBeGreaterThanOrEqual(30)
  })

  it('getCities retorna las ciudades de Cundinamarca', () => {
    const cities = getCities('Colombia', 'Cundinamarca')
    expect(cities).toContain('Bogotá D.C.')
    expect(cities).toContain('Soacha')
  })

  it('getCities retorna array vacío para departamento desconocido', () => {
    expect(getCities('Colombia', 'Atlantida')).toEqual([])
  })

  it('getCities retorna array vacío para combinación inválida', () => {
    expect(getCities('', '')).toEqual([])
  })

  it('LOCATION_DATA tiene estructura válida (sin arrays vacíos)', () => {
    for (const country of Object.keys(LOCATION_DATA)) {
      for (const dept of Object.keys(LOCATION_DATA[country])) {
        expect(LOCATION_DATA[country][dept].length).toBeGreaterThan(0)
      }
    }
  })
})
