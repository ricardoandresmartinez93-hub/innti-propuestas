/**
 * Cliente API para comunicación con el backend.
 */
import axios from 'axios'
import type { PortfolioProduct, Proposal, ProposalCreate, Client, ClientCreate } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
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

  generateDocument: (id: number, useInnti = true) =>
    api.post(`/proposals/${id}/generate-document`, null, {
      params: { use_innti: useInnti },
      responseType: 'blob',
    }),

  generateAnnex: (id: number) =>
    api.post(`/proposals/${id}/generate-annex`, null, {
      responseType: 'blob',
    }),
}

export default api
