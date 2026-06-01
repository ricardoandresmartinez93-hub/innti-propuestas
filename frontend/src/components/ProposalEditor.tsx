import { useState, useEffect, useRef, useMemo, useImperativeHandle, forwardRef } from 'react'
import { useEditor, EditorContent, Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import TextAlign from '@tiptap/extension-text-align'
import Highlight from '@tiptap/extension-highlight'
import { Color } from '@tiptap/extension-color'
import TextStyle from '@tiptap/extension-text-style'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import { proposalApi } from '../services/api'
import type { Proposal, ProposalScheme, SchemeType } from '../types'
import { SCHEME_LABELS } from '../types'

interface ProposalEditorProps {
  proposal: Proposal
}

/** Handle expuesto al componente padre mediante forwardRef. */
export interface ProposalEditorHandle {
  /** Guarda el contenido actual en la BD. En modo silencioso no muestra alertas. */
  save: (silent?: boolean) => Promise<void>
  /** True cuando hay cambios pendientes de guardar (globales o por esquema). */
  hasUnsavedChanges: boolean
  /** Reemplaza todo el contenido del editor con datos frescos del servidor. */
  refreshContent: (proposal: Proposal) => void
}

type SectionScope = 'global' | 'scheme'

interface SectionDef {
  id: string
  label: string
  scope: SectionScope
  readOnly: boolean
}

const SECTIONS: SectionDef[] = [
  { id: 'context_content', label: 'Contexto', scope: 'global', readOnly: false },
  { id: 'scope_content', label: 'Alcance', scope: 'scheme', readOnly: false },
  { id: 'validity_period', label: 'Plazo', scope: 'scheme', readOnly: false },
  { id: 'economic_conditions', label: 'Condiciones Económicas', scope: 'scheme', readOnly: false },
  { id: 'payment_terms', label: 'Forma de Pago', scope: 'scheme', readOnly: false },
  { id: 'excluded_services', label: 'Servicios Excluidos', scope: 'scheme', readOnly: false },
  { id: 'ip_section', label: 'Propiedad Intelectual', scope: 'scheme', readOnly: false },
  { id: 'letter_content', label: 'Carta de Presentación', scope: 'global', readOnly: true },
]

const SCHEME_FIELDS = [
  'scope_content',
  'validity_period',
  'economic_conditions',
  'payment_terms',
  'excluded_services',
  'ip_section',
] as const

type SchemeField = (typeof SCHEME_FIELDS)[number]

type GlobalContents = {
  context_content: string
  letter_content: string
}

type SchemeContentMap = Record<number, Record<SchemeField, string>>

function _buildSchemeContents(schemes: ProposalScheme[]): SchemeContentMap {
  const map: SchemeContentMap = {}
  for (const s of schemes) {
    if (s.id == null) continue
    map[s.id] = {
      scope_content: s.scope_content || '',
      validity_period: s.validity_period || '',
      economic_conditions: s.economic_conditions || '',
      payment_terms: s.payment_terms || '',
      excluded_services: s.excluded_services || '',
      ip_section: s.ip_section || '',
    }
  }
  return map
}

const MenuBar = ({ editor }: { editor: Editor | null }) => {
  if (!editor) return null
  const isReadOnly = !editor.isEditable

  const btn = (active: boolean) =>
    `px-2 py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed ${
      active ? 'bg-blue-600 text-white' : 'bg-white border'
    }`

  // Prompt URL for link; empty input removes the link.
  const handleLink = () => {
    const previous = editor.getAttributes('link').href as string | undefined
    const url = window.prompt('URL del enlace (vacío para quitar):', previous ?? '')
    if (url === null) return
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }
    editor
      .chain()
      .focus()
      .extendMarkRange('link')
      .setLink({ href: url, target: '_blank' })
      .run()
  }

  // Clear formatting: if nothing is selected, apply to the whole document.
  // unsetAllMarks/clearNodes only act on the current selection.
  const handleClearFormat = () => {
    const { from, to } = editor.state.selection
    const chain = editor.chain().focus()
    if (from === to) {
      chain.selectAll()
    }
    chain.unsetAllMarks().clearNodes().setTextAlign('left').run()
  }

  const Separator = () => <span className="w-px bg-gray-300 mx-1 self-stretch" />

  return (
    <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-gray-50">
      {/* Grupo 1 — Texto */}
      <button
        type="button"
        title="Negrita"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleBold().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('bold'))}
      >B</button>
      <button
        type="button"
        title="Cursiva"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleItalic().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('italic'))}
      >I</button>
      <button
        type="button"
        title="Subrayado"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleUnderline().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('underline'))}
      >U</button>
      <button
        type="button"
        title="Tachado"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleStrike().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('strike'))}
      >S</button>
      <button
        type="button"
        title="Superíndice"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleSuperscript().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('superscript'))}
      >x²</button>
      <button
        type="button"
        title="Subíndice"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleSubscript().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('subscript'))}
      >x₂</button>

      <Separator />

      {/* Grupo 2 — Encabezados */}
      <button
        type="button"
        title="Encabezado 1"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 1 }).run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('heading', { level: 1 }))}
      >H1</button>
      <button
        type="button"
        title="Encabezado 2"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 2 }).run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('heading', { level: 2 }))}
      >H2</button>
      <button
        type="button"
        title="Encabezado 3"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 3 }).run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('heading', { level: 3 }))}
      >H3</button>
      <button
        type="button"
        title="Párrafo normal"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setParagraph().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('paragraph') && !editor.isActive('heading'))}
      >¶</button>

      <Separator />

      {/* Grupo 3 — Alineación */}
      <button
        type="button"
        title="Alinear a la izquierda"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('left').run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive({ textAlign: 'left' }))}
      >Izq</button>
      <button
        type="button"
        title="Centrar"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('center').run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive({ textAlign: 'center' }))}
      >Cen</button>
      <button
        type="button"
        title="Alinear a la derecha"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('right').run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive({ textAlign: 'right' }))}
      >Der</button>
      <button
        type="button"
        title="Justificar"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('justify').run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive({ textAlign: 'justify' }))}
      >Just</button>

      <Separator />

      {/* Grupo 4 — Listas y bloques */}
      <button
        type="button"
        title="Lista con viñetas"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleBulletList().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('bulletList'))}
      >• List</button>
      <button
        type="button"
        title="Lista numerada"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleOrderedList().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('orderedList'))}
      >1. List</button>
      <button
        type="button"
        title="Cita"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleBlockquote().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('blockquote'))}
      >❝</button>
      <button
        type="button"
        title="Código en línea"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleCode().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('code'))}
      >{'</>'}</button>
      <button
        type="button"
        title="Bloque de código"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().toggleCodeBlock().run() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('codeBlock'))}
      >Code</button>
      <button
        type="button"
        title="Línea horizontal"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().setHorizontalRule().run() }}
        disabled={isReadOnly}
        className={btn(false)}
      >—</button>

      <Separator />

      {/* Grupo 5 — Enlace y color */}
      <button
        type="button"
        title="Insertar/editar enlace"
        onMouseDown={(e) => { e.preventDefault(); handleLink() }}
        disabled={isReadOnly}
        className={btn(editor.isActive('link'))}
      >Link</button>
      <label
        title="Color de texto"
        className={`flex items-center gap-1 px-2 py-1 rounded border bg-white cursor-pointer ${
          isReadOnly ? 'opacity-40 cursor-not-allowed' : ''
        }`}
      >
        <span>Color</span>
        <input
          type="color"
          aria-label="Color de texto"
          disabled={isReadOnly}
          onChange={(e) => editor.chain().focus().setColor(e.target.value).run()}
          className="h-4 w-4 cursor-pointer border-0 bg-transparent p-0"
        />
      </label>
      <label
        title="Color de resaltado"
        className={`flex items-center gap-1 px-2 py-1 rounded border bg-white cursor-pointer ${
          isReadOnly ? 'opacity-40 cursor-not-allowed' : ''
        }`}
      >
        <span>Marca</span>
        <input
          type="color"
          aria-label="Color de resaltado"
          disabled={isReadOnly}
          onChange={(e) => editor.chain().focus().toggleHighlight({ color: e.target.value }).run()}
          className="h-4 w-4 cursor-pointer border-0 bg-transparent p-0"
        />
      </label>

      <Separator />

      {/* Grupo 6 — Tabla */}
      <button
        type="button"
        title="Insertar tabla 3x3"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() }}
        disabled={isReadOnly}
        className={btn(false)}
      >Tabla</button>

      <Separator />

      {/* Grupo 7 — Historia y limpieza */}
      <button
        type="button"
        title="Deshacer"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().undo().run() }}
        disabled={isReadOnly}
        className={btn(false)}
      >↶</button>
      <button
        type="button"
        title="Rehacer"
        onMouseDown={(e) => { e.preventDefault(); editor.chain().focus().redo().run() }}
        disabled={isReadOnly}
        className={btn(false)}
      >↷</button>
      <button
        type="button"
        title="Limpiar formato (si no hay selección, aplica a todo el documento)"
        onMouseDown={(e) => { e.preventDefault(); handleClearFormat() }}
        disabled={isReadOnly}
        className={btn(false)}
      >Limpiar</button>
    </div>
  )
}

