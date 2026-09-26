import React, { useState } from 'react';
import { 
  Film, 
  Search, 
  Play, 
  PlusCircle, 
  Filter, 
  ArrowUpRight, 
  Eye, 
  CheckSquare,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { Video } from '../types';
import { Badge } from '../components/common/Badge';
import { getThumbnailUrl } from '../utils/media';

interface MyVideosViewProps {
  videos: Video[];
  onNavigate: (tab: any, videoId?: number) => void;
  onOpenVideoModal: (video: Video) => void;
}

export const MyVideosView: React.FC<MyVideosViewProps> = ({
  videos,
  onNavigate,
  onOpenVideoModal,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filterTabs = [
    { key: 'ALL', label: 'All', count: videos.length },
    { key: 'DRAFT', label: 'Draft', count: videos.filter(v => v.status === 'DRAFT').length },
    { key: 'PROCESSING', label: 'Processing', count: videos.filter(v => v.status === 'PROCESSING').length },
    { key: 'PENDING_APPROVAL', label: 'Pending Approval', count: videos.filter(v => v.status === 'PENDING_APPROVAL').length },
    { key: 'APPROVED', label: 'Approved', count: videos.filter(v => v.status === 'APPROVED').length },
    { key: 'PUBLISHED', label: 'Published', count: videos.filter(v => v.status === 'PUBLISHED').length },
    { key: 'FAILED', label: 'Failed', count: videos.filter(v => v.status === 'FAILED' || v.status === 'REJECTED').length },
  ];

  const filteredVideos = videos.filter((video) => {
    // Status filter
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'FAILED' && (video.status === 'FAILED' || video.status === 'REJECTED')) {
        // match
      } else if (video.status !== filterStatus) {
        return false;
      }
    }
    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (video.title || '').toLowerCase().includes(q);
      const matchTopic = (video.topic || '').toLowerCase().includes(q);
      const matchId = video.id.toString() === q;
      if (!matchTitle && !matchTopic && !matchId) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">My Videos</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Browse and manage all generated videos, check pipeline states, and inspect assets.
          </p>
        </div>
        <button
          onClick={() => onNavigate('create')}
          className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Create New Video</span>
        </button>
      </div>

      {/* FILTER TABS & SEARCH BAR */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-4 space-y-4">
        {/* Horizontal Status Pill Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {filterTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilterStatus(tab.key)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors flex items-center gap-2 ${
                filterStatus === tab.key
                  ? 'bg-[#C62845] text-white font-semibold shadow-sm'
                  : 'bg-[#1D1D25] text-[#A9A4AA] hover:text-[#F7F4F5] hover:bg-[#252530] border border-[#2B2B35]'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                filterStatus === tab.key ? 'bg-white/20 text-white' : 'bg-[#2B2B35] text-[#736E76]'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search input */}
        <div className="relative">
          <Search className="w-4 h-4 text-[#736E76] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by title, topic, or video ID..."
            className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg pl-9 pr-4 py-2 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845]"
          />
        </div>
      </div>

      {/* VIDEOS TABLE */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#23232C] bg-[#111116] text-[11px] font-bold uppercase tracking-wider text-[#736E76]">
                <th className="py-3 px-6">VIDEO</th>
                <th className="py-3 px-4">FORMAT / STYLE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">PLATFORMS</th>
                <th className="py-3 px-4">CREATED</th>
                <th className="py-3 px-6 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#23232C] text-xs">
              {filteredVideos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-[#736E76]">
                    No videos match your filter criteria.
                  </td>
                </tr>
              ) : (
                filteredVideos.map((video) => (
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
                        <div className="min-w-0 max-w-sm">
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

                    {/* FORMAT / STYLE */}
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
                        {video.selected_platforms && video.selected_platforms.includes('instagram') && (
                          <span className="w-6 h-6 rounded bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] text-white text-[10px] font-bold flex items-center justify-center" title="Instagram Reels">
                            IG
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
