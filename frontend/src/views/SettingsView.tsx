import React, { useState } from 'react';
import { 
  Settings, 
  Cpu, 
  Film, 
  Share2, 
  ShieldCheck, 
  User, 
  Check, 
  Database,
  Terminal,
  Save,
  Key
} from 'lucide-react';

export const SettingsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'ai' | 'video' | 'social' | 'security' | 'admin'>('general');

  const navItems = [
    { key: 'general', label: 'General', icon: Settings },
    { key: 'ai', label: 'AI Generation', icon: Cpu },
    { key: 'video', label: 'Video Defaults', icon: Film },
    { key: 'social', label: 'Social Publishing', icon: Share2 },
    { key: 'security', label: 'Security & Keys', icon: ShieldCheck },
    { key: 'admin', label: 'Admin & Database', icon: Database },
  ];

  return (
    <div className="space-y-6">
      {/* HEADER */}
      <div>
        <h1 className="text-2xl font-bold text-[#F7F4F5]">Settings & Configuration</h1>
        <p className="text-sm text-[#A9A4AA] mt-1">
          Configure AI provider models, rendering defaults, OAuth callbacks, and system credentials.
        </p>
      </div>

      {/* 2-COLUMN SETTINGS LAYOUT MATCHING FIGMA */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* LEFT VERTICAL TABS */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-3 space-y-1 h-fit">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key as any)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-colors ${
                  isActive
                    ? 'bg-[#C62845] text-white shadow-md shadow-[#C62845]/20'
                    : 'text-[#A9A4AA] hover:text-[#F7F4F5] hover:bg-[#1D1D25]'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* RIGHT SETTINGS PANEL */}
        <div className="md:col-span-3 bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 space-y-6">
          {activeTab === 'general' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">General Settings</h2>
              
              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Studio Project Name</label>
                  <input
                    type="text"
                    defaultValue="AI Video Studio (Production)"
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
                  />
                </div>

                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">FastAPI Backend URL</label>
                  <input
                    type="text"
                    defaultValue="http://127.0.0.1:8000"
                    disabled
                    className="w-full bg-[#111116] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#736E76] font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Admin Human-in-the-Loop Mode</label>
                  <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-[#F7F4F5]">Require Admin Approval Before Publishing</div>
                      <div className="text-[11px] text-[#736E76]">All generated videos pause at PENDING_APPROVAL stage</div>
                    </div>
                    <span className="text-[#35C98B] font-bold text-xs">ACTIVE</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">AI Model Pipelines</h2>
              <div className="space-y-3 text-xs">
                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-[#F7F4F5]">Script LLM Engine</div>
                    <div className="text-[11px] text-[#736E76]">Gemini 1.5 Pro / Flash via Google AI API</div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#112A20] text-[#35C98B] font-semibold text-[11px]">ONLINE</span>
                </div>

                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-[#F7F4F5]">Text-to-Speech (TTS)</div>
                    <div className="text-[11px] text-[#736E76]">Edge-TTS & ElevenLabs Voice Cloning Engine</div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#112A20] text-[#35C98B] font-semibold text-[11px]">READY</span>
                </div>

                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-[#F7F4F5]">Whisper Subtitle Transcriber</div>
                    <div className="text-[11px] text-[#736E76]">OpenAI Whisper Timestamp Sync + MoviePy TextClip</div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#112A20] text-[#35C98B] font-semibold text-[11px]">READY</span>
                </div>

                <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35] flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-[#F7F4F5]">Image Generation Engines</div>
                    <div className="text-[11px] text-[#736E76]">Local Stable Diffusion + Hugging Face FLUX + Replicate SDXL</div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#112A20] text-[#35C98B] font-semibold text-[11px]">READY</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'video' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">Video Defaults</h2>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Default Aspect Ratio</label>
                  <select className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5]">
                    <option value="9:16">9:16 (Vertical Shorts/TikTok)</option>
                    <option value="16:9">16:9 (Horizontal YouTube)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Output Resolution</label>
                  <select className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5]">
                    <option value="1080x1920">1080 x 1920 (Full HD)</option>
                    <option value="720x1280">720 x 1280 (Standard)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Video FPS</label>
                  <select className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5]">
                    <option value="30">30 FPS</option>
                    <option value="60">60 FPS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-2">Video Codec</label>
                  <input
                    type="text"
                    defaultValue="libx264 (AAC Audio)"
                    disabled
                    className="w-full bg-[#111116] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#736E76]"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'social' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">Social Publishing Config</h2>
              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-1">TikTok Desktop Callback URL</label>
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-2 font-mono text-[#35C98B]">
                    http://localhost:8000/social/oauth/callback/tiktok
                  </div>
                </div>
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-1">YouTube OAuth Callback URL</label>
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-2 font-mono text-[#35C98B]">
                    http://localhost:8000/social/oauth/callback/youtube
                  </div>
                </div>
                <div>
                  <label className="block text-[#A9A4AA] font-bold uppercase mb-1">Instagram Callback URL</label>
                  <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-2 font-mono text-[#35C98B]">
                    http://localhost:8000/social/oauth/callback/instagram
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">Security & Encrypted Token Storage</h2>
              <p className="text-xs text-[#A9A4AA]">
                All social access and refresh tokens are AES-256-GCM encrypted in the SQLite database using `ENCRYPTION_KEY`.
              </p>
              <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Encryption Cipher:</span>
                  <span className="font-mono text-[#35C98B]">AES-256-GCM (Fernet)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Token Auto-Refresh:</span>
                  <span className="text-[#35C98B] font-semibold">Enabled (YouTube & TikTok)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Admin Header Auth:</span>
                  <span className="font-mono text-[#F7F4F5]">X-Admin-Role: admin</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'admin' && (
            <div className="space-y-5">
              <h2 className="text-base font-bold text-[#F7F4F5]">Database & System Maintenance</h2>
              <div className="bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-4 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Database File:</span>
                  <span className="font-mono text-[#F7F4F5]">app.db</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Assets Folder:</span>
                  <span className="font-mono text-[#F7F4F5]">/assets</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Engine Status:</span>
                  <span className="text-[#35C98B] font-semibold">● Healthy</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
