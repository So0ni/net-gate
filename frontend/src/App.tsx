import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Profiles from './pages/Profiles'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profiles" element={<Profiles />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
