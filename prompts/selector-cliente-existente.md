# Tarea: Añadir selector de cliente existente en el Paso 3 del wizard de nueva propuesta

## Contexto del proyecto
- Stack: React 18 + TypeScript + Vite + Tailwind CSS (frontend) / FastAPI + SQLAlchemy (backend)
- Colores de marca: clase `quipux-blue` (azul) — usarla en lugar de `indigo`

## Problema actual
En el paso 3 ("Información del Cliente") de `frontend/src/pages/NewProposalPage.tsx`,
solo existe la opción de CREAR un cliente nuevo a través del componente `<ClientForm>`.
El usuario no puede reutilizar un cliente ya registrado en la base de datos.

## Cambio requerido
Modificar únicamente el **Paso 3** del wizard para ofrecer dos modos mutuamente excluyentes:

1. **"Seleccionar cliente existente"** — modo por defecto
2. **"Crear nuevo cliente"** — modo alternativo

---

## UX esperada

- Al entrar al paso 3, mostrar dos tabs/botones toggle:
  "Seleccionar existente" (activo por defecto) y "Crear nuevo"
- En modo **"Seleccionar existente"**:
  - Hacer un GET a `/api/clients/?skip=0&limit=100` al montar el componente
  - Mostrar un campo de búsqueda tipo texto para filtrar la lista por nombre o entidad
  - Renderizar la lista de clientes como tarjetas o filas clickeables
  - Al hacer clic en un cliente, marcarlo como seleccionado (estado visual) y
    llamar a `setClient(selectedClient)` del padre
  - Si no hay clientes, mostrar el mensaje: _"No hay clientes registrados. Crea uno nuevo."_
  - Mostrar estado de carga mientras se obtiene la lista
- En modo **"Crear nuevo"**:
  - Mostrar el componente `<ClientForm>` existente (sin modificarlo)
  - Al guardar un cliente nuevo, `onClientCreated` hace `setClient(newClient)`
    y vuelve automáticamente al modo "Seleccionar existente" mostrando el cliente creado como seleccionado
- En **ambos modos**: si ya hay un `client` seleccionado, mostrar el banner verde
  existente con botón "Cambiar" (lógica ya implementada en el padre, no tocar)

---

## Archivos a modificar

### 1. `frontend/src/pages/NewProposalPage.tsx`

Solo modificar la sección `{currentStep === 3 && (...)}` (aproximadamente líneas 198–227).
El resto del archivo **NO debe cambiar**.

Agregar estado local dentro del componente para:

```typescript
const [clientMode, setClientMode] = useState<'select' | 'create'>('select')
const [existingClients, setExistingClients] = useState<Client[]>([])
const [clientSearch, setClientSearch] = useState('')
const [loadingClients, setLoadingClients] = useState(false)
```

Cargar clientes cuando `currentStep === 3` con un `useEffect` que dependa de `currentStep`:

```typescript
useEffect(() => {
  if (currentStep === 3) {
    setLoadingClients(true)
    clientApi.list()
      .then(res => setExistingClients(res.data))
      .catch(console.error)
      .finally(() => setLoadingClients(false))
  }
}, [currentStep])
```

> `clientApi` ya está importado en el archivo. El tipo `Client` también. Verificar que estén en los imports y agregarlos si faltara alguno.

### 2. `frontend/src/components/ClientForm.tsx`

**NO modificar este archivo.** Usarlo tal cual con su prop `onClientCreated`.

---

## Comportamiento del filtro de búsqueda

```typescript
const filteredClients = existingClients.filter(c =>
  c.name.toLowerCase().includes(clientSearch.toLowerCase()) ||
  c.entity.toLowerCase().includes(clientSearch.toLowerCase())
)
```

---

## Estructura visual del Paso 3 (cuando `client` es null)

```
┌─────────────────────────────────────────────────┐
│  3  Información del Cliente                      │
│                                                  │
│  [Seleccionar existente] [Crear nuevo]  ← tabs  │
│                                                  │
│  Si modo = 'select':                             │
│  ┌─────────────────────────────────────────┐    │
│  │  🔍 Buscar por nombre o entidad...      │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  • Nombre — Entidad — Ciudad   [✓]      │    │
│  │  • Nombre — Entidad — Ciudad            │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  Si modo = 'create':                             │
│  <ClientForm onClientCreated={...} />            │
└─────────────────────────────────────────────────┘
```

### Datos de cada tarjeta de cliente en la lista

Mostrar por cliente:
- `client.name` (negrita)
- `client.entity`
- `client.city` (opcional)
- `client.email` (opcional)

---

## API disponible (ya implementada — no crear nada nuevo en el backend)

```typescript
// frontend/src/services/api.ts — clientApi
clientApi.list(skip?: number, limit?: number)
// → GET /api/clients/?skip=0&limit=100
// → devuelve Client[] con campos: id, name, position?, entity, department?, city?, email?
```

Tipo `Client` definido en `frontend/src/types/index.ts`:

```typescript
export interface Client {
  id: number
  name: string
  position?: string
  entity: string
  department?: string
  city?: string
  email?: string
}
```

---

## Restricciones importantes

- ❌ No instalar librerías externas nuevas
- ❌ No modificar ningún archivo de backend
- ❌ No modificar `frontend/src/components/ClientForm.tsx`
- ❌ No modificar los tests existentes ni otros componentes
- ✅ Mantener consistencia visual con Tailwind CSS y las clases `quipux-blue` ya usadas en el wizard
- ✅ El botón "Siguiente" del wizard ya valida `client !== null` — no tocarlo
