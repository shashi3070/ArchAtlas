import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { ChallengesPage } from './pages/ChallengesPage'
import { ChallengeRunPage } from './pages/ChallengeRunPage'
import { GlossaryPage } from './pages/GlossaryPage'
import { HomePage } from './pages/HomePage'
import { InterviewPage } from './pages/InterviewPage'
import { LabPage } from './pages/LabPage'
import { LoginPage } from './pages/LoginPage'
import { TopicPage } from './pages/TopicPage'
import { TopicsPage } from './pages/TopicsPage'
import { useAuth } from './state/auth'
import { useProgress } from './state/progress'

export default function App() {
  const refresh = useProgress((s) => s.refresh)
  const fetchMe = useAuth((s) => s.fetchMe)
  useEffect(() => {
    void refresh()
    void fetchMe()
  }, [refresh, fetchMe])

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/learn" element={<TopicsPage />} />
          <Route path="/learn/:topicId" element={<TopicPage />} />
          <Route path="/lab" element={<LabPage />} />
          <Route path="/challenges" element={<ChallengesPage />} />
          <Route path="/challenges/:cid" element={<ChallengeRunPage />} />
          <Route path="/interview" element={<InterviewPage />} />
          <Route path="/glossary" element={<GlossaryPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
