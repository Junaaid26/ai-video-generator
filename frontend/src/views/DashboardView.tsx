import React from 'react';
import { 
  Film, 
  CheckSquare, 
  Share2, 
  CheckCircle, 
  Play, 
  ArrowRight, 
  Sparkles,
  ExternalLink,
  Clock,
  AlertCircle
} from 'lucide-react';
import { Video, SocialAccount, VideoPublication } from '../types';
import { Badge } from '../components/common/Badge';
import { getThumbnailUrl } from '../utils/media';

interface DashboardViewProps {
  videos: Video[];
  accounts: SocialAccount[];
  publications: VideoPublication[];
  onNavigate: (tab: any, videoId?: number) => void;
  onOpenVideoModal: (video: Video) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  videos,
  accounts,
  publications,
  onNavigate,
  onOpenVideoModal,
}) => {
  // Compute real metrics
  const totalVideos = videos.length;
  const pendingReviewVideos = videos.filter(v => v.status === 'PENDING_APPROVAL');
  const publishedVideos = videos.filter(v => v.status === 'PUBLISHED');
  const processingVideos = videos.filter(v => v.status === 'PROCESSING');
  const draftVideos = videos.filter(v => v.status === 'DRAFT');
  const failedVideos = videos.filter(v => v.status === 'FAILED' || v.status === 'REJECTED');
  const approvedVideos = videos.filter(v => v.status === 'APPROVED');

  const activeAccounts = accounts.filter(a => a.status === 'ACTIVE' && !a.is_mock);
  const tiktokAccount = accounts.find(a => a.platform.toLowerCase() === 'tiktok' && a.status === 'ACTIVE');
  const youtubeAccount = accounts.find(a => a.platform.toLowerCase() === 'youtube' && a.status === 'ACTIVE');
  const instagramAccount = accounts.find(a => a.platform.toLowerCase() === 'instagram' && a.status === 'ACTIVE');

  // Distribution calculations
  const totalForBar = Math.max(totalVideos, 1);
  const draftPct = ((draftVideos.length / totalForBar) * 100).toFixed(0);
  const procPct = ((processingVideos.length / totalForBar) * 100).toFixed(0);
  const pendingPct = ((pendingReviewVideos.length / totalForBar) * 100).toFixed(0);
  const approvedPct = ((approvedVideos.length / totalForBar) * 100).toFixed(0);
  const pubPct = ((publishedVideos.length / totalForBar) * 100).toFixed(0);
  const failPct = ((failedVideos.length / totalForBar) * 100).toFixed(0);

  // Recent 6 videos
  const recentVideos = [...videos].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 6);

  return (
    <div className="space-y-8">
      {/* PAGE HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">Dashboard Overview</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Monitor pipeline health, generation performance, and multi-channel publication status.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('create')}
            className="bg-[#C62845] hover:bg-[#D93655] text-white text-sm font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate New Video</span>
          </button>
        </div>
      </div>

      {/* 4 STAT METRIC CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Card 1: Total Videos */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-5 hover:border-[#3A3A48] transition-colors">
          <div className="flex items-center justify-between text-[#A9A4AA] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Videos</span>
            <div className="w-8 h-8 rounded-lg bg-[#1D1D25] flex items-center justify-center text-[#F7F4F5]">
              <Film className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#F7F4F5]">{totalVideos}</div>
          <div className="text-xs text-[#736E76] mt-2">
            Generated projects in database
          </div>
        </div>

        {/* Card 2: Ready for Review */}
        <div 
          onClick={() => onNavigate('reviews')}
          className={`border rounded-xl p-5 cursor-pointer transition-all ${
            pendingReviewVideos.length > 0 
              ? 'bg-[#22161A] border-[#8E1B32] shadow-lg shadow-[#C62845]/10' 
              : 'bg-[#15151B] border-[#2B2B35]'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className={`text-xs font-semibold uppercase tracking-wider ${pendingReviewVideos.length > 0 ? 'text-[#FF7A93]' : 'text-[#A9A4AA]'}`}>
              Ready for Review
            </span>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${pendingReviewVideos.length > 0 ? 'bg-[#C62845] text-white' : 'bg-[#1D1D25] text-[#A9A4AA]'}`}>
              <CheckSquare className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-3xl font-extrabold ${pendingReviewVideos.length > 0 ? 'text-[#FF7A93]' : 'text-[#F7F4F5]'}`}>
            {pendingReviewVideos.length}
          </div>
          <div className="text-xs text-[#A9A4AA] mt-2 flex items-center justify-between">
            <span>Awaiting human approval</span>
            {pendingReviewVideos.length > 0 && <span className="text-[#FF7A93] font-medium flex items-center">Review now →</span>}
          </div>
        </div>

        {/* Card 3: Active Channels */}
        <div 
          onClick={() => onNavigate('social')}
          className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-5 hover:border-[#3A3A48] cursor-pointer transition-colors"
        >
          <div className="flex items-center justify-between text-[#A9A4AA] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Channels</span>
            <div className="w-8 h-8 rounded-lg bg-[#1D1D25] flex items-center justify-center text-[#35C98B]">
              <Share2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#F7F4F5]">
            {activeAccounts.length}
          </div>
          <div className="text-xs text-[#736E76] mt-2">
            TikTok & YouTube connected
          </div>
        </div>

        {/* Card 4: Published Videos */}
        <div 
          onClick={() => onNavigate('history')}
          className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-5 hover:border-[#3A3A48] cursor-pointer transition-colors"
        >
          <div className="flex items-center justify-between text-[#A9A4AA] mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Published Posts</span>
            <div className="w-8 h-8 rounded-lg bg-[#1D1D25] flex items-center justify-center text-[#35C98B]">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-[#F7F4F5]">
            {publications.filter(p => p.status === 'PUBLISHED').length}
          </div>
          <div className="text-xs text-[#736E76] mt-2">
            Across active social channels
          </div>
        </div>
      </div>

      {/* MIDDLE SECTION: LIFECYCLE + CHANNELS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* VIDEO LIFECYCLE DISTRIBUTION (2 Cols) */}
        <div className="lg:col-span-2 bg-[#15151B] border border-[#2B2B35] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-[#F7F4F5]">Video Lifecycle</h2>
              <p className="text-xs text-[#A9A4AA]">Distribution of pipeline stages across all projects</p>
            </div>
            <span className="text-xs font-mono text-[#736E76]">{totalVideos} videos</span>
          </div>

          {/* Segmented Progress Bar */}
          <div className="h-4 w-full bg-[#1D1D25] rounded-full overflow-hidden flex gap-0.5 p-0.5 border border-[#2B2B35] mb-6">
            {draftVideos.length > 0 && (
              <div 
                style={{ width: `${(draftVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#736E76] h-full rounded-l-full transition-all"
                title={`Draft: ${draftVideos.length}`} 
              />
            )}
            {processingVideos.length > 0 && (
              <div 
                style={{ width: `${(processingVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#4A90E2] h-full transition-all"
                title={`Processing: ${processingVideos.length}`} 
              />
            )}
            {pendingReviewVideos.length > 0 && (
              <div 
                style={{ width: `${(pendingReviewVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#E8A83E] h-full transition-all"
                title={`Pending Approval: ${pendingReviewVideos.length}`} 
              />
            )}
            {approvedVideos.length > 0 && (
              <div 
                style={{ width: `${(approvedVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#C62845] h-full transition-all"
                title={`Approved: ${approvedVideos.length}`} 
              />
            )}
            {publishedVideos.length > 0 && (
              <div 
                style={{ width: `${(publishedVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#35C98B] h-full rounded-r-full transition-all"
                title={`Published: ${publishedVideos.length}`} 
              />
            )}
            {failedVideos.length > 0 && (
              <div 
                style={{ width: `${(failedVideos.length / totalForBar) * 100}%` }} 
                className="bg-[#E05260] h-full transition-all"
                title={`Failed/Rejected: ${failedVideos.length}`} 
              />
            )}
          </div>

          {/* Legend Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#736E76]" />
                <span className="text-xs text-[#A9A4AA]">Draft</span>
              </div>
              <span className="text-xs font-bold text-[#F7F4F5]">{draftVideos.length}</span>
            </div>

            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#4A90E2]" />
                <span className="text-xs text-[#A9A4AA]">Processing</span>
              </div>
              <span className="text-xs font-bold text-[#F7F4F5]">{processingVideos.length}</span>
            </div>

            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E8A83E]" />
                <span className="text-xs text-[#A9A4AA]">Pending</span>
              </div>
              <span className="text-xs font-bold text-[#E8A83E]">{pendingReviewVideos.length}</span>
            </div>

            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#C62845]" />
                <span className="text-xs text-[#A9A4AA]">Approved</span>
              </div>
              <span className="text-xs font-bold text-[#F7F4F5]">{approvedVideos.length}</span>
            </div>

            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#35C98B]" />
                <span className="text-xs text-[#A9A4AA]">Published</span>
              </div>
              <span className="text-xs font-bold text-[#35C98B]">{publishedVideos.length}</span>
            </div>

            <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E05260]" />
                <span className="text-xs text-[#A9A4AA]">Failed / Rejected</span>
              </div>
              <span className="text-xs font-bold text-[#E05260]">{failedVideos.length}</span>
            </div>
          </div>
        </div>

        {/* PUBLICATION OVERVIEW (1 Col) */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-[#F7F4F5]">Publication Channels</h2>
              <button 
                onClick={() => onNavigate('social')}
                className="text-xs text-[#C62845] hover:text-[#D93655] font-medium"
              >
                Manage →
              </button>
            </div>

            <div className="space-y-3">
              {/* TikTok Channel Card */}
              <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-black flex items-center justify-center text-white font-black text-xs">
                    TT
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#F7F4F5]">TikTok</div>
                    <div className="text-[11px] text-[#A9A4AA]">
                      {tiktokAccount ? (tiktokAccount.account_handle || tiktokAccount.account_name) : 'Not configured'}
                    </div>
                  </div>
                </div>
                <div>
                  {tiktokAccount ? (
                    <Badge variant="CONNECTED" size="sm" />
                  ) : (
                    <Badge variant="NOT_CONNECTED" size="sm" />
                  )}
                </div>
              </div>

              {/* YouTube Channel Card */}
              <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-[#CC0000] flex items-center justify-center text-white font-bold text-xs">
                    YT
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#F7F4F5]">YouTube Shorts</div>
                    <div className="text-[11px] text-[#A9A4AA]">
                      {youtubeAccount ? (youtubeAccount.account_handle || youtubeAccount.account_name) : 'Not configured'}
                    </div>
                  </div>
                </div>
                <div>
                  {youtubeAccount ? (
                    <Badge variant="CONNECTED" size="sm" />
                  ) : (
                    <Badge variant="NOT_CONNECTED" size="sm" />
                  )}
                </div>
              </div>

              {/* Instagram Channel Card */}
              <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] flex items-center justify-center text-white font-bold text-xs">
                    IG
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#F7F4F5]">Instagram Reels</div>
                    <div className="text-[11px] text-[#A9A4AA]">
                      {instagramAccount ? (instagramAccount.account_handle || instagramAccount.account_name) : 'Disconnected'}
                    </div>
                  </div>
                </div>
                <div>
                  {instagramAccount ? (
                    <Badge variant="CONNECTED" size="sm" />
                  ) : (
                    <Badge variant="NOT_CONNECTED" size="sm" />
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-[#23232C] flex items-center justify-between text-xs text-[#736E76]">
            <span>Real-time OAuth credentials active</span>
            <span className="text-[#35C98B] flex items-center gap-1">● Ready</span>
          </div>
        </div>
      </div>

      {/* RECENT VIDEOS TABLE */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl overflow-hidden">
        <div className="p-6 border-b border-[#2B2B35] flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#F7F4F5]">Recent Videos</h2>
            <p className="text-xs text-[#A9A4AA]">Latest video generations and their publication lifecycle</p>
          </div>
          <button
            onClick={() => onNavigate('videos')}
            className="text-xs font-semibold text-[#C62845] hover:text-[#D93655] flex items-center gap-1"
          >
            <span>View All Videos ({totalVideos})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#23232C] bg-[#111116] text-[11px] font-bold uppercase tracking-wider text-[#736E76]">
                <th className="py-3 px-6">VIDEO</th>
                <th className="py-3 px-4">FORMAT & STYLE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">TARGET PLATFORMS</th>
                <th className="py-3 px-4">CREATED</th>
                <th className="py-3 px-6 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#23232C] text-xs">
              {recentVideos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[#736E76]">
                    No videos created yet. Click "Generate New Video" to start.
                  </td>
                </tr>
              ) : (
                recentVideos.map((video) => (
                  <tr key={video.id} className="hover:bg-[#1D1D25] transition-colors group">
                    {/* VIDEO COLUMN */}
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div 
                          onClick={() => onOpenVideoModal(video)}
                          className="w-16 h-10 rounded-lg bg-[#111116] border border-[#2B2B35] flex items-center justify-center relative group-hover:border-[#C62845] cursor-pointer overflow-hidden flex-shrink-0"
                        >
                          {getThumbnailUrl(video) ? (
                            <img 
                              src={getThumbnailUrl(video)!} 
                              alt="thumb" 
                              className="w-full h-full object-cover" 
                            />
                          ) : (
                            <Play className="w-4 h-4 text-[#C62845] fill-[#C62845]" />
                          )}
                        </div>
                        <div className="min-w-0 max-w-xs">
                          <div 
                            onClick={() => onNavigate('detail', video.id)}
                            className="font-semibold text-[#F7F4F5] truncate hover:text-[#FF7A93] cursor-pointer"
                          >
                            #{video.id} - {video.title || video.topic || 'Untitled Video'}
                          </div>
                          <div className="text-[11px] text-[#736E76] truncate">
                            {video.topic || 'No topic specified'}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* FORMAT & STYLE */}
                    <td className="py-4 px-4 text-[#A9A4AA]">
                      <div className="font-medium text-[#F7F4F5]">{video.aspect_ratio || '9:16'}</div>
                      <div className="text-[11px] text-[#736E76]">
                        {video.visual_provider || 'local'} • {video.visual_style || 'realistic'}
                      </div>
                    </td>

                    {/* STATUS */}
                    <td className="py-4 px-4">
                      <Badge variant={video.status} />
                    </td>

                    {/* PLATFORMS */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1.5">
                        {video.selected_platforms && video.selected_platforms.includes('tiktok') && (
                          <span className="w-6 h-6 rounded bg-black text-white text-[10px] font-bold flex items-center justify-center" title="TikTok">
                            TT
                          </span>
                        )}
                        {video.selected_platforms && video.selected_platforms.includes('youtube') && (
                          <span className="w-6 h-6 rounded bg-[#CC0000] text-white text-[10px] font-bold flex items-center justify-center" title="YouTube Shorts">
                            YT
                          </span>
                        )}
                        {(!video.selected_platforms || video.selected_platforms.length === 0) && (
                          <span className="text-[11px] text-[#736E76]">None</span>
                        )}
                      </div>
                    </td>

                    {/* CREATED */}
                    <td className="py-4 px-4 text-[#736E76]">
                      {new Date(video.created_at).toLocaleDateString()}
                    </td>

                    {/* ACTIONS */}
                    <td className="py-4 px-6 text-right space-x-2">
                      {video.status === 'PENDING_APPROVAL' ? (
                        <button
                          onClick={() => onNavigate('reviews', video.id)}
                          className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
                        >
                          Review & Approve
                        </button>
                      ) : (
                        <button
                          onClick={() => onNavigate('detail', video.id)}
                          className="bg-[#1D1D25] hover:bg-[#2B2B35] text-[#F7F4F5] text-xs font-medium px-3 py-1.5 rounded-lg border border-[#2B2B35] transition-colors"
                        >
                          Open Details
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
