/**
 * Cliente API para comunicación con el backend.
 */
import axios from 'axios'
import type {
  PortfolioProduct,
  Proposal,
  ProposalCreate,
  Client,
  ClientCreate,
  Approval,
  ApproveRequest,
  RejectRequest,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('innti_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Portafolio ---
export const portfolioApi = {
  listProducts: (search?: string, productType?: string) => {
    const params: Record<string, string> = {}
    if (search) params.search = search
    if (productType) params.product_type = productType
    return api.get<PortfolioProduct[]>('/portfolio/products', { params })
  },

  listProductTypes: () =>
    api.get<string[]>('/portfolio/products/types'),
}

// --- Propuestas ---
export const proposalApi = {
  list: (skip = 0, limit = 50) =>
    api.get<Proposal[]>('/proposals/', { params: { skip, limit } }),

  get: (id: number) =>
    api.get<Proposal>(`/proposals/${id}`),

  create: (data: ProposalCreate) =>
    api.post<Proposal>('/proposals/', data),

  update: (id: number, data: Partial<Proposal>) =>
    api.patch<Proposal>(`/proposals/${id}`, data),

  delete: (id: number) =>
    api.delete(`/proposals/${id}`),

  submitForReview: (id: number) =>
    api.post(`/proposals/${id}/submit-review`),

  approve: (id: number, data: ApproveRequest) =>
    api.post<Approval>(`/proposals/${id}/approve`, data),

  reject: (id: number, data: RejectRequest) =>
    api.post<Approval>(`/proposals/${id}/reject`, data),

  getApprovals: (id: number) =>
    api.get<Approval[]>(`/proposals/${id}/approvals`),

  markSentToClient: (id: number) =>
    api.post(`/proposals/${id}/submit-review`),

  generateDocument: (id: number, useInnti = false) =>
    api.post(`/proposals/${id}/generate-document`, null, {
      params: { use_innti: useInnti },
      responseType: 'blob',
      timeout: 300_000, // 5 min — Innti hace 8+ llamadas secuenciales + generación Word
    }),

  generatePdf: (id: number, useInnti = false) =>
    api.post(`/proposals/${id}/generate-pdf`, null, {
      params: { use_innti: useInnti },
      responseType: 'blob',
      timeout: 300_000,
    }),

  generateAnnex: (id: number) =>
    api.post(`/proposals/${id}/generate-annex`, null, {
      responseType: 'blob',
      timeout: 120_000,
    }),
}

// --- Clientes ---
export const clientApi = {
  list: (skip = 0, limit = 50) =>
    api.get<Client[]>('/clients/', { params: { skip, limit } }),

  get: (id: number) =>
    api.get<Client>(`/clients/${id}`),

  create: (data: ClientCreate) =>
    api.post<Client>('/clients/', data),

  update: (id: number, data: Partial<ClientCreate>) =>
    api.patch<Client>(`/clients/${id}`, data),
}

export default api
