import React, { useState } from 'react';
import { 
  Share2, 
  Check, 
  ExternalLink, 
  RefreshCw, 
  Trash2, 
  PlusCircle, 
  ShieldCheck, 
  AlertCircle,
  Key
} from 'lucide-react';
import { SocialAccount } from '../types';
import { Badge } from '../components/common/Badge';
import { api } from '../services/api';
import { normalizeApiError } from '../utils/errors';

interface SocialAccountsViewProps {
  accounts: SocialAccount[];
  onRefreshAccounts: () => void;
}

export const SocialAccountsView: React.FC<SocialAccountsViewProps> = ({
  accounts,
  onRefreshAccounts,
}) => {
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const tiktokAccount = accounts.find(a => a.platform.toLowerCase() === 'tiktok' && a.status === 'ACTIVE');
  const youtubeAccount = accounts.find(a => a.platform.toLowerCase() === 'youtube' && a.status === 'ACTIVE');
  const instagramAccount = accounts.find(a => a.platform.toLowerCase() === 'instagram' && a.status === 'ACTIVE');

  const handleConnect = async (platform: string) => {
    setConnectingPlatform(platform);
    setErrorMessage(null);
    try {
      const { authorization_url } = await api.getOAuthUrl(platform);
      if (authorization_url) {
        window.location.href = authorization_url;
      }
    } catch (err: any) {
      setErrorMessage(normalizeApiError(err, `Failed to initiate ${platform} connection.`));
      setConnectingPlatform(null);
    }
  };

  const handleDisconnect = async (accountId: number) => {
    if (!confirm('Are you sure you want to disconnect this social account?')) return;
    try {
      await api.disconnectSocialAccount(accountId);
      onRefreshAccounts();
    } catch (err: any) {
      setErrorMessage(normalizeApiError(err, 'Failed to disconnect account.'));
    }
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F7F4F5]">Social Accounts</h1>
          <p className="text-sm text-[#A9A4AA] mt-1">
            Connect and manage multi-platform distribution channels for automated publishing.
          </p>
        </div>
        <button
          onClick={onRefreshAccounts}
          className="bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Status</span>
        </button>
      </div>

      {errorMessage && (
        <div className="bg-[#2C1418] border border-[#5B2129] rounded-xl p-4 text-xs text-[#E05260] flex items-start gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span className="whitespace-pre-line">{normalizeApiError(errorMessage)}</span>
        </div>
      )}

      {/* 3 PLATFORM CARDS MATCHING FIGMA */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* TIKTOK CARD */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white font-black text-sm">
                  TT
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#F7F4F5]">TikTok</h3>
                  <div className="text-[11px] text-[#736E76]">Content Posting API v2</div>
                </div>
              </div>
              <Badge variant={tiktokAccount ? 'CONNECTED' : 'NOT_CONNECTED'} size="sm" />
            </div>

            <div className="space-y-3 py-4 border-y border-[#23232C] text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Connected User:</span>
                <span className="font-semibold text-[#F7F4F5]">
                  {tiktokAccount ? (tiktokAccount.account_handle || tiktokAccount.account_name) : 'None'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Account Type:</span>
                <span className="text-[#A9A4AA]">
                  {tiktokAccount ? (tiktokAccount.is_mock ? 'Mock Sandbox' : 'Real Account (OAuth)') : 'Not linked'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Direct Post:</span>
                <span className="text-[#35C98B] font-medium">Enabled (Private/Draft)</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-2">
            {tiktokAccount ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleConnect('tiktok')}
                  disabled={connectingPlatform === 'tiktok'}
                  className="flex-1 bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold py-2 rounded-lg transition-colors text-center"
                >
                  {connectingPlatform === 'tiktok' ? 'Connecting...' : 'Reconnect'}
                </button>
                <button
                  onClick={() => handleDisconnect(tiktokAccount.id)}
                  className="bg-[#2C1418] hover:bg-[#3D1A21] text-[#E05260] border border-[#5B2129] text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => handleConnect('tiktok')}
                disabled={connectingPlatform === 'tiktok'}
                className="w-full bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold py-2 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md shadow-[#C62845]/20"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Connect TikTok</span>
              </button>
            )}
          </div>
        </div>

        {/* YOUTUBE CARD */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#CC0000] flex items-center justify-center text-white font-bold text-sm">
                  YT
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#F7F4F5]">YouTube Shorts</h3>
                  <div className="text-[11px] text-[#736E76]">YouTube Data API v3</div>
                </div>
              </div>
              <Badge variant={youtubeAccount ? 'CONNECTED' : 'NOT_CONNECTED'} size="sm" />
            </div>

            <div className="space-y-3 py-4 border-y border-[#23232C] text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Channel:</span>
                <span className="font-semibold text-[#F7F4F5]">
                  {youtubeAccount ? (youtubeAccount.account_name || youtubeAccount.account_handle) : 'None'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Account Type:</span>
                <span className="text-[#A9A4AA]">
                  {youtubeAccount ? (youtubeAccount.is_mock ? 'Mock Channel' : 'Real Google OAuth') : 'Not linked'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Token Refresh:</span>
                <span className="text-[#35C98B] font-medium">Auto-Refresh Active</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-2">
            {youtubeAccount ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleConnect('youtube')}
                  disabled={connectingPlatform === 'youtube'}
                  className="flex-1 bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold py-2 rounded-lg transition-colors text-center"
                >
                  {connectingPlatform === 'youtube' ? 'Connecting...' : 'Reconnect'}
                </button>
                <button
                  onClick={() => handleDisconnect(youtubeAccount.id)}
                  className="bg-[#2C1418] hover:bg-[#3D1A21] text-[#E05260] border border-[#5B2129] text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => handleConnect('youtube')}
                disabled={connectingPlatform === 'youtube'}
                className="w-full bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold py-2 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md shadow-[#C62845]/20"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Connect YouTube</span>
              </button>
            )}
          </div>
        </div>

        {/* INSTAGRAM CARD */}
        <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#FD1D1D] to-[#E1306C] flex items-center justify-center text-white font-bold text-sm">
                  IG
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#F7F4F5]">Instagram Reels</h3>
                  <div className="text-[11px] text-[#736E76]">Instagram Graph API</div>
                </div>
              </div>
              <Badge variant={instagramAccount ? 'CONNECTED' : 'NOT_CONNECTED'} size="sm" />
            </div>

            <div className="space-y-3 py-4 border-y border-[#23232C] text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Instagram:</span>
                <span className="font-semibold text-[#F7F4F5]">
                  {instagramAccount ? (instagramAccount.account_handle || instagramAccount.account_name) : 'None'}
                </span>
              </div>
              {instagramAccount?.metadata_json?.page_name && (
                <div className="flex items-center justify-between">
                  <span className="text-[#736E76]">Facebook Page:</span>
                  <span className="text-[#A9A4AA] font-medium">
                    {instagramAccount.metadata_json.page_name}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Account Type:</span>
                <span className="text-[#A9A4AA]">
                  {instagramAccount ? (instagramAccount.is_mock ? 'Mock Account' : 'Real Meta OAuth') : 'Not linked'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#736E76]">Reels Publishing:</span>
                <span className="text-[#A9A4AA]">Single-container video</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-2">
            {instagramAccount ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleConnect('instagram')}
                  disabled={connectingPlatform === 'instagram'}
                  className="flex-1 bg-[#1D1D25] hover:bg-[#252530] text-[#F7F4F5] border border-[#2B2B35] text-xs font-semibold py-2 rounded-lg transition-colors text-center"
                >
                  Reconnect
                </button>
                <button
                  onClick={() => handleDisconnect(instagramAccount.id)}
                  className="bg-[#2C1418] hover:bg-[#3D1A21] text-[#E05260] border border-[#5B2129] text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => handleConnect('instagram')}
                disabled={connectingPlatform === 'instagram'}
                className="w-full bg-[#C62845] hover:bg-[#D93655] text-white text-xs font-bold py-2 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md shadow-[#C62845]/20"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Connect Instagram</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* CONNECTED ACCOUNTS TABLE */}
      <div className="bg-[#15151B] border border-[#2B2B35] rounded-xl overflow-hidden">
        <div className="p-6 border-b border-[#2B2B35]">
          <h2 className="text-base font-bold text-[#F7F4F5]">Configured Social Accounts</h2>
          <p className="text-xs text-[#A9A4AA]">All active and mock social accounts currently registered in database</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#23232C] bg-[#111116] text-[11px] font-bold uppercase tracking-wider text-[#736E76]">
                <th className="py-3 px-6">ACCOUNT</th>
                <th className="py-3 px-4">PLATFORM</th>
                <th className="py-3 px-4">TYPE</th>
                <th className="py-3 px-4">STATUS</th>
                <th className="py-3 px-4">CREATED</th>
                <th className="py-3 px-6 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#23232C] text-xs">
              {accounts.map((acc) => (
                <tr key={acc.id} className="hover:bg-[#1D1D25] transition-colors">
                  <td className="py-4 px-6 font-semibold text-[#F7F4F5]">
                    {acc.account_name} {acc.account_handle ? `(${acc.account_handle})` : ''}
                  </td>
                  <td className="py-4 px-4 capitalize text-[#A9A4AA]">
                    {acc.platform}
                  </td>
                  <td className="py-4 px-4">
                    <Badge variant={acc.is_mock ? 'SANDBOX' : 'REAL'} size="sm" />
                  </td>
                  <td className="py-4 px-4">
                    <Badge variant={acc.status} size="sm" />
                  </td>
                  <td className="py-4 px-4 text-[#736E76]">
                    {new Date(acc.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => handleDisconnect(acc.id)}
                      className="text-xs text-[#E05260] hover:text-[#FF7A93] font-medium"
                    >
                      Disconnect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
