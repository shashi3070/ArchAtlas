import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { ChallengesPage } from './pages/ChallengesPage'
import { ChallengeRunPage } from './pages/ChallengeRunPage'
import { GlossaryPage } from './pages/GlossaryPage'
import { HomePage } from './pages/HomePage'
import { LabPage } from './pages/LabPage'
import { TopicPage } from './pages/TopicPage'
import { TopicsPage } from './pages/TopicsPage'
import { useProgress } from './state/progress'

export default function App() {
  const refresh = useProgress((s) => s.refresh)
  useEffect(() => {
    void refresh()
  }, [refresh])

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/learn" element={<TopicsPage />} />
          <Route path="/learn/:topicId" element={<TopicPage />} />
          <Route path="/lab" element={<LabPage />} />
          <Route path="/challenges" element={<ChallengesPage />} />
          <Route path="/challenges/:cid" element={<ChallengeRunPage />} />
          <Route path="/glossary" element={<GlossaryPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
