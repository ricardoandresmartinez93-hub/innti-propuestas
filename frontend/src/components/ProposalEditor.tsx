import React, { useState, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { proposalApi } from '../services/api'

interface ProposalEditorProps {
  proposalId: number
  initialContent: Record<string, string>
}

const SECTIONS = [
  { id: 'context_content', label: 'Contexto' },
  { id: 'scope_content', label: 'Alcance' },
  { id: 'economic_conditions', label: 'Condiciones Económicas' },
  { id: 'payment_terms', label: 'Forma de Pago' },
]

const MenuBar = ({ editor }: { editor: any }) => {
  if (!editor) {
    return null
  }

  return (
    <div className="flex flex-wrap gap-2 p-2 border-b bg-gray-50">
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        disabled={!editor.can().chain().focus().toggleBold().run()}
        className={`px-2 py-1 rounded ${editor.isActive('bold') ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        B
      </button>
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        disabled={!editor.can().chain().focus().toggleItalic().run()}
        className={`px-2 py-1 rounded ${editor.isActive('italic') ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        I
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        className={`px-2 py-1 rounded ${editor.isActive('heading', { level: 1 }) ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        H1
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={`px-2 py-1 rounded ${editor.isActive('heading', { level: 2 }) ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        H2
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        className={`px-2 py-1 rounded ${editor.isActive('heading', { level: 3 }) ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        H3
      </button>
      <button
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={`px-2 py-1 rounded ${editor.isActive('bulletList') ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        • List
      </button>
      <button
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={`px-2 py-1 rounded ${editor.isActive('orderedList') ? 'bg-blue-600 text-white' : 'bg-white border'}`}
      >
        1. List
      </button>
      <button
        onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
        className="px-2 py-1 rounded bg-white border"
      >
        Tabla
      </button>
    </div>
  )
}

const ProposalEditor: React.FC<ProposalEditorProps> = ({ proposalId, initialContent }) => {
  const [activeTab, setActiveTab] = useState(SECTIONS[0].id)
  const [contents, setContents] = useState<Record<string, string>>(initialContent)
  const [isSaving, setIsSaving] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const editor = useEditor({
    extensions: [
      StarterKit,
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    content: initialContent[activeTab] || '',
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      setContents((prev) => ({ ...prev, [activeTab]: html }))
      setHasUnsavedChanges(true)
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl focus:outline-none p-4 min-h-[300px] max-w-none',
      },
    },
  })

  // Update editor content when switching tabs
  useEffect(() => {
    if (editor && activeTab) {
      editor.commands.setContent(contents[activeTab] || '')
    }
  }, [activeTab, editor])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await proposalApi.update(proposalId, contents)
      setHasUnsavedChanges(false)
      alert('Cambios guardados correctamente')
    } catch (error) {
      console.error('Error saving proposal:', error)
      alert('Error al guardar los cambios')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow border overflow-hidden">
      <div className="flex justify-between items-center bg-gray-100 px-4 py-2 border-b">
        <div className="flex space-x-1">
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveTab(section.id)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === section.id
                  ? 'bg-white text-blue-600 border-t border-x border-gray-200'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {section.label}
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
            onClick={handleSave}
            disabled={isSaving || !hasUnsavedChanges}
            className={`px-4 py-2 text-sm font-white rounded shadow ${
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

export default ProposalEditor
