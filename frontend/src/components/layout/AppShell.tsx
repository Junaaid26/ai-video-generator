import React from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  Film, 
  CheckSquare, 
  Share2, 
  ListOrdered, 
  Clock, 
  Settings, 
  Search, 
  Bell, 
  Play, 
  Radio,
  ExternalLink,
  Sparkles
} from 'lucide-react';

export type NavItemKey = 
  | 'dashboard' 
  | 'create' 
  | 'videos' 
  | 'reviews' 
  | 'social' 
  | 'queue' 
  | 'history' 
  | 'settings'
  | 'detail';

interface AppShellProps {
  currentTab: NavItemKey;
  onNavigate: (tab: NavItemKey, videoId?: number) => void;
  pendingReviewCount?: number;
  apiConnected?: boolean;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onNavigate,
  pendingReviewCount = 0,
  apiConnected = true,
  children,
}) => {
  const getBreadcrumbTitle = () => {
    switch (currentTab) {
      case 'dashboard': return 'Dashboard';
      case 'create': return 'Create Video';
      case 'videos': return 'My Videos';
      case 'reviews': return 'Review & Approvals';
      case 'social': return 'Social Accounts';
      case 'queue': return 'Publishing Queue';
      case 'history': return 'Publication History';
      case 'settings': return 'Settings';
      case 'detail': return 'Video Details';
      default: return 'Dashboard';
    }
  };

  const navItemClass = (active: boolean) => `
    flex items-center justify-between w-full px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150
    ${active 
      ? 'bg-[#C62845] text-white shadow-lg shadow-[#C62845]/20 font-semibold' 
      : 'text-[#A9A4AA] hover:text-[#F7F4F5] hover:bg-[#1D1D25]'
    }
  `;

  return (
    <div className="flex min-h-screen bg-[#0B0B0F] text-[#F7F4F5]">
      {/* LEFT SIDEBAR */}
      <aside className="w-64 flex-shrink-0 bg-[#15151B] border-r border-[#2B2B35] flex flex-col justify-between select-none">
        <div>
          {/* LOGO HEADER */}
          <div className="p-5 border-b border-[#23232C] flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#C62845] to-[#8E1B32] flex items-center justify-center shadow-md shadow-[#C62845]/30">
              <Play className="w-4 h-4 text-white fill-white ml-0.5" />
            </div>
            <div>
              <div className="text-xs font-bold tracking-widest text-[#F7F4F5] uppercase leading-none">
                AI VIDEO
              </div>
              <div className="text-[11px] font-black tracking-wider text-[#C62845] uppercase leading-tight">
                STUDIO
              </div>
            </div>
          </div>

          {/* NAV GROUPS */}
          <div className="px-3 py-4 space-y-6">
            {/* GROUP: MAIN */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-[#736E76]">
                MAIN
              </div>
              <nav className="space-y-1">
                <button
                  onClick={() => onNavigate('dashboard')}
                  className={navItemClass(currentTab === 'dashboard')}
                >
                  <div className="flex items-center gap-3">
                    <LayoutDashboard className="w-4 h-4" />
                    <span>Dashboard</span>
                  </div>
                </button>

                <button
                  onClick={() => onNavigate('create')}
                  className={navItemClass(currentTab === 'create')}
                >
                  <div className="flex items-center gap-3">
                    <Sparkles className="w-4 h-4" />
                    <span>Create Video</span>
                  </div>
                </button>

                <button
                  onClick={() => onNavigate('videos')}
                  className={navItemClass(currentTab === 'videos')}
                >
                  <div className="flex items-center gap-3">
                    <Film className="w-4 h-4" />
                    <span>My Videos</span>
                  </div>
                </button>

                <button
                  onClick={() => onNavigate('reviews')}
                  className={navItemClass(currentTab === 'reviews')}
                >
                  <div className="flex items-center gap-3">
                    <CheckSquare className="w-4 h-4" />
                    <span>Review & Approvals</span>
                  </div>
                  {pendingReviewCount > 0 && (
                    <span className={`px-2 py-0.5 text-[11px] font-bold rounded-full ${
                      currentTab === 'reviews' 
                        ? 'bg-white text-[#C62845]' 
                        : 'bg-[#C62845] text-white'
                    }`}>
                      {pendingReviewCount}
                    </span>
                  )}
                </button>
              </nav>
            </div>

            {/* GROUP: PUBLISHING */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-[#736E76]">
                PUBLISHING
              </div>
              <nav className="space-y-1">
                <button
                  onClick={() => onNavigate('social')}
                  className={navItemClass(currentTab === 'social')}
                >
                  <div className="flex items-center gap-3">
                    <Share2 className="w-4 h-4" />
                    <span>Social Accounts</span>
                  </div>
                </button>

                <button
                  onClick={() => onNavigate('queue')}
                  className={navItemClass(currentTab === 'queue')}
                >
                  <div className="flex items-center gap-3">
                    <ListOrdered className="w-4 h-4" />
                    <span>Publishing Queue</span>
                  </div>
                </button>

                <button
                  onClick={() => onNavigate('history')}
                  className={navItemClass(currentTab === 'history')}
                >
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4" />
                    <span>Publication History</span>
                  </div>
                </button>
              </nav>
            </div>

            {/* GROUP: SYSTEM */}
            <div>
              <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-[#736E76]">
                SYSTEM
              </div>
              <nav className="space-y-1">
                <button
                  onClick={() => onNavigate('settings')}
                  className={navItemClass(currentTab === 'settings')}
                >
                  <div className="flex items-center gap-3">
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </div>
                </button>
              </nav>
            </div>
          </div>
        </div>

        {/* BOTTOM SIDEBAR FOOTER */}
        <div className="p-3 border-t border-[#23232C] space-y-3">
          {/* API STATUS CARD */}
          <div className="bg-[#1D1D25] rounded-lg p-2.5 border border-[#2B2B35] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${apiConnected ? 'bg-[#35C98B] shadow-sm shadow-[#35C98B]' : 'bg-[#E05260]'}`} />
              <div className="text-[11px] font-medium text-[#A9A4AA]">
                FastAPI Engine
              </div>
            </div>
            <span className="text-[10px] font-mono text-[#736E76]">
              :8000
            </span>
          </div>

          {/* USER CARD */}
          <div className="flex items-center gap-3 px-2 py-1.5">
            <div className="w-8 h-8 rounded-full bg-[#2A141A] border border-[#8E1B32] text-[#FF7A93] font-bold text-xs flex items-center justify-center">
              AA
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-[#F7F4F5] truncate">
                Authorized Admin
              </div>
              <div className="text-[10px] text-[#736E76] truncate">
                Administrator
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT WRAPPER */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* TOP NAVBAR HEADER */}
        <header className="h-16 bg-[#15151B] border-b border-[#2B2B35] px-8 flex items-center justify-between sticky top-0 z-30">
          {/* BREADCRUMB */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#736E76]">AI Video Studio</span>
            <span className="text-[#736E76]">/</span>
            <span className="font-semibold text-[#F7F4F5]">{getBreadcrumbTitle()}</span>
          </div>

          {/* ACTIONS & SEARCH */}
          <div className="flex items-center gap-4">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#736E76] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search videos and projects..."
                className="w-64 bg-[#1D1D25] border border-[#2B2B35] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845] transition-colors"
              />
            </div>

            {/* Notification Bell */}
            <button className="w-8 h-8 rounded-lg bg-[#1D1D25] border border-[#2B2B35] flex items-center justify-center text-[#A9A4AA] hover:text-[#F7F4F5] transition-colors relative">
              <Bell className="w-4 h-4" />
              {pendingReviewCount > 0 && (
                <span className="w-2 h-2 rounded-full bg-[#C62845] absolute top-1.5 right-1.5" />
              )}
            </button>

            {/* Quick Action Button */}
            {currentTab !== 'create' && (
              <button
                onClick={() => onNavigate('create')}
                className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg flex items-center gap-2 shadow-md shadow-[#C62845]/20 transition-all"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Create Video</span>
              </button>
            )}
          </div>
        </header>

        {/* PAGE CONTENT */}
        <main className="flex-1 p-8 overflow-y-auto max-w-[1600px] w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
