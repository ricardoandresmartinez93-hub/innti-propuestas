/**
 * Tipos TypeScript para la aplicación Innti Propuestas.
 */

// --- Portafolio ---
export interface PortfolioProduct {
  name: string
  product_type: string
  description: string
  business_framework: string
  monetization_model: string
  pricing_model: string
  country: string
}

// --- Esquemas ---
export type SchemeType =
  | 'licensing'
  | 'services'
  | 'support_maintenance'
  | 'concession_bpo'
  | 'supply'

export const SCHEME_LABELS: Record<SchemeType, string> = {
  licensing: 'Licenciamiento',
  services: 'Prestación de Servicios',
  support_maintenance: 'Soporte y Mantenimiento',
  concession_bpo: 'Concesión o BPO',
  supply: 'Suministro',
}

// --- Estado de propuesta ---
export type ProposalStatus =
  | 'draft'
  | 'pending_review'
  | 'reviewed'
  | 'pending_vp'
  | 'approved'
  | 'rejected'
  | 'sent_to_client'

export const STATUS_LABELS: Record<ProposalStatus, string> = {
  draft: 'Borrador',
  pending_review: 'En Revisión',
  reviewed: 'Revisada',
  pending_vp: 'Pendiente VP',
  approved: 'Aprobada',
  rejected: 'Rechazada',
  sent_to_client: 'Enviada al Cliente',
}

// --- Cliente ---
export interface Client {
  id: number
  name: string
  position?: string
  entity: string
  country?: string
  department?: string
  city?: string
  email?: string
}

export interface ClientCreate {
  name: string
  position?: string
  entity: string
  country?: string
  department?: string
  city?: string
  email?: string
}

// --- Propuesta ---
export interface ProposalProduct {
  id?: number
  product_name: string
  product_type?: string
  description?: string
  category?: string
}

export interface ProposalScheme {
  id?: number
  scheme_type: SchemeType
  payment_frequency?: string
}

export interface Proposal {
  id: number
  title: string
  code?: string
  status: ProposalStatus
  combine_schemes: boolean
  cover_title?: string
  letter_content?: string
  context_content?: string
  scope_content?: string
  economic_conditions?: string
  payment_terms?: string
  excluded_services?: string
  ip_section?: string
  confidentiality?: string
  client_id: number
  products: ProposalProduct[]
  schemes: ProposalScheme[]
  created_at: string
  updated_at: string
}

export interface ProposalCreate {
  title: string
  code?: string
  client_id: number
  combine_schemes: boolean
  products: Omit<ProposalProduct, 'id'>[]
  schemes: Omit<ProposalScheme, 'id'>[]
}

// --- Aprobaciones ---
export type ApprovalRole = 'reviewer' | 'vp'
export type ApprovalAction = 'approved' | 'rejected'

export interface Approval {
  id: number
  proposal_id: number
  role: ApprovalRole
  approver_name: string
  approver_email?: string
  action: ApprovalAction
  comments?: string
  created_at: string
}

export interface ApproveRequest {
  approver_name: string
  approver_email?: string
  role: ApprovalRole
  action: ApprovalAction // valor siempre 'approved'
  comments?: string
}

export interface RejectRequest {
  approver_name: string
  approver_email?: string
  role: ApprovalRole
  action: ApprovalAction // valor siempre 'rejected'
  comments: string // obligatorio al rechazar
}

export const ROLE_LABELS: Record<ApprovalRole, string> = {
  reviewer: 'Revisora (Ángela)',
  vp: 'VP (Juan Pablo)',
}
