import React from 'react';
import { X, Play, Download, ExternalLink } from 'lucide-react';
import { Video } from '../../types';
import { Badge } from './Badge';
import { getVideoUrl, getThumbnailUrl } from '../../utils/media';

interface VideoModalProps {
  video: Video | null;
  onClose: () => void;
  onNavigate: (tab: any, videoId?: number) => void;
}

export const VideoModal: React.FC<VideoModalProps> = ({ video, onClose, onNavigate }) => {
  if (!video) return null;

  const videoSrc = getVideoUrl(video);
  const posterSrc = getThumbnailUrl(video);
  const isLandscape = video.aspect_ratio === '16:9';

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* MODAL HEADER */}
        <div className="p-4 border-b border-[#23232C] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono font-bold text-[#C62845]">#{video.id}</span>
            <h3 className="text-sm font-bold text-[#F7F4F5] max-w-md truncate">
              {video.title || video.topic || 'Video Preview'}
            </h3>
            <Badge variant={video.status} size="sm" />
          </div>
          <button 
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#1D1D25] border border-[#2B2B35] flex items-center justify-center text-[#A9A4AA] hover:text-[#F7F4F5] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* MODAL BODY */}
        <div className="p-6 flex flex-col items-center justify-center bg-[#0B0B0F]">
          <div className={`w-full ${isLandscape ? 'aspect-video max-w-full' : 'max-w-[280px] aspect-[9/16]'} bg-black rounded-xl border border-[#2B2B35] overflow-hidden flex items-center justify-center shadow-2xl relative`}>
            {videoSrc ? (
              <video
                key={videoSrc}
                src={videoSrc}
                controls
                autoPlay
                playsInline
                preload="metadata"
                poster={posterSrc || undefined}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-center p-4 space-y-2 text-[#736E76]">
                <Play className="w-8 h-8 mx-auto text-[#C62845]" />
                <div className="text-xs font-semibold text-[#F7F4F5]">Video Not Rendered Yet</div>
                <p className="text-[10px]">Processing in background</p>
              </div>
            )}
          </div>
        </div>

        {/* MODAL FOOTER */}
        <div className="p-4 border-t border-[#23232C] bg-[#15151B] flex items-center justify-between text-xs">
          <div className="text-[#736E76]">
            {video.visual_provider || 'local'} • {video.visual_style || 'realistic'}
          </div>

          <div className="flex items-center gap-2">
            {videoSrc && (
              <a
                href={videoSrc}
                download={`video_${video.id}.mp4`}
                className="bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors"
              >
                <Download className="w-3.5 h-3.5 text-[#C62845]" />
                <span>Download MP4</span>
              </a>
            )}

            <button
              onClick={() => {
                onClose();
                onNavigate(video.status === 'PENDING_APPROVAL' ? 'reviews' : 'detail', video.id);
              }}
              className="bg-[#C62845] hover:bg-[#D93655] text-white font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-md shadow-[#C62845]/20"
            >
              {video.status === 'PENDING_APPROVAL' ? 'Review & Approve' : 'Open Full Details'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
