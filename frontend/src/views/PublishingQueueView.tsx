import React, { useState } from 'react';
import { 
  ListOrdered, 
  RotateCw, 
  CheckCircle, 
  AlertCircle, 
  ExternalLink, 
  Play, 
  RefreshCw,
  Search
} from 'lucide-react';
import { VideoPublication, Video } from '../types';
import { Badge } from '../components/common/Badge';
import { api } from '../services/api';
import { normalizeApiError } from '../utils/errors';

interface PublishingQueueViewProps {
  publications: VideoPublication[];
  videos: Video[];
  onRefresh: () => void;
  onNavigate: (tab: any, videoId?: number) => void;
  onOpenVideoModal: (video: Video) => void;
}

export const PublishingQueueView: React.FC<PublishingQueueViewProps> = ({
  publications,
  videos,
  onRefresh,
  onNavigate,
  onOpenVideoModal,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const filterTabs = [
    { key: 'ALL', label: 'All Jobs', count: publications.length },
    { key: 'QUEUED', label: 'Queued', count: publications.filter(p => p.status === 'QUEUED').length },
    { key: 'PUBLISHING', label: 'Publishing', count: publications.filter(p => p.status === 'PUBLISHING').length },
    { key: 'PUBLISHED', label: 'Published', count: publications.filter(p => p.status === 'PUBLISHED').length },
    { key: 'FAILED', label: 'Failed', count: publications.filter(p => p.status === 'FAILED').length },
  ];

  const filteredPubs = publications.filter((p) => {
    if (filterStatus !== 'ALL' && p.status !== filterStatus) return false;
    return true;
  });

  const handleRetry = async (pub: VideoPublication) => {
    setRetryingId(pub.id);
    setActionMessage(null);
    try {
      await api.retryPublication(pub.video_id, pub.platform);
      setActionMessage(`Publication retry triggered for Video #${pub.video_id} on ${pub.platform}.`);
      onRefresh();
    } catch (err: any) {
      setActionMessage(`Retry failed: ${normalizeApiError(err, 'Failed to retry publication.')}`);
    } finally {
      setRetryingId(null);
    }
  };

  const getVideoForPub = (videoId: number) => {
    return videos.find(v => v.id === videoId);
  };

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">Publishing Queue</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Track multi-platform publishing jobs, check retry attempts, and inspect payload status.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {actionMessage && (
        <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-xl p-4 text-xs text-[#F7F4F5] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-[#35C98B] flex-shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* FILTER TABS */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-4">
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
      </div>

      {/* QUEUE TABLE */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#23232C] bg-[#111116] text-[11px] font-bold uppercase tracking-wider text-[#736E76]">
                <th className="py-3 px-6">VIDEO</th>
                <th className="py-3 px-4">PLATFORM</th>
                <th className="py-3 px-4">ACCOUNT</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">ATTEMPTS</th>
                <th className="py-3 px-4">TIMESTAMP</th>
                <th className="py-3 px-6 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#23232C] text-xs">
              {filteredPubs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#736E76]">
                    No publication items match this filter.
                  </td>
                </tr>
              ) : (
                filteredPubs.map((pub) => {
                  const vid = getVideoForPub(pub.video_id);
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
                            {pub.error_message && (
                              <div className="text-[10px] text-[#E05260] truncate" title={pub.error_message}>
                                Err: {pub.error_message}
                              </div>
                            )}
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
                        {pub.account_handle || pub.account_name || (pub.social_account_id ? `Account #${pub.social_account_id}` : 'Default')}
                      </td>

                      {/* STATUS */}
                      <td className="py-4 px-4">
                        <Badge variant={pub.status} />
                      </td>

                      {/* ATTEMPTS */}
                      <td className="py-4 px-4 text-[#736E76] font-mono">
                        {pub.attempt_count}
                      </td>

                      {/* TIMESTAMP */}
                      <td className="py-4 px-4 text-[#736E76]">
                        {pub.published_at 
                          ? new Date(pub.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
                          : new Date(pub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>

                      {/* ACTIONS */}
                      <td className="py-4 px-6 text-right space-x-2">
                        {pub.status === 'FAILED' && (
                          <button
                            onClick={() => handleRetry(pub)}
                            disabled={retryingId === pub.id}
                            className="bg-[#2A141A] hover:bg-[#381620] text-[#FF7A93] border border-[#8E1B32] text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1.5"
                          >
                            <RotateCw className={`w-3.5 h-3.5 ${retryingId === pub.id ? 'animate-spin' : ''}`} />
                            <span>Retry</span>
                          </button>
                        )}
                        {pub.post_url ? (
                          <a
                            href={pub.post_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-[#1D1D25] hover:bg-[#2B2B35] text-[#F7F4F5] border border-[#2B2B35] text-xs font-medium px-3 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1"
                          >
                            <span>Open Post</span>
                            <ExternalLink className="w-3 h-3 text-[#A9A4AA]" />
                          </a>
                        ) : (
                          <button
                            onClick={() => onNavigate('detail', pub.video_id)}
                            className="bg-[#1D1D25] hover:bg-[#2B2B35] text-[#A9A4AA] hover:text-[#F7F4F5] border border-[#2B2B35] text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                          >
                            Details
                          </button>
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
