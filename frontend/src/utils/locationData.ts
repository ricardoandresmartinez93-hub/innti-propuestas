interface LocationData {
  [country: string]: {
    [department: string]: string[]
  }
}

export const LOCATION_DATA: LocationData = {
  Colombia: {
    Amazonas: ['Leticia', 'Puerto Nariño'],
    Antioquia: ['Medellín', 'Bello', 'Itagüí', 'Envigado', 'Apartadó', 'Turbo', 'Rionegro', 'Caucasia'],
    Arauca: ['Arauca', 'Saravena', 'Tame'],
    Atlántico: ['Barranquilla', 'Soledad', 'Malambo', 'Sabanalarga'],
    Bolívar: ['Cartagena', 'Magangué', 'Turbaco', 'El Carmen de Bolívar'],
    Boyacá: ['Tunja', 'Duitama', 'Sogamoso', 'Chiquinquirá'],
    Caldas: ['Manizales', 'Villamaría', 'La Dorada', 'Chinchiná'],
    Caquetá: ['Florencia', 'San Vicente del Caguán'],
    Casanare: ['Yopal', 'Aguazul', 'Villanueva'],
    Cauca: ['Popayán', 'Santander de Quilichao', 'Puerto Tejada'],
    Cesar: ['Valledupar', 'Aguachica', 'Codazzi'],
    Chocó: ['Quibdó', 'Istmina', 'Bahía Solano'],
    Córdoba: ['Montería', 'Lorica', 'Sahagún', 'Montelíbano'],
    Cundinamarca: ['Bogotá D.C.', 'Soacha', 'Facatativá', 'Zipaquirá', 'Chía', 'Fusagasugá', 'Mosquera', 'Madrid', 'Funza'],
    Guainía: ['Inírida'],
    Guaviare: ['San José del Guaviare'],
    Huila: ['Neiva', 'Pitalito', 'Garzón', 'La Plata'],
    'La Guajira': ['Riohacha', 'Maicao', 'Uribia'],
    Magdalena: ['Santa Marta', 'Ciénaga', 'Fundación'],
    Meta: ['Villavicencio', 'Acacías', 'Granada'],
    Nariño: ['Pasto', 'Tumaco', 'Ipiales', 'Túquerres'],
    'Norte de Santander': ['Cúcuta', 'Ocaña', 'Pamplona', 'Villa del Rosario'],
    Putumayo: ['Mocoa', 'Puerto Asís'],
    Quindío: ['Armenia', 'Calarcá', 'Montenegro'],
    Risaralda: ['Pereira', 'Dosquebradas', 'Santa Rosa de Cabal'],
    'San Andrés y Providencia': ['San Andrés', 'Providencia'],
    Santander: ['Bucaramanga', 'Floridablanca', 'Girón', 'Piedecuesta', 'Barrancabermeja'],
    Sucre: ['Sincelejo', 'Corozal', 'Sampués'],
    Tolima: ['Ibagué', 'Espinal', 'Melgar', 'Honda'],
    'Valle del Cauca': ['Cali', 'Palmira', 'Buenaventura', 'Buga', 'Tuluá', 'Cartago'],
    Vaupés: ['Mitú'],
    Vichada: ['Puerto Carreño'],
  },
  Ecuador: {
    Pichincha: ['Quito', 'Sangolquí', 'Cayambe'],
    Guayas: ['Guayaquil', 'Samborondón', 'Milagro', 'Durán'],
    Azuay: ['Cuenca', 'Gualaceo'],
    Manabí: ['Manta', 'Portoviejo', 'Chone'],
    'El Oro': ['Machala', 'Santa Rosa', 'Pasaje'],
    Tungurahua: ['Ambato', 'Baños'],
    'Los Ríos': ['Babahoyo', 'Quevedo'],
    Imbabura: ['Ibarra', 'Otavalo'],
    Chimborazo: ['Riobamba', 'Alausí'],
    Loja: ['Loja', 'Catamayo'],
  },
  Venezuela: {
    'Distrito Capital': ['Caracas'],
    Miranda: ['Los Teques', 'Guarenas', 'Guatire'],
    Carabobo: ['Valencia', 'Puerto Cabello'],
    Zulia: ['Maracaibo', 'Cabimas'],
    Lara: ['Barquisimeto', 'Carora'],
    Aragua: ['Maracay', 'La Victoria'],
    Bolívar: ['Ciudad Bolívar', 'Ciudad Guayana'],
    Mérida: ['Mérida', 'El Vigía'],
    Táchira: ['San Cristóbal', 'Táchira'],
  },
  Perú: {
    Lima: ['Lima', 'Callao', 'San Juan de Lurigancho', 'Villa El Salvador'],
    Arequipa: ['Arequipa', 'Mollendo'],
    'La Libertad': ['Trujillo', 'Chimbote'],
    Piura: ['Piura', 'Sullana', 'Talara'],
    Cusco: ['Cusco', 'Sicuani'],
    Lambayeque: ['Chiclayo', 'Lambayeque'],
    Junín: ['Huancayo', 'La Oroya'],
    Áncash: ['Huaraz', 'Chimbote'],
  },
  México: {
    'Ciudad de México': ['Ciudad de México'],
    Jalisco: ['Guadalajara', 'Zapopan', 'Tlaquepaque'],
    'Nuevo León': ['Monterrey', 'San Nicolás de los Garza', 'Guadalupe'],
    'Estado de México': ['Toluca', 'Naucalpan', 'Tlalnepantla'],
    Puebla: ['Puebla', 'Tehuacán'],
    Guanajuato: ['León', 'Guanajuato', 'Salamanca'],
    Veracruz: ['Veracruz', 'Xalapa', 'Coatzacoalcos'],
    Chihuahua: ['Chihuahua', 'Ciudad Juárez'],
    'Baja California': ['Tijuana', 'Mexicali', 'Ensenada'],
    Sonora: ['Hermosillo', 'Ciudad Obregón'],
  },
  Chile: {
    'Región Metropolitana': ['Santiago', 'Puente Alto', 'Maipú', 'La Florida'],
    Valparaíso: ['Valparaíso', 'Viña del Mar', 'Quilpué'],
    Biobío: ['Concepción', 'Talcahuano', 'Chillán'],
    'La Araucanía': ['Temuco', 'Padre Las Casas'],
    Maule: ['Talca', 'Curicó', 'Linares'],
    "O'Higgins": ['Rancagua', 'San Fernando'],
    'Los Lagos': ['Puerto Montt', 'Osorno'],
  },
  Argentina: {
    'Buenos Aires': ['Buenos Aires', 'La Plata', 'Mar del Plata', 'Quilmes'],
    Córdoba: ['Córdoba', 'Villa Carlos Paz', 'Río Cuarto'],
    'Santa Fe': ['Rosario', 'Santa Fe', 'Rafaela'],
    Mendoza: ['Mendoza', 'San Rafael', 'Godoy Cruz'],
    Tucumán: ['San Miguel de Tucumán', 'Yerba Buena'],
    'Entre Ríos': ['Paraná', 'Concordia'],
    Salta: ['Salta', 'Orán'],
    Misiones: ['Posadas', 'Oberá'],
  },
  Panamá: {
    Panamá: ['Ciudad de Panamá', 'San Miguelito', 'Tocumen'],
    Chiriquí: ['David', 'Boquete'],
    Colón: ['Colón', 'Portobelo'],
    Veraguas: ['Santiago'],
  },
  'Costa Rica': {
    'San José': ['San José', 'Desamparados', 'Alajuelita'],
    Alajuela: ['Alajuela', 'San Carlos'],
    Cartago: ['Cartago', 'Turrialba'],
    Heredia: ['Heredia', 'Belén'],
    Guanacaste: ['Liberia', 'Nicoya'],
    Puntarenas: ['Puntarenas', 'Quepos'],
    Limón: ['Limón'],
  },
}

export const COUNTRIES = Object.keys(LOCATION_DATA).sort(
  (a, b) => (a === 'Colombia' ? -1 : b === 'Colombia' ? 1 : a.localeCompare(b))
)

export function getDepartments(country: string): string[] {
  return Object.keys(LOCATION_DATA[country] ?? {}).sort()
}

export function getCities(country: string, department: string): string[] {
  return [...(LOCATION_DATA[country]?.[department] ?? [])].sort()
}
