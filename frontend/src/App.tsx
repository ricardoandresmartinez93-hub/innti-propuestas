import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import NewProposalPage from './pages/NewProposalPage'
import ProposalListPage from './pages/ProposalListPage'
import ProposalDetailPage from './pages/ProposalDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="proposals" element={<ProposalListPage />} />
        <Route path="proposals/new" element={<NewProposalPage />} />
        <Route path="proposals/:id" element={<ProposalDetailPage />} />
      </Route>
    </Routes>
  )
}

export default App
