import React, { useState, useEffect } from 'react';
import { 
  CheckSquare, 
  Play, 
  Pause, 
  Check, 
  X, 
  AlertTriangle, 
  RefreshCw, 
  Download, 
  Share2, 
  Film, 
  Layers, 
  FileText,
  Volume2,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Loader2,
  ShieldCheck
} from 'lucide-react';
import { Video, Scene } from '../types';
import { Badge } from '../components/common/Badge';
import { api } from '../services/api';
import { normalizeApiError } from '../utils/errors';
import { getVideoUrl, getThumbnailUrl, resolveMediaUrl, isVideoGenerating, isVideoPendingReview } from '../utils/media';

interface ReviewApprovalsViewProps {
  videos: Video[];
  selectedVideoId?: number | null;
  onRefreshVideos: () => void;
  onNavigate: (tab: any, videoId?: number) => void;
}

export const ReviewApprovalsView: React.FC<ReviewApprovalsViewProps> = ({
  videos,
  selectedVideoId,
  onRefreshVideos,
  onNavigate,
}) => {
  const [activeTab, setActiveTab] = useState<'PENDING' | 'APPROVED' | 'REJECTED' | 'PUBLISHED'>('PENDING');
  
  // Filter videos based on tab
  const pendingVideos = videos.filter(
    (v) =>
      v.status === 'PENDING_APPROVAL' ||
      v.status === 'PENDING_REVIEW' ||
      v.status === 'RENDER_READY' ||
      v.status === 'GENERATED' ||
      v.status === 'QA_PENDING'
  );
  const approvedVideos = videos.filter(
    (v) => v.status === 'APPROVED' || v.status === 'READY_TO_SCHEDULE' || v.status === 'SCHEDULED'
  );
  const rejectedVideos = videos.filter((v) => v.status === 'REJECTED');
  const publishedVideos = videos.filter((v) => v.status === 'PUBLISHED');

  const getFilteredList = () => {
    switch (activeTab) {
      case 'PENDING': return pendingVideos;
      case 'APPROVED': return approvedVideos;
      case 'REJECTED': return rejectedVideos;
      case 'PUBLISHED': return publishedVideos;
      default: return pendingVideos;
    }
  };

  const list = getFilteredList();

  // Current selected video
  const initialVideo = selectedVideoId 
    ? videos.find((v) => v.id === selectedVideoId) || list[0] || videos[0]
    : list[0] || videos[0];

  const [currentVideoId, setCurrentVideoId] = useState<number | null>(initialVideo?.id || null);
  const currentVideo = videos.find((v) => v.id === currentVideoId) || initialVideo;

  // Publishing form state
  const [targetPlatforms, setTargetPlatforms] = useState<string[]>(
    currentVideo?.selected_platforms || ['tiktok', 'youtube']
  );
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Sync selected platforms when currentVideo changes
  useEffect(() => {
    if (currentVideo?.selected_platforms && currentVideo.selected_platforms.length > 0) {
      setTargetPlatforms(currentVideo.selected_platforms);
    }
  }, [currentVideo?.id]);

  // Parse script if json string
  let scriptObj: any = null;
  if (currentVideo?.script) {
    if (typeof currentVideo.script === 'string') {
      try {
        scriptObj = JSON.parse(currentVideo.script);
      } catch (_) {
        scriptObj = { hook: currentVideo.script };
      }
    } else {
      scriptObj = currentVideo.script;
    }
  }

  const scenes: Scene[] = scriptObj?.scenes || [];

  const handleTogglePlatform = (p: string) => {
    if (targetPlatforms.includes(p)) {
      setTargetPlatforms(targetPlatforms.filter((item) => item !== p));
    } else {
      setTargetPlatforms([...targetPlatforms, p]);
    }
  };

  const handleApprove = async () => {
    if (!currentVideo) return;
    if (targetPlatforms.length === 0) {
      setActionError('Please select at least one social media channel.');
      return;
    }

    setIsApproving(true);
    setActionError(null);
    setActionSuccess(null);

    try {
      await api.approveAndPublish(currentVideo.id, {
        selected_platforms: targetPlatforms,
        auto_publish: true,
      });
      setActionSuccess(`Video #${currentVideo.id} approved and dispatched to publishing queue!`);
      onRefreshVideos();
      setTimeout(() => {
        onNavigate('queue');
      }, 1200);
    } catch (err: any) {
      setActionError(normalizeApiError(err, 'Failed to approve video.'));
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!currentVideo) return;
    if (!rejectionReason.trim()) {
      setActionError('Please enter a reason for rejection.');
      return;
    }

    setIsRejecting(true);
    setActionError(null);

    try {
      await api.rejectVideo(currentVideo.id, rejectionReason);
      setShowRejectModal(false);
      setActionSuccess(`Video #${currentVideo.id} marked as rejected.`);
      onRefreshVideos();
    } catch (err: any) {
      setActionError(normalizeApiError(err, 'Failed to reject video.'));
    } finally {
      setIsRejecting(false);
    }
  };

  const currentVideoSrc = getVideoUrl(currentVideo);
  const currentPosterSrc = getThumbnailUrl(currentVideo);
  const isGenerating = isVideoGenerating(currentVideo);
  const isLandscape = currentVideo?.aspect_ratio === '16:9';

  return (
    <div className="space-y-6">
      {/* HEADER & FILTER TABS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">Review & Approvals</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Perform human-in-the-loop validation on generated scripts, audio, visuals, and dispatch to social platforms.
          </p>
        </div>

        {/* Tab pills */}
        <div className="flex items-center gap-2 bg-[#15151B] border border-[#2B2B35] p-1.5 rounded-xl self-start sm:self-auto overflow-x-auto">
          <button
            onClick={() => setActiveTab('PENDING')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'PENDING'
                ? 'bg-[#C62845] text-white shadow-sm'
                : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
            }`}
          >
            <span>Pending Review</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 text-white">
              {pendingVideos.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('APPROVED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'APPROVED'
                ? 'bg-[#C62845] text-white shadow-sm'
                : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
            }`}
          >
            <span>Approved</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 text-white">
              {approvedVideos.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('PUBLISHED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'PUBLISHED'
                ? 'bg-[#C62845] text-white shadow-sm'
                : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
            }`}
          >
            <span>Published</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 text-white">
              {publishedVideos.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('REJECTED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'REJECTED'
                ? 'bg-[#C62845] text-white shadow-sm'
                : 'text-[#A9A4AA] hover:text-[#F7F4F5]'
            }`}
          >
            <span>Rejected</span>
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 text-white">
              {rejectedVideos.length}
            </span>
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="bg-[#112A20] border border-[#1D523B] rounded-xl p-4 text-xs text-[#35C98B] flex items-center gap-2">
          <Check className="w-4 h-4 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionError && (
        <div className="bg-[#2C1418] border border-[#5B2129] rounded-xl p-4 text-xs text-[#E05260] flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span className="whitespace-pre-line">{normalizeApiError(actionError)}</span>
        </div>
      )}

      {/* VIDEO SELECTOR CAROUSEL IF MULTIPLE VIDEOS IN TAB */}
      {list.length > 1 && (
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-3 flex items-center gap-3 overflow-x-auto">
          <span className="text-xs font-bold uppercase tracking-wider text-[#736E76] px-2 flex-shrink-0">
            Select Video:
          </span>
          {list.map((vid) => (
            <button
              key={vid.id}
              onClick={() => setCurrentVideoId(vid.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center gap-2 flex-shrink-0 ${
                currentVideo?.id === vid.id
                  ? 'bg-[#C62845] text-white font-bold'
                  : 'bg-[#1D1D25] text-[#A9A4AA] hover:text-[#F7F4F5] border border-[#2B2B35]'
              }`}
            >
              <span>#{vid.id}</span>
              <span className="max-w-[140px] truncate">{vid.title || vid.topic || 'Untitled'}</span>
            </button>
          ))}
        </div>
      )}

      {!currentVideo ? (
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-16 text-center space-y-3">
          <CheckSquare className="w-12 h-12 text-[#736E76] mx-auto opacity-40" />
          <h3 className="text-base font-bold text-[#F7F4F5]">No videos in {activeTab} stage</h3>
          <p className="text-xs text-[#A9A4AA] max-w-sm mx-auto">
            All videos have been processed or are in another lifecycle stage.
          </p>
        </div>
      ) : (
        /* 2-COLUMN REVIEW LAYOUT MATCHING FIGMA */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT: VIDEO PLAYER CARD (5 Cols) */}
          <div className="lg:col-span-5 bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col items-center justify-between">
            <div className="w-full flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#F7F4F5]">Video Preview</span>
                <span className="text-[11px] font-mono text-[#736E76]">
                  {currentVideo.aspect_ratio || '9:16'}
                </span>
              </div>
              <Badge variant={currentVideo.status} />
            </div>

            {/* Video Container */}
            <div className={`w-full ${isLandscape ? 'aspect-video max-w-full' : 'max-w-[320px] aspect-[9/16]'} bg-black rounded-xl border border-[#2B2B35] relative overflow-hidden flex items-center justify-center group shadow-2xl`}>
              {currentVideoSrc ? (
                <video
                  key={currentVideoSrc}
                  src={currentVideoSrc}
                  controls
                  playsInline
                  preload="metadata"
                  poster={currentPosterSrc || undefined}
                  className="w-full h-full object-contain"
                />
              ) : isGenerating ? (
                <div className="text-center p-6 space-y-3">
                  <Loader2 className="w-10 h-10 text-[#C62845] animate-spin mx-auto" />
                  <div className="text-xs font-bold text-[#F7F4F5]">Video Rendering in Progress</div>
                  <p className="text-[11px] text-[#736E76]">
                    AI visuals, subtitles, and audio composition running in background.
                  </p>
                </div>
              ) : (
                <div className="text-center p-6 space-y-3">
                  <div className="w-16 h-16 rounded-full bg-[#1D1D25] border border-[#2B2B35] flex items-center justify-center mx-auto text-[#C62845]">
                    <Play className="w-8 h-8 fill-[#C62845] ml-1" />
                  </div>
                  <div className="text-xs font-bold text-[#F7F4F5]">No Final Render Yet</div>
                  <p className="text-[11px] text-[#736E76]">
                    Click generate to start the video assembly pipeline.
                  </p>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="w-full mt-6 pt-4 border-t border-[#23232C] flex items-center justify-between">
              <span className="text-xs text-[#736E76]">Format: MP4 H.264 / AAC</span>
              {currentVideoSrc && (
                <a
                  href={currentVideoSrc}
                  download={`video_${currentVideo.id}.mp4`}
                  className="text-xs font-semibold text-[#C62845] hover:text-[#D93655] flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download MP4</span>
                </a>
              )}
            </div>
          </div>

          {/* RIGHT: VIDEO DETAILS, SCENES & APPROVAL (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Metadata Card */}
            <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 space-y-5">
              <div>
                <div className="text-xs font-mono text-[#C62845] mb-1">PROJECT #{currentVideo.id}</div>
                <h2 className="text-xl font-bold text-[#F7F4F5]">
                  {currentVideo.title || currentVideo.topic || 'Untitled Project'}
                </h2>
                <p className="text-xs text-[#A9A4AA] mt-1">
                  {currentVideo.topic}
                </p>
              </div>

              {/* Attributes Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                  <div className="text-[10px] font-bold uppercase text-[#736E76]">Provider</div>
                  <div className="text-xs font-semibold text-[#F7F4F5] capitalize mt-0.5">
                    {currentVideo.visual_provider || 'Local'}
                  </div>
                </div>

                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                  <div className="text-[10px] font-bold uppercase text-[#736E76]">Audience</div>
                  <div className="text-xs font-semibold text-[#F7F4F5] truncate mt-0.5">
                    {currentVideo.target_audience || 'General'}
                  </div>
                </div>

                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                  <div className="text-[10px] font-bold uppercase text-[#736E76]">Created</div>
                  <div className="text-xs font-semibold text-[#F7F4F5] mt-0.5">
                    {new Date(currentVideo.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>

              {/* Script & Scenes breakdown */}
              {scriptObj && (
                <div className="space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-[#A9A4AA]">
                    Script Hook & Structure
                  </div>
                  {scriptObj.hook && (
                    <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-xs text-[#F7F4F5]">
                      <span className="text-[#C62845] font-bold">HOOK: </span>
                      "{scriptObj.hook}"
                    </div>
                  )}

                  {/* Scene cards gallery */}
                  {scenes.length > 0 && (
                    <div className="space-y-2 mt-3">
                      <div className="text-[11px] font-semibold text-[#736E76]">
                        GENERATED SCENES ({scenes.length})
                      </div>
                      <div className="grid grid-cols-1 gap-2 max-h-56 overflow-y-auto pr-1">
                        {scenes.map((sc, i) => (
                          <div key={i} className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-xs flex items-start gap-3">
                            <span className="w-5 h-5 rounded bg-[#2B2B35] text-[#A9A4AA] text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                              {i + 1}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-[#F7F4F5] leading-relaxed">
                                {sc.narration}
                              </p>
                              <div className="text-[10px] text-[#736E76] mt-1 truncate">
                                Prompt: {sc.image_prompt || (sc as any).visual_prompt}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Social Channels Destination Selection */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                  Publishing Channels Destination
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('tiktok')}
                    className={`p-2.5 rounded-lg border flex items-center justify-between transition-all ${
                      targetPlatforms.includes('tiktok')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-black text-white text-[9px] font-bold flex items-center justify-center">TT</span>
                      <span className="text-xs font-semibold">TikTok</span>
                    </div>
                    {targetPlatforms.includes('tiktok') && <Check className="w-3.5 h-3.5 text-[#C62845]" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('youtube')}
                    className={`p-2.5 rounded-lg border flex items-center justify-between transition-all ${
                      targetPlatforms.includes('youtube')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-[#CC0000] text-white text-[9px] font-bold flex items-center justify-center">YT</span>
                      <span className="text-xs font-semibold">Shorts</span>
                    </div>
                    {targetPlatforms.includes('youtube') && <Check className="w-3.5 h-3.5 text-[#C62845]" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('instagram')}
                    className={`p-2.5 rounded-lg border flex items-center justify-between transition-all ${
                      targetPlatforms.includes('instagram')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] text-white text-[9px] font-bold flex items-center justify-center">IG</span>
                      <span className="text-xs font-semibold">Reels</span>
                    </div>
                    {targetPlatforms.includes('instagram') && <Check className="w-3.5 h-3.5 text-[#C62845]" />}
                  </button>
                </div>
              </div>

              {/* ACTION BUTTONS */}
              <div className="pt-4 border-t border-[#23232C] flex items-center justify-between gap-4">
                <button
                  type="button"
                  onClick={() => setShowRejectModal(true)}
                  disabled={isApproving || isRejecting}
                  className="bg-[#2C1418] hover:bg-[#3D1A21] text-[#E05260] border border-[#5B2129] text-xs font-bold px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  <span>Reject Video</span>
                </button>

                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={isApproving || isRejecting}
                  className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-6 py-2.5 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all flex-1 justify-center"
                >
                  <Check className="w-4 h-4" />
                  <span>{isApproving ? 'Approving & Publishing...' : 'Approve & Publish to Channels'}</span>
                </button>
              </div>
            </div>

            {/* Approval Guardrail Notice Card */}
            <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-xl p-4 flex items-start gap-3 text-xs text-[#A9A4AA]">
              <AlertTriangle className="w-5 h-5 text-[#E8A83E] flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#F7F4F5]">Human-in-the-Loop Safeguard: </span>
                Review all audio narration, subtitle timings, and generated visuals carefully before approving. Once approved, the video is instantly queued for automated social publication.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REJECTION MODAL */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-[#F7F4F5]">Reject Video #{currentVideo?.id}</h3>
              <button 
                onClick={() => setShowRejectModal(false)}
                className="text-[#736E76] hover:text-[#F7F4F5]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-[#A9A4AA]">
              Provide feedback for the rejection. The video status will be updated to REJECTED.
            </p>
            <textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Visual pacing is too fast, hook needs revision..."
              className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845]"
            />
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 text-xs font-medium text-[#A9A4AA] hover:text-[#F7F4F5]"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={isRejecting}
                className="bg-[#E05260] hover:bg-[#B83845] text-white text-xs font-bold px-4 py-2 rounded-lg"
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
