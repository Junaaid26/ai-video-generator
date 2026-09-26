import React, { useState } from 'react';
import { 
  Sparkles, 
  Lightbulb, 
  Check, 
  ArrowRight, 
  Loader2, 
  Film, 
  Volume2, 
  Palette, 
  Sliders, 
  Share2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { normalizeApiError } from '../utils/errors';
import { Video } from '../types';

interface CreateVideoViewProps {
  onVideoCreated: (video: Video) => void;
  onCancel: () => void;
  onNavigate: (tab: any, videoId?: number) => void;
}

export const CreateVideoView: React.FC<CreateVideoViewProps> = ({
  onVideoCreated,
  onCancel,
  onNavigate,
}) => {
  // Form State
  const [topic, setTopic] = useState('');
  const [targetAudience, setTargetAudience] = useState('Tech & AI Enthusiasts');
  const [tone, setTone] = useState('engaging');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [visualProvider, setVisualProvider] = useState('local');
  const [visualStyle, setVisualStyle] = useState('cinematic');
  const [platforms, setPlatforms] = useState<string[]>(['tiktok', 'youtube']);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);
  const [createdVideo, setCreatedVideo] = useState<Video | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const steps = [
    { num: '01', title: 'Concept', desc: 'Idea & prompt' },
    { num: '02', title: 'Script', desc: 'LLM generation' },
    { num: '03', title: 'Visuals', desc: 'AI scene art' },
    { num: '04', title: 'Render', desc: 'MoviePy composition' },
    { num: '05', title: 'Review', desc: 'Human approval' },
    { num: '06', title: 'Publish', desc: 'Multi-platform' },
  ];

  const handleTogglePlatform = (p: string) => {
    if (platforms.includes(p)) {
      setPlatforms(platforms.filter(item => item !== p));
    } else {
      setPlatforms([...platforms, p]);
    }
  };

  const handleStartGeneration = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      setErrorMessage('Please enter a video topic or prompt.');
      return;
    }

    setErrorMessage(null);
    setIsGenerating(true);
    setCurrentStep(2);
    setGenerationLogs(['[1/4] Initializing video project in database...']);

    try {
      // 1. Create draft video
      const newVideo = await api.createVideo({
        topic,
        target_audience: targetAudience,
        tone,
        aspect_ratio: aspectRatio,
        visual_style: visualStyle,
        visual_provider: visualProvider,
        selected_platforms: platforms,
      });

      setCreatedVideo(newVideo);
      setGenerationLogs(prev => [
        ...prev, 
        `[1/4] Project #${newVideo.id} created successfully.`,
        '[2/4] Generating script & scene breakdown via Gemini AI agent...'
      ]);

      // 2. Trigger async generation pipeline
      setCurrentStep(3);
      setGenerationLogs(prev => [
        ...prev,
        '[3/4] Triggering background visual generation & TTS audio synthesis...',
      ]);

      const genResult = await api.generateVideo(newVideo.id, {
        visual_provider: visualProvider,
        visual_style: visualStyle,
        selected_platforms: platforms,
      });

      setCurrentStep(4);
      setGenerationLogs(prev => [
        ...prev,
        '[4/4] Video rendering pipeline running in background.',
        'Redirecting to review screen...'
      ]);

      // Notify parent & navigate to review
      setTimeout(() => {
        onVideoCreated(genResult);
        onNavigate('reviews', newVideo.id);
      }, 1200);

    } catch (err: any) {
      console.error('Generation error:', err);
      setErrorMessage(normalizeApiError(err, 'Failed to start video generation.'));
      setIsGenerating(false);
      setCurrentStep(1);
    }
  };

  return (
    <div className="space-y-8">
      {/* 6-STEP STEPPER MATCHING FIGMA */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6">
        <div className="grid grid-cols-6 gap-2 relative">
          {steps.map((step, idx) => {
            const stepNum = idx + 1;
            const isActive = currentStep === stepNum;
            const isCompleted = currentStep > stepNum;

            return (
              <div key={step.num} className="flex flex-col items-center text-center relative group">
                {/* Step Circle */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-200 ${
                  isActive 
                    ? 'bg-[#C62845] text-white shadow-lg shadow-[#C62845]/30 ring-4 ring-[#C62845]/20' 
                    : isCompleted
                    ? 'bg-[#112A20] text-[#35C98B] border border-[#1D523B]'
                    : 'bg-[#1D1D25] text-[#736E76] border border-[#2B2B35]'
                }`}>
                  {isCompleted ? <Check className="w-4 h-4" /> : step.num}
                </div>

                {/* Step Titles */}
                <div className="mt-2.5">
                  <div className={`text-xs font-semibold ${isActive ? 'text-[#F7F4F5]' : isCompleted ? 'text-[#35C98B]' : 'text-[#736E76]'}`}>
                    {step.title}
                  </div>
                  <div className="text-[10px] text-[#736E76] hidden sm:block">
                    {step.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2-COLUMN FORM & TIPS LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT COLUMN: FORM (2 Cols) */}
        <div className="lg:col-span-2 bg-[#15151B] border border-[#2B2B35] rounded-xl p-6">
          <div className="mb-6">
            <h2 className="text-lg font-bold text-[#F7F4F5]">Concept & Strategy</h2>
            <p className="text-xs text-[#A9A4AA]">Define your topic, audience, visual aesthetics, and target channels</p>
          </div>

          {errorMessage && (
            <div className="mb-6 bg-[#2C1418] border border-[#5B2129] rounded-lg p-3 text-xs text-[#E05260] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span className="whitespace-pre-line">{normalizeApiError(errorMessage)}</span>
            </div>
          )}

          {isGenerating ? (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
              <Loader2 className="w-10 h-10 text-[#C62845] animate-spin" />
              <div>
                <h3 className="text-base font-bold text-[#F7F4F5]">Generating Video Assets...</h3>
                <p className="text-xs text-[#A9A4AA] mt-1">
                  Gemini LLM, Visual AI engines, and MoviePy are assembling your project.
                </p>
              </div>
              <div className="w-full max-w-md bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-left font-mono text-[11px] text-[#A9A4AA] space-y-1">
                {generationLogs.map((log, index) => (
                  <div key={index} className="text-[#35C98B]">{log}</div>
                ))}
              </div>
            </div>
          ) : (
            <form onSubmit={handleStartGeneration} className="space-y-6">
              {/* TOPIC / CONCEPT */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                  Topic / Core Prompt <span className="text-[#C62845]">*</span>
                </label>
                <textarea
                  rows={3}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. 5 Mind-Blowing Facts About Deep Space Discoveries That Scientists Can't Explain"
                  className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg p-3 text-sm text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845] transition-colors"
                />
              </div>

              {/* TARGET AUDIENCE & TONE */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                    Target Audience
                  </label>
                  <input
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    placeholder="e.g. Young professionals, gamers, students"
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] placeholder-[#736E76] focus:outline-none focus:border-[#C62845]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                    Tone & Pacing
                  </label>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
                  >
                    <option value="engaging">Engaging & Fast-Paced</option>
                    <option value="educational">Educational & Authoritative</option>
                    <option value="cinematic">Cinematic & Dramatic</option>
                    <option value="humorous">Humorous & Viral</option>
                    <option value="inspiring">Inspiring & Uplifting</option>
                  </select>
                </div>
              </div>

              {/* VISUAL PROVIDER & STYLE */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                    Visual Provider
                  </label>
                  <select
                    value={visualProvider}
                    onChange={(e) => setVisualProvider(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
                  >
                    <option value="local">Local Stable Diffusion</option>
                    <option value="huggingface">HuggingFace FLUX.1</option>
                    <option value="replicate">Replicate SDXL</option>
                    <option value="mock">Fast Mock Engine</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                    Visual Style
                  </label>
                  <select
                    value={visualStyle}
                    onChange={(e) => setVisualStyle(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
                  >
                    <option value="cinematic">Cinematic 4K</option>
                    <option value="realistic">Photorealistic</option>
                    <option value="anime">Anime / Manga</option>
                    <option value="3d-render">3D Cyberpunk / Render</option>
                    <option value="vintage">Vintage Film</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-2">
                    Aspect Ratio
                  </label>
                  <select
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value)}
                    className="w-full bg-[#1D1D25] border border-[#2B2B35] rounded-lg px-3 py-2 text-xs text-[#F7F4F5] focus:outline-none focus:border-[#C62845]"
                  >
                    <option value="9:16">9:16 (Vertical Shorts / Reels)</option>
                    <option value="16:9">16:9 (Landscape YouTube)</option>
                  </select>
                </div>
              </div>

              {/* TARGET PUBLISHING CHANNELS */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#A9A4AA] mb-3">
                  Target Social Channels
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('tiktok')}
                    className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                      platforms.includes('tiktok')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded bg-black text-white text-[10px] font-bold flex items-center justify-center">TT</span>
                      <span className="text-xs font-semibold">TikTok</span>
                    </div>
                    {platforms.includes('tiktok') && <Check className="w-4 h-4 text-[#C62845]" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('youtube')}
                    className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                      platforms.includes('youtube')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded bg-[#CC0000] text-white text-[10px] font-bold flex items-center justify-center">YT</span>
                      <span className="text-xs font-semibold">YouTube Shorts</span>
                    </div>
                    {platforms.includes('youtube') && <Check className="w-4 h-4 text-[#C62845]" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleTogglePlatform('instagram')}
                    className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                      platforms.includes('instagram')
                        ? 'bg-[#2A141A] border-[#8E1B32] text-white shadow-sm'
                        : 'bg-[#1D1D25] border-[#2B2B35] text-[#736E76]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] text-white text-[10px] font-bold flex items-center justify-center">IG</span>
                      <span className="text-xs font-semibold">Instagram Reels</span>
                    </div>
                    {platforms.includes('instagram') && <Check className="w-4 h-4 text-[#C62845]" />}
                  </button>
                </div>
              </div>

              {/* ACTION BUTTONS */}
              <div className="pt-4 border-t border-[#23232C] flex items-center justify-between">
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-4 py-2 text-xs font-medium text-[#A9A4AA] hover:text-[#F7F4F5] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold px-6 py-2.5 rounded-lg flex items-center gap-2 shadow-lg shadow-[#C62845]/25 transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Video (AI Pipeline)</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {/* RIGHT COLUMN: TIPS CARD MATCHING FIGMA (1 Col) */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4 text-[#FF7A93]">
              <Lightbulb className="w-5 h-5" />
              <h3 className="text-sm font-bold text-[#F7F4F5]">Create a stronger concept</h3>
            </div>

            <div className="space-y-4 text-xs text-[#A9A4AA]">
              <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                <div className="font-semibold text-[#F7F4F5] mb-1">🎯 3-Second Hook Rule</div>
                <p className="text-[11px] text-[#736E76]">
                  Start with a shocking stat, question, or bold claim to stop viewers from scrolling past in TikTok & Shorts feeds.
                </p>
              </div>

              <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                <div className="font-semibold text-[#F7F4F5] mb-1">⏱️ 30-50 Second Sweet Spot</div>
                <p className="text-[11px] text-[#736E76]">
                  Videos between 30 and 50 seconds achieve the highest algorithmic completion rates on modern social platforms.
                </p>
              </div>

              <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                <div className="font-semibold text-[#F7F4F5] mb-1">🎬 Multi-Scene Retention</div>
                <p className="text-[11px] text-[#736E76]">
                  The automated pipeline generates 4-6 scene images with dynamic subtitle transitions to maintain visual pacing.
                </p>
              </div>

              <div className="bg-[#1D1D25] p-3 rounded-lg border border-[#2B2B35]">
                <div className="font-semibold text-[#F7F4F5] mb-1">🛡️ Admin Human-in-the-Loop</div>
                <p className="text-[11px] text-[#736E76]">
                  All generated content enters Review & Approvals before any live API publication occurs.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#23232C] text-[11px] text-[#736E76] flex items-center justify-between">
            <span>Powered by Gemini 1.5 Pro</span>
            <span className="text-[#35C98B]">● Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};
