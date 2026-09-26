import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Play, 
  Download, 
  Check, 
  RotateCw, 
  ExternalLink, 
  Film, 
  Layers, 
  FileText, 
  Volume2, 
  Calendar, 
  Share2,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Sparkles,
  ShieldCheck,
  X
} from 'lucide-react';
import { Video, VideoPublication, Scene, SocialAccount } from '../types';
import { Badge } from '../components/common/Badge';
import { api } from '../services/api';
import { normalizeApiError } from '../utils/errors';
import { getVideoUrl, getThumbnailUrl, resolveMediaUrl, isVideoGenerating, isVideoPendingReview } from '../utils/media';

interface VideoDetailViewProps {
  videoId: number;
  videos: Video[];
  publications: VideoPublication[];
  onBack: () => void;
  onRefresh: () => void;
  onNavigate: (tab: any, videoId?: number) => void;
}

export const VideoDetailView: React.FC<VideoDetailViewProps> = ({
  videoId,
  videos,
  publications,
  onBack,
  onRefresh,
  onNavigate,
}) => {
  const [video, setVideo] = useState<Video | undefined>(videos.find((v) => v.id === videoId));
  const [videoPubs, setVideoPubs] = useState<VideoPublication[]>(
    publications.filter((p) => p.video_id === videoId)
  );
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);

  // Action states
  const [retryingPlatform, setRetryingPlatform] = useState<string | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  
  // Modals
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['tiktok', 'youtube']);
  const [youtubePrivacy, setYoutubePrivacy] = useState<'public' | 'unlisted' | 'private'>('public');
  const [tiktokPrivacy, setTiktokPrivacy] = useState<'PUBLIC_TO_EVERYONE' | 'SELF_ONLY'>('PUBLIC_TO_EVERYONE');
  const [useSandbox, setUseSandbox] = useState(false);

  // Feedback notifications
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // View tab
  const [activeTab, setActiveTab] = useState<'scenes' | 'script' | 'publications' | 'qa'>('scenes');

  // Keep local video state in sync when parent props update
  useEffect(() => {
    const found = videos.find((v) => v.id === videoId);
    if (found) {
      setVideo(found);
      if (found.selected_platforms && found.selected_platforms.length > 0) {
        setSelectedPlatforms(found.selected_platforms);
      }
    }
    setVideoPubs(publications.filter((p) => p.video_id === videoId));
  }, [videos, publications, videoId]);

  // Fetch social accounts for publishing review modal
  useEffect(() => {
    api.getSocialAccounts().then(setAccounts).catch(() => {});
  }, []);

  // AUTO-POLLING: While the video is generating, processing, or publishing, poll every 2.5s
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    const shouldPoll = 
      video && 
      (isVideoGenerating(video) || 
       video.status === 'PUBLISHING' || 
       video.status === 'DRAFT');

    if (shouldPoll) {
      timer = setInterval(async () => {
        try {
          const [updatedVideo, updatedPubs] = await Promise.all([
            api.getVideo(videoId),
            api.getVideoPublications(videoId).catch(() => []),
          ]);
          setVideo(updatedVideo);
          if (updatedPubs && updatedPubs.length > 0) {
            setVideoPubs(updatedPubs);
          }
          onRefresh();
        } catch {
          // ignore transient poll error
        }
      }, 2500);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [video?.status, videoId, onRefresh]);

  if (!video) {
    return (
      <div className="space-y-6">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-xs text-[#A9A4AA] hover:text-[#F7F4F5] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Videos</span>
        </button>
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-12 text-center text-[#736E76]">
          Video #{videoId} not found in repository.
        </div>
      </div>
    );
  }

  const videoSrc = getVideoUrl(video);
  const posterSrc = getThumbnailUrl(video);
  const generating = isVideoGenerating(video);
  const pendingReview = isVideoPendingReview(video);
  const isLandscape = video.aspect_ratio === '16:9';

  // Parse script if json string
  let scriptObj: any = null;
  if (video.script) {
    if (typeof video.script === 'string') {
      try {
        scriptObj = JSON.parse(video.script);
      } catch (_) {
        scriptObj = { hook: video.script };
      }
    } else {
      scriptObj = video.script;
    }
  }

  const scenes: Scene[] = scriptObj?.scenes || [];

  // Toggle platform in approval modal
  const handleTogglePlatform = (platform: string) => {
    if (selectedPlatforms.includes(platform)) {
      setSelectedPlatforms(selectedPlatforms.filter((p) => p !== platform));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform]);
    }
  };

  // 1. APPROVE & PUBLISH HANDLER
  const handleConfirmApproveAndPublish = async () => {
    if (selectedPlatforms.length === 0) {
      setActionError('Please select at least one social media platform for publishing.');
      return;
    }

    setIsApproving(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      const response = await api.approveAndPublish(video.id, {
        selected_platforms: selectedPlatforms,
        auto_publish: true,
      });

      setShowApproveModal(false);
      setActionSuccess(`Video #${video.id} approved and dispatched to publishing queue!`);
      
      // Update local state immediately
      setVideo((prev) => prev ? { ...prev, status: response.video_status || 'PUBLISHED', selected_platforms: selectedPlatforms } : prev);
      onRefresh();
    } catch (err: any) {
      setActionError(normalizeApiError(err, 'Failed to approve and publish video.'));
    } finally {
      setIsApproving(false);
    }
  };

  // 2. REJECT HANDLER
  const handleConfirmReject = async () => {
    if (!rejectionReason.trim()) {
      setActionError('Please enter a reason for rejecting this video.');
      return;
    }

    setIsRejecting(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      await api.rejectVideo(video.id, rejectionReason.trim());
      setShowRejectModal(false);
      setActionSuccess(`Video #${video.id} marked as rejected.`);
      setVideo((prev) => prev ? { ...prev, status: 'REJECTED', rejection_reason: rejectionReason.trim() } : prev);
      onRefresh();
    } catch (err: any) {
      setActionError(normalizeApiError(err, 'Failed to reject video.'));
    } finally {
      setIsRejecting(false);
    }
  };

  // 3. REGENERATE / RETRY PIPELINE
  const handleRegenerate = async () => {
    setIsRegenerating(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      await api.regenerateVideo(video.id);
      setActionSuccess(`Regeneration started for Video #${video.id}. Live pipeline running...`);
      setVideo((prev) => prev ? { ...prev, status: 'GENERATING', error_message: null } : prev);
      onRefresh();
    } catch (err: any) {
      setActionError(normalizeApiError(err, 'Failed to restart video generation.'));
    } finally {
      setIsRegenerating(false);
    }
  };

  // 4. RETRY SINGLE FAILED PLATFORM PUBLICATION
  const handleRetryPlatform = async (platform: string) => {
    setRetryingPlatform(platform);
    setActionError(null);
    try {
      await api.retryPublication(video.id, platform);
      setActionSuccess(`Retry publishing triggered for ${platform}.`);
      onRefresh();
    } catch (err: any) {
      setActionError(normalizeApiError(err, `Failed to retry publication on ${platform}.`));
    } finally {
      setRetryingPlatform(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* TOP NAVIGATION & ACTION BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button 
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-semibold text-[#A9A4AA] hover:text-[#F7F4F5] transition-colors self-start"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Videos</span>
        </button>

        {/* Dynamic Action Buttons based on Video State */}
        <div className="flex items-center gap-3 self-start sm:self-auto">
          {pendingReview && (
            <>
              <button
                onClick={() => setShowRejectModal(true)}
                className="bg-[#1D1D25] hover:bg-[#2A141A] text-[#E05260] hover:border-[#8E1B32] border border-[#2B2B35] text-xs font-semibold px-4 py-2 rounded-lg transition-all"
              >
                Reject
              </button>
              <button
                onClick={() => setShowApproveModal(true)}
                className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-5 py-2 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Approve & Publish</span>
              </button>
            </>
          )}

          {video.status === 'APPROVED' && (
            <button
              onClick={() => setShowApproveModal(true)}
              className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-5 py-2 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all"
            >
              <Share2 className="w-4 h-4" />
              <span>Publish to Channels</span>
            </button>
          )}

          {(video.status === 'FAILED' || video.status === 'REJECTED') && (
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-2 transition-all shadow-md"
            >
              <RotateCw className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />
              <span>{isRegenerating ? 'Restarting...' : 'Regenerate Video'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ALERT BANNERS */}
      {actionSuccess && (
        <div className="bg-[#112A20] border border-[#1D523B] rounded-xl p-4 text-xs text-[#35C98B] flex items-center gap-2 animate-in fade-in">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionError && (
        <div className="bg-[#2C1418] border border-[#5B2129] rounded-xl p-4 text-xs text-[#E05260] flex items-start gap-2 animate-in fade-in">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span className="whitespace-pre-line">{normalizeApiError(actionError)}</span>
        </div>
      )}

      {/* 2-COLUMN MAIN VIEW */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN: VIDEO PLAYER & METADATA (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col items-center">
            <div className="w-full flex items-center justify-between mb-4">
              <span className="text-xs font-mono font-bold text-[#C62845]">PROJECT #{video.id}</span>
              <Badge variant={video.status} />
            </div>

            {/* VIDEO PLAYER CONTAINER */}
            <div className={`w-full ${isLandscape ? 'aspect-video max-w-full' : 'max-w-[320px] aspect-[9/16]'} bg-black rounded-xl border border-[#2B2B35] relative overflow-hidden flex items-center justify-center shadow-2xl`}>
              {videoSrc ? (
                /* REAL HTML5 VIDEO PLAYER WITH FULL PLAYBACK CONTROLS */
                <video
                  key={videoSrc}
                  src={videoSrc}
                  controls
                  playsInline
                  preload="metadata"
                  poster={posterSrc || undefined}
                  className="w-full h-full object-contain"
                />
              ) : generating ? (
                /* ACTIVE GENERATION PIPELINE STATE */
                <div className="text-center p-6 space-y-4">
                  <Loader2 className="w-10 h-10 mx-auto text-[#C62845] animate-spin" />
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-[#F7F4F5]">Generation in Progress</div>
                    <p className="text-[11px] text-[#A9A4AA]">
                      Your video is being prepared. This page will update automatically.
                    </p>
                  </div>
                  <div className="text-[10px] font-mono text-[#35C98B] bg-[#1D1D25] border border-[#2B2B35] rounded px-3 py-1.5 inline-block">
                    Stage: {video.generation_stage || 'ASSEMBLING ASSETS'}
                  </div>
                </div>
              ) : video.status === 'FAILED' ? (
                /* FAILED STATE */
                <div className="text-center p-6 space-y-2 text-[#E05260]">
                  <AlertTriangle className="w-10 h-10 mx-auto text-[#E05260]" />
                  <div className="text-xs font-bold text-[#F7F4F5]">Generation Failed</div>
                  <p className="text-[10px] text-[#A9A4AA] max-w-xs">{video.error_message || 'Video pipeline encountered an error.'}</p>
                </div>
              ) : (
                /* DRAFT / NO RENDER YET */
                <div className="text-center p-6 space-y-2 text-[#736E76]">
                  <Play className="w-10 h-10 mx-auto text-[#C62845]" />
                  <div className="text-xs font-semibold text-[#F7F4F5]">No Final Render Yet</div>
                  <p className="text-[10px]">Processing in background</p>
                </div>
              )}
            </div>

            {/* DOWNLOAD MP4 LINK */}
            {videoSrc && (
              <a
                href={videoSrc}
                download={`video_${video.id}.mp4`}
                className="w-full mt-4 bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold py-2.5 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Download className="w-4 h-4 text-[#C62845]" />
                <span>Download Final MP4</span>
              </a>
            )}
          </div>

          {/* PROJECT STATS & PIPELINE DETAILS */}
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-5 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[#736E76]">Aspect Ratio:</span>
              <span className="font-semibold text-[#F7F4F5]">{video.aspect_ratio || '9:16'} ({video.resolution || '1080x1920'})</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#736E76]">Visual Engine:</span>
              <span className="text-[#F7F4F5]">{video.visual_provider || 'local'} • {video.visual_style || 'cinematic'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#736E76]">Target Audience:</span>
              <span className="text-[#F7F4F5]">{video.target_audience || 'General'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#736E76]">Created At:</span>
              <span className="text-[#F7F4F5]">{new Date(video.created_at).toLocaleString()}</span>
            </div>
            {video.rejection_reason && (
              <div className="pt-2 border-t border-[#23232C] text-[#E05260]">
                <span className="font-bold">Rejection Note:</span> {video.rejection_reason}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: SCENES, SCRIPT, PUBLICATIONS & QA (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6">
            <h1 className="text-xl font-bold text-[#F7F4F5] mb-2">
              {video.title || video.topic || 'Untitled Project'}
            </h1>
            <p className="text-xs text-[#A9A4AA] mb-6 leading-relaxed">
              {video.topic}
            </p>

            {/* TAB BAR */}
            <div className="flex items-center gap-2 border-b border-[#23232C] pb-3 mb-6 overflow-x-auto">
              <button
                onClick={() => setActiveTab('scenes')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === 'scenes' ? 'bg-[#C62845] text-white' : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Scenes & Imagery ({scenes.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('script')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === 'script' ? 'bg-[#C62845] text-white' : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Script & Narration</span>
              </button>

              <button
                onClick={() => setActiveTab('publications')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === 'publications' ? 'bg-[#C62845] text-white' : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
                }`}
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Publications ({videoPubs.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('qa')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  activeTab === 'qa' ? 'bg-[#C62845] text-white' : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>QA & Integrity</span>
              </button>
            </div>

            {/* TAB 1: SCENES */}
            {activeTab === 'scenes' && (
              <div className="space-y-4">
                {scenes.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#736E76]">
                    No scene breakdowns recorded for this video.
                  </div>
                ) : (
                  scenes.map((sc, i) => {
                    const sceneImgSrc = resolveMediaUrl(sc.image_path || sc.generated_image_path);
                    return (
                      <div key={i} className="bg-[#1D1D25] border border-[#2B2B35] rounded-xl p-4 flex gap-4">
                        <div className="w-24 h-24 rounded-lg bg-[#111116] border border-[#2B2B35] flex-shrink-0 overflow-hidden flex items-center justify-center">
                          {sceneImgSrc ? (
                            <img 
                              src={sceneImgSrc} 
                              alt={`Scene ${i + 1}`} 
                              className="w-full h-full object-cover" 
                            />
                          ) : (
                            <Film className="w-6 h-6 text-[#736E76]" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-[#FF7A93]">Scene {i + 1}</span>
                            <span className="text-[10px] text-[#736E76]">{sc.duration}s</span>
                          </div>
                          <p className="text-xs text-[#F7F4F5] leading-relaxed">
                            {sc.narration}
                          </p>
                          <p className="text-[11px] text-[#736E76] italic">
                            "{sc.image_prompt || (sc as any).visual_prompt}"
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* TAB 2: SCRIPT */}
            {activeTab === 'script' && (
              <div className="space-y-4 text-xs">
                {scriptObj?.hook && (
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4">
                    <div className="font-bold text-[#C62845] mb-1">HOOK</div>
                    <div className="text-[#F7F4F5] leading-relaxed">{scriptObj.hook}</div>
                  </div>
                )}
                {typeof video.script === 'string' && !scriptObj?.hook && (
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4">
                    <div className="font-bold text-[#C62845] mb-1">NARRATION SCRIPT</div>
                    <div className="text-[#F7F4F5] whitespace-pre-wrap leading-relaxed">{video.script}</div>
                  </div>
                )}
                {scriptObj?.cta && (
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4">
                    <div className="font-bold text-[#35C98B] mb-1">CALL TO ACTION (CTA)</div>
                    <div className="text-[#F7F4F5] leading-relaxed">{scriptObj.cta}</div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: PUBLICATIONS */}
            {activeTab === 'publications' && (
              <div className="space-y-3">
                {videoPubs.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#736E76]">
                    No publication records for this project yet.
                  </div>
                ) : (
                  videoPubs.map((pub) => (
                    <div key={pub.id} className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4 flex items-center justify-between text-xs">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-bold capitalize text-[#F7F4F5]">{pub.platform}</span>
                          <Badge variant={pub.status} size="sm" />
                        </div>
                        <div className="text-[11px] text-[#736E76]">
                          Account: {pub.account_handle || pub.account_name || 'Connected Channel'} • Attempts: {pub.attempt_count}
                        </div>
                        {pub.error_message && (
                          <div className="text-[11px] text-[#E05260] mt-1">
                            Error: {pub.error_message}
                          </div>
                        )}
                      </div>

                      <div>
                        {pub.post_url ? (
                          <a
                            href={pub.post_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-[#C62845] hover:bg-[#D93655] text-white px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                          >
                            <span>View Live</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : pub.status === 'FAILED' ? (
                          <button
                            onClick={() => handleRetryPlatform(pub.platform)}
                            disabled={retryingPlatform === pub.platform}
                            className="bg-[#2A141A] text-[#FF7A93] border border-[#8E1B32] px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5"
                          >
                            <RotateCw className={`w-3.5 h-3.5 ${retryingPlatform === pub.platform ? 'animate-spin' : ''}`} />
                            <span>Retry</span>
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* TAB 4: QA & INTEGRITY REPORT */}
            {activeTab === 'qa' && (
              <div className="space-y-4 text-xs">
                {video.qa_report ? (
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-xl p-5 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#F7F4F5]">QA Validation Status:</span>
                      <span className={`font-bold uppercase px-2 py-0.5 rounded text-[11px] ${video.qa_report.passed ? 'bg-[#112A20] text-[#35C98B]' : 'bg-[#2C1418] text-[#E05260]'}`}>
                        {video.qa_report.passed ? 'Passed QA' : 'Failed QA'}
                      </span>
                    </div>

                    {video.qa_report.summary && (
                      <div className="text-[#A9A4AA] bg-[#15151B] p-3 rounded-lg border border-[#2B2B35]">
                        {video.qa_report.summary}
                      </div>
                    )}

                    {video.qa_report.checks && (
                      <div className="space-y-2 pt-2 border-t border-[#2B2B35]">
                        <div className="font-semibold text-[#F7F4F5] mb-2">Automated Checks:</div>
                        {Object.entries(video.qa_report.checks).map(([k, v]) => (
                          <div key={k} className="flex items-center justify-between text-[11px]">
                            <span className="text-[#736E76] capitalize">{k.replace(/_/g, ' ')}:</span>
                            <span className="font-mono text-[#F7F4F5]">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="py-8 text-center text-xs text-[#736E76]">
                    No QA validation report has been recorded yet.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* APPROVE & PUBLISH CONFIRMATION MODAL */}
      {showApproveModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="p-5 border-b border-[#23232C] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#35C98B]" />
                <h3 className="text-base font-bold text-[#F7F4F5]">Approve & Publish Video</h3>
              </div>
              <button 
                onClick={() => setShowApproveModal(false)}
                className="text-[#736E76] hover:text-[#F7F4F5] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5 text-xs">
              <div>
                <div className="font-semibold text-[#F7F4F5] mb-1">Video Title:</div>
                <div className="text-[#A9A4AA] bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                  #{video.id} - {video.title || video.topic}
                </div>
              </div>

              {/* Platform Selector */}
              <div>
                <div className="font-semibold text-[#F7F4F5] mb-2">Target Social Channels:</div>
                <div className="space-y-2">
                  {['tiktok', 'youtube', 'instagram'].map((plat) => {
                    const acc = accounts.find((a) => a.platform.toLowerCase() === plat && a.status === 'ACTIVE');
                    const isSelected = selectedPlatforms.includes(plat);

                    return (
                      <div
                        key={plat}
                        onClick={() => handleTogglePlatform(plat)}
                        className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-[#2A141A] border-[#8E1B32] text-white'
                            : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="font-bold uppercase text-[11px]">{plat}</span>
                          <span className="text-[11px] text-[#A9A4AA]">
                            {acc ? `(${acc.account_handle || acc.account_name})` : '(No Active Account)'}
                          </span>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-[#C62845]" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Privacy Setting */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[#736E76] mb-1 font-semibold">YouTube Privacy</label>
                  <select
                    value={youtubePrivacy}
                    onChange={(e: any) => setYoutubePrivacy(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-2.5 py-1.5 text-xs text-[#F7F4F5]"
                  >
                    <option value="public">Public</option>
                    <option value="unlisted">Unlisted</option>
                    <option value="private">Private</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[#736E76] mb-1 font-semibold">TikTok Privacy</label>
                  <select
                    value={tiktokPrivacy}
                    onChange={(e: any) => setTiktokPrivacy(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-2.5 py-1.5 text-xs text-[#F7F4F5]"
                  >
                    <option value="PUBLIC_TO_EVERYONE">Public</option>
                    <option value="SELF_ONLY">Self Only</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-[#23232C] bg-[#111116] flex items-center justify-between">
              <button
                type="button"
                onClick={() => setShowApproveModal(false)}
                className="text-xs font-semibold text-[#A9A4AA] hover:text-[#F7F4F5]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmApproveAndPublish}
                disabled={isApproving}
                className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-5 py-2.5 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all"
              >
                {isApproving ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                <span>{isApproving ? 'Approving & Publishing...' : 'Confirm Approve & Publish'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT MODAL */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-2xl max-w-md w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="p-5 border-b border-[#23232C] flex items-center justify-between">
              <h3 className="text-base font-bold text-[#F7F4F5]">Reject Video Project</h3>
              <button 
                onClick={() => setShowRejectModal(false)}
                className="text-[#736E76] hover:text-[#F7F4F5] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <p className="text-[#A9A4AA]">
                Please describe what needs to be changed before this video can be approved:
              </p>
              <textarea
                rows={4}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Narration tone needs to be more energetic; scene 2 visual is inaccurate..."
                className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845]"
              />
            </div>

            <div className="p-4 border-t border-[#23232C] bg-[#111116] flex items-center justify-between">
              <button
                type="button"
                onClick={() => setShowRejectModal(false)}
                className="text-xs font-semibold text-[#A9A4AA] hover:text-[#F7F4F5]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmReject}
                disabled={isRejecting}
                className="bg-[#2C1418] hover:bg-[#3D1A20] text-[#E05260] border border-[#5B2129] text-xs font-bold px-4 py-2 rounded-lg transition-colors"
              >
                {isRejecting ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
