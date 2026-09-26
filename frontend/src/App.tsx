import React, { useState, useEffect } from 'react';
import { AppShell, NavItemKey } from './components/layout/AppShell';
import { DashboardView } from './views/DashboardView';
import { CreateVideoView } from './views/CreateVideoView';
import { MyVideosView } from './views/MyVideosView';
import { ReviewApprovalsView } from './views/ReviewApprovalsView';
import { SocialAccountsView } from './views/SocialAccountsView';
import { PublishingQueueView } from './views/PublishingQueueView';
import { PublicationHistoryView } from './views/PublicationHistoryView';
import { SettingsView } from './views/SettingsView';
import { VideoDetailView } from './views/VideoDetailView';
import { VideoModal } from './components/common/Modal';
import { Video, SocialAccount, VideoPublication } from './types';
import { api } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavItemKey>('dashboard');
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null);
  const [previewVideo, setPreviewVideo] = useState<Video | null>(null);

  // Data state
  const [videos, setVideos] = useState<Video[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [publications, setPublications] = useState<VideoPublication[]>([]);
  const [apiConnected, setApiConnected] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchData = async () => {
    try {
      const [vList, aList, pList] = await Promise.all([
        api.getVideos().catch(() => []),
        api.getSocialAccounts().catch(() => []),
        api.getPublications().catch(() => []),
      ]);
      setVideos(vList);
      setAccounts(aList);
      setPublications(pList);
      setApiConnected(true);
    } catch (err) {
      console.error('Failed to fetch studio data:', err);
      setApiConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Dynamic polling interval: 3s if active background jobs exist, 10s otherwise
    const hasActiveJobs = videos.some(
      (v) =>
        v.status === 'GENERATING' ||
        v.status === 'PROCESSING' ||
        v.status === 'QA_PENDING' ||
        v.status === 'PUBLISHING'
    );
    const interval = hasActiveJobs ? 3000 : 10000;
    const timer = setInterval(fetchData, interval);
    return () => clearInterval(timer);
  }, [videos]);

  const handleNavigate = (tab: NavItemKey, videoId?: number) => {
    setCurrentTab(tab);
    if (videoId !== undefined) {
      setSelectedVideoId(videoId);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const pendingCount = videos.filter(
    (v) =>
      v.status === 'PENDING_APPROVAL' ||
      v.status === 'PENDING_REVIEW' ||
      v.status === 'RENDER_READY' ||
      v.status === 'GENERATED'
  ).length;

  return (
    <AppShell
      currentTab={currentTab}
      onNavigate={handleNavigate}
      pendingReviewCount={pendingCount}
      apiConnected={apiConnected}
    >
      {currentTab === 'dashboard' && (
        <DashboardView
          videos={videos}
          accounts={accounts}
          publications={publications}
          onNavigate={handleNavigate}
          onOpenVideoModal={setPreviewVideo}
        />
      )}

      {currentTab === 'create' && (
        <CreateVideoView
          onVideoCreated={(newVid) => {
            fetchData();
            setSelectedVideoId(newVid.id);
          }}
          onCancel={() => handleNavigate('dashboard')}
          onNavigate={handleNavigate}
        />
      )}

      {currentTab === 'videos' && (
        <MyVideosView
          videos={videos}
          onNavigate={handleNavigate}
          onOpenVideoModal={setPreviewVideo}
        />
      )}

      {currentTab === 'reviews' && (
        <ReviewApprovalsView
          videos={videos}
          selectedVideoId={selectedVideoId}
          onRefreshVideos={fetchData}
          onNavigate={handleNavigate}
        />
      )}

      {currentTab === 'social' && (
        <SocialAccountsView
          accounts={accounts}
          onRefreshAccounts={fetchData}
        />
      )}

      {currentTab === 'queue' && (
        <PublishingQueueView
          publications={publications}
          videos={videos}
          onRefresh={fetchData}
          onNavigate={handleNavigate}
          onOpenVideoModal={setPreviewVideo}
        />
      )}

      {currentTab === 'history' && (
        <PublicationHistoryView
          publications={publications}
          videos={videos}
          onNavigate={handleNavigate}
          onOpenVideoModal={setPreviewVideo}
        />
      )}

      {currentTab === 'settings' && (
        <SettingsView />
      )}

      {currentTab === 'detail' && selectedVideoId && (
        <VideoDetailView
          videoId={selectedVideoId}
          videos={videos}
          publications={publications}
          onBack={() => handleNavigate('videos')}
          onRefresh={fetchData}
          onNavigate={handleNavigate}
        />
      )}

      {/* GLOBAL VIDEO PREVIEW MODAL */}
      <VideoModal
        video={previewVideo}
        onClose={() => setPreviewVideo(null)}
        onNavigate={handleNavigate}
      />
    </AppShell>
  );
}

export default App;
