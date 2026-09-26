import React, { useState } from 'react';
import { 
  Clock, 
  ExternalLink, 
  Search, 
  Filter, 
  CheckCircle, 
  AlertCircle,
  Play
} from 'lucide-react';
import { VideoPublication, Video } from '../types';
import { Badge } from '../components/common/Badge';

interface PublicationHistoryViewProps {
  publications: VideoPublication[];
  videos: Video[];
  onNavigate: (tab: any, videoId?: number) => void;
  onOpenVideoModal: (video: Video) => void;
}

export const PublicationHistoryView: React.FC<PublicationHistoryViewProps> = ({
  publications,
  videos,
  onNavigate,
  onOpenVideoModal,
}) => {
  const [platformFilter, setPlatformFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredPubs = publications.filter((p) => {
    if (platformFilter !== 'ALL' && p.platform.toLowerCase() !== platformFilter.toLowerCase()) {
      return false;
    }
    if (statusFilter !== 'ALL' && p.status !== statusFilter) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const vid = videos.find(v => v.id === p.video_id);
      const matchTitle = (vid?.title || '').toLowerCase().includes(q);
      const matchTopic = (vid?.topic || '').toLowerCase().includes(q);
      const matchHandle = (p.account_handle || '').toLowerCase().includes(q);
      if (!matchTitle && !matchTopic && !matchHandle) return false;
    }
    return true;
  });

  const getVideo = (id: number) => videos.find(v => v.id === id);

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">Publication History</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Complete audit log of multi-platform post broadcasts and external links.
          </p>
        </div>
      </div>

      {/* FILTERS */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-[10px] font-bold uppercase text-[#736E76] mb-1.5">Platform</label>
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
          >
            <option value="ALL">All Platforms</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-bold uppercase text-[#736E76] mb-1.5">Status</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
          >
            <option value="ALL">All Statuses</option>
            <option value="PUBLISHED">Published</option>
            <option value="FAILED">Failed</option>
            <option value="QUEUED">Queued</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-bold uppercase text-[#736E76] mb-1.5">Search</label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by video title or handle..."
            className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845]"
          />
        </div>
      </div>

      {/* HISTORY TABLE */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#23232C] bg-[#111116] text-[11px] font-bold uppercase tracking-wider text-[#736E76]">
                <th className="py-3 px-6">VIDEO</th>
                <th className="py-3 px-4">PLATFORM</th>
                <th className="py-3 px-4">ACCOUNT</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">PUBLISHED AT</th>
                <th className="py-3 px-6 text-right">EXTERNAL LINK</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#23232C] text-xs">
              {filteredPubs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-[#736E76]">
                    No publication records found.
                  </td>
                </tr>
              ) : (
                filteredPubs.map((pub) => {
                  const vid = getVideo(pub.video_id);
                  return (
                    <tr key={pub.id} className="hover:bg-[#1D1D25] transition-colors">
                      {/* VIDEO */}
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div 
                            onClick={() => vid && onOpenVideoModal(vid)}
                            className="w-12 h-8 rounded bg-[#111116] border border-[#2B2B35] flex items-center justify-center cursor-pointer overflow-hidden flex-shrink-0"
                          >
                            {vid?.thumbnail_path ? (
                              <img 
                                src={`http://127.0.0.1:8000/${vid.thumbnail_path.replace(/^\//, '')}`} 
                                alt="thumb" 
                                className="w-full h-full object-cover" 
                              />
                            ) : (
                              <Play className="w-3.5 h-3.5 text-[#C62845]" />
                            )}
                          </div>
                          <div className="min-w-0 max-w-xs">
                            <div 
                              onClick={() => onNavigate('detail', pub.video_id)}
                              className="font-semibold text-[#F7F4F5] truncate hover:text-[#FF7A93] cursor-pointer"
                            >
                              #{pub.video_id} - {vid?.title || vid?.topic || 'Untitled'}
                            </div>
                            <div className="text-[11px] text-[#736E76] truncate">
                              {vid?.topic}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* PLATFORM */}
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          {pub.platform.toLowerCase() === 'tiktok' && (
                            <span className="w-5 h-5 rounded bg-black text-white text-[9px] font-bold flex items-center justify-center">TT</span>
                          )}
                          {pub.platform.toLowerCase() === 'youtube' && (
                            <span className="w-5 h-5 rounded bg-[#CC0000] text-white text-[9px] font-bold flex items-center justify-center">YT</span>
                          )}
                          {pub.platform.toLowerCase() === 'instagram' && (
                            <span className="w-5 h-5 rounded bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] text-white text-[9px] font-bold flex items-center justify-center">IG</span>
                          )}
                          <span className="capitalize text-[#F7F4F5]">{pub.platform}</span>
                        </div>
                      </td>

                      {/* ACCOUNT */}
                      <td className="py-4 px-4 text-[#A9A4AA]">
                        {pub.account_handle || pub.account_name || 'System Account'}
                      </td>

                      {/* STATUS */}
                      <td className="py-4 px-4">
                        <Badge variant={pub.status} />
                      </td>

                      {/* PUBLISHED AT */}
                      <td className="py-4 px-4 text-[#736E76]">
                        {pub.published_at 
                          ? new Date(pub.published_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
                          : new Date(pub.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </td>

                      {/* LINK */}
                      <td className="py-4 px-6 text-right">
                        {pub.post_url ? (
                          <a
                            href={pub.post_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-[#1D1D25] hover:bg-[#2B2B35] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1.5"
                          >
                            <span>Open Link</span>
                            <ExternalLink className="w-3 h-3 text-[#A9A4AA]" />
                          </a>
                        ) : pub.platform_post_id ? (
                          <span className="font-mono text-[11px] text-[#736E76]">
                            ID: {pub.platform_post_id}
                          </span>
                        ) : (
                          <span className="text-[#736E76]">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