const ProposalEditor = forwardRef<ProposalEditorHandle, ProposalEditorProps>(
  function ProposalEditorInner({ proposal }, ref) {
    const [activeTab, setActiveTab] = useState(SECTIONS[0].id)
    const [activeSchemeId, setActiveSchemeId] = useState<number | null>(
      proposal.schemes[0]?.id ?? null
    )
    const [globalContents, setGlobalContents] = useState<GlobalContents>({
      context_content: proposal.context_content || '',
      letter_content: proposal.letter_content || '',
    })
    const [schemeContents, setSchemeContents] = useState<SchemeContentMap>(
      () => _buildSchemeContents(proposal.schemes)
    )
    const [dirtyGlobal, setDirtyGlobal] = useState(false)
    const [dirtySchemes, setDirtySchemes] = useState<Set<number>>(new Set())
    const [isSaving, setIsSaving] = useState(false)

    const activeSection = useMemo(
      () => SECTIONS.find((s) => s.id === activeTab) ?? SECTIONS[0],
      [activeTab]
    )

    // Refs para que el callback onUpdate de TipTap (registrado una sola vez)
    // siempre escriba en la pestaña/esquema activos actuales.
    const activeTabRef = useRef(activeTab)
    const activeSchemeRef = useRef(activeSchemeId)
    useEffect(() => { activeTabRef.current = activeTab }, [activeTab])
    useEffect(() => { activeSchemeRef.current = activeSchemeId }, [activeSchemeId])

    const getActiveContent = (): string => {
      if (activeSection.scope === 'global') {
        return globalContents[activeTab as keyof GlobalContents] || ''
      }
      if (activeSchemeId == null) return ''
      return schemeContents[activeSchemeId]?.[activeTab as SchemeField] || ''
    }

    const editor = useEditor({
      extensions: [
        StarterKit,
        Underline,
        Link.configure({
          openOnClick: false,
          autolink: true,
          HTMLAttributes: { class: 'text-blue-600 underline', rel: 'noopener noreferrer' },
        }),
        TextAlign.configure({ types: ['heading', 'paragraph'] }),
        Highlight.configure({ multicolor: true }),
        TextStyle,
        Color,
        Superscript,
        Subscript,
        Table.configure({ resizable: true }),
        TableRow,
        TableHeader,
        TableCell,
      ],
      content: getActiveContent(),
      onUpdate: ({ editor }) => {
        const html = editor.getHTML()
        const tab = activeTabRef.current
        const section = SECTIONS.find((s) => s.id === tab) ?? SECTIONS[0]
        if (section.scope === 'global') {
          setGlobalContents((prev) => ({ ...prev, [tab]: html }))
          setDirtyGlobal(true)
        } else {
          const sid = activeSchemeRef.current
          if (sid == null) return
          setSchemeContents((prev) => ({
            ...prev,
            [sid]: { ...prev[sid], [tab as SchemeField]: html },
          }))
          setDirtySchemes((prev) => new Set(prev).add(sid))
        }
      },
      editorProps: {
        attributes: {
          class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl focus:outline-none p-4 min-h-[300px] max-w-none',
        },
      },
    })

    // Sincronizar el editor cuando cambia la pestaña o el esquema activo.
    // No incluir `editor` en las deps: el mock de tiptap genera nuevas referencias
    // en cada render y eso causaría un bucle infinito. El editor se asume estable
    // dentro de un mismo mount del componente (el padre usa key={proposal.id-version}
    // para forzar re-mount cuando llega data nueva de Innti).
    useEffect(() => {
      if (!editor) return
      editor.commands.setContent(getActiveContent(), false)
      editor.setEditable(!activeSection.readOnly)
    }, [activeTab, activeSchemeId]) // eslint-disable-line react-hooks/exhaustive-deps

    const handleSave = async (silent = false) => {
      setIsSaving(true)
      try {
        // Globales
        if (dirtyGlobal) {
          await proposalApi.update(proposal.id, globalContents)
        }
        // Por esquema (solo los modificados)
        for (const sid of dirtySchemes) {
          await proposalApi.updateScheme(proposal.id, sid, schemeContents[sid])
        }
        setDirtyGlobal(false)
        setDirtySchemes(new Set())
        if (!silent) alert('Cambios guardados correctamente')
      } catch (error) {
        console.error('Error saving proposal:', error)
        if (!silent) alert('Error al guardar los cambios')
        throw error
      } finally {
        setIsSaving(false)
      }
    }

    const hasUnsavedChanges = dirtyGlobal || dirtySchemes.size > 0

    useImperativeHandle(ref, () => ({
      save: (silent = false) => handleSave(silent),
      hasUnsavedChanges,
      refreshContent: (newProposal: Proposal) => {
        // El useEffect de [proposal, editor] ya re-sincroniza al cambiar el prop;
        // este método queda para invocación imperativa explícita.
        setGlobalContents({
          context_content: newProposal.context_content || '',
          letter_content: newProposal.letter_content || '',
        })
        setSchemeContents(_buildSchemeContents(newProposal.schemes))
        setDirtyGlobal(false)
        setDirtySchemes(new Set())
        if (editor) {
          const tab = activeTabRef.current
          const section = SECTIONS.find((s) => s.id === tab) ?? SECTIONS[0]
          let content = ''
          if (section.scope === 'global') {
            content = (newProposal as any)[tab] || ''
          } else {
            const sid = activeSchemeRef.current
            const sch = sid != null ? newProposal.schemes.find((s) => s.id === sid) : newProposal.schemes[0]
            content = (sch as any)?.[tab] || ''
          }
          editor.commands.setContent(content, false)
          editor.setEditable(!section.readOnly)
        }
      },
    }))

    const showSchemeTabs = activeSection.scope === 'scheme' && proposal.schemes.length > 1

    return (
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        <div className="flex justify-between items-center bg-gray-100 px-4 py-2 border-b">
          <div className="flex space-x-1 overflow-x-auto">
            {SECTIONS.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveTab(section.id)}
                className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${
                  activeTab === section.id
                    ? 'bg-white text-blue-600 border-t border-x border-gray-200'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {section.label}
                {section.scope === 'scheme' && proposal.schemes.length > 1 && (
                  <span className="ml-1 text-[10px] text-blue-500">×{proposal.schemes.length}</span>
                )}
              </button>
            ))}
          </div>
          <div className="flex items-center space-x-4">
            {hasUnsavedChanges && (
              <span className="text-xs font-medium text-orange-600 animate-pulse">
                Cambios sin guardar
              </span>
            )}
            <button
              onClick={() => handleSave()}
              disabled={isSaving || !hasUnsavedChanges}
              className={`px-4 py-2 text-sm font-medium rounded shadow ${
                isSaving || !hasUnsavedChanges
                  ? 'bg-gray-400 cursor-not-allowed text-gray-200'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isSaving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>

        <div className="flex flex-col">
          {showSchemeTabs && (
            <div className="flex items-center space-x-1 px-4 py-2 bg-blue-50 border-b border-blue-100">
              <span className="text-xs font-semibold text-blue-700 mr-2">Esquema:</span>
              {proposal.schemes.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSchemeId(s.id ?? null)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    activeSchemeId === s.id
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-white text-blue-700 border border-blue-200 hover:bg-blue-100'
                  }`}
                >
                  {SCHEME_LABELS[s.scheme_type as SchemeType] || s.scheme_type}
                </button>
              ))}
            </div>
          )}

          {activeSection.readOnly && (
            <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800 flex items-center">
              <span className="mr-2">⚠️</span>
              Esta sección es generada automáticamente por Innti. No se puede editar manualmente.
            </div>
          )}
          {activeSection.scope === 'scheme' && proposal.schemes.length > 1 && (
            <div className="bg-indigo-50 border-b border-indigo-100 px-4 py-2 text-xs text-indigo-800">
              Estás editando el contenido del esquema{' '}
              <strong>
                {SCHEME_LABELS[
                  proposal.schemes.find((s) => s.id === activeSchemeId)?.scheme_type as SchemeType
                ] || ''}
              </strong>
              . Cambia el esquema arriba para editar los demás documentos.
            </div>
          )}
          <MenuBar editor={editor} />
          <div className="border-t bg-white">
            <EditorContent editor={editor} />
          </div>
        </div>

        <style>{`
          .ProseMirror table {
            border-collapse: collapse;
            table-layout: fixed;
            width: 100%;
            margin: 0;
            overflow: hidden;
          }
          .ProseMirror td, .ProseMirror th {
            min-width: 1em;
            border: 2px solid #ced4da;
            padding: 3px 5px;
            vertical-align: top;
            box-sizing: border-box;
            position: relative;
          }
          .ProseMirror th {
            font-weight: bold;
            text-align: left;
            background-color: #f1f3f5;
          }
          .ProseMirror .selectedCell:after {
            z-index: 2;
            position: absolute;
            content: "";
            left: 0; right: 0; top: 0; bottom: 0;
            background: rgba(200, 200, 255, 0.4);
            pointer-events: none;
          }
          .ProseMirror .column-resize-handle {
            position: absolute;
            right: -2px;
            top: 0;
            bottom: -2px;
            width: 4px;
            background-color: #adf;
            pointer-events: none;
          }
        `}</style>
      </div>
    )
  }
)

export default ProposalEditor
