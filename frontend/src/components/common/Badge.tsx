import React from 'react';

export type BadgeVariant = 
  | 'DRAFT' 
  | 'GENERATING'
  | 'PROCESSING' 
  | 'QA_PENDING'
  | 'PENDING_APPROVAL' 
  | 'PENDING_REVIEW'
  | 'APPROVED' 
  | 'READY_TO_SCHEDULE'
  | 'SCHEDULED'
  | 'PUBLISHING'
  | 'PUBLISHED' 
  | 'FAILED' 
  | 'REJECTED'
  | 'QUEUED'
  | 'CONNECTED'
  | 'NOT_CONNECTED'
  | 'ACTIVE'
  | 'SANDBOX'
  | 'REAL'
  | 'NEUTRAL';

interface BadgeProps {
  variant: BadgeVariant | string;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant, label, size = 'md', className = '' }) => {
  const norm = (variant || '').toUpperCase().replace(/\s+/g, '_');
  
  let styles = 'bg-[#1D1D25] text-[#A9A4AA] border-[#2B2B35]';
  let dotColor = 'bg-[#736E76]';
  let displayLabel = label || variant;

  switch (norm) {
    case 'PENDING_APPROVAL':
    case 'PENDING_REVIEW':
    case 'RENDER_READY':
    case 'PENDING':
      styles = 'bg-[#2E2211] text-[#E8A83E] border-[#5E4119]';
      dotColor = 'bg-[#E8A83E]';
      displayLabel = label || 'Pending Review';
      break;
    case 'APPROVED':
      styles = 'bg-[#112A20] text-[#35C98B] border-[#1D523B]';
      dotColor = 'bg-[#35C98B]';
      displayLabel = label || 'Approved';
      break;
    case 'READY_TO_SCHEDULE':
    case 'SCHEDULED':
      styles = 'bg-[#192438] text-[#5EB1FF] border-[#274B72]';
      dotColor = 'bg-[#5EB1FF]';
      displayLabel = label || (norm === 'SCHEDULED' ? 'Scheduled' : 'Ready to Schedule');
      break;
    case 'PUBLISHED':
    case 'CONNECTED':
    case 'ACTIVE':
      styles = 'bg-[#112A20] text-[#35C98B] border-[#1D523B]';
      dotColor = 'bg-[#35C98B]';
      displayLabel = label || (norm === 'CONNECTED' ? 'CONNECTED' : norm === 'ACTIVE' ? 'ACTIVE' : 'Published');
      break;
    case 'GENERATING':
    case 'PROCESSING':
    case 'QA_PENDING':
    case 'PUBLISHING':
      styles = 'bg-[#142233] text-[#4A90E2] border-[#1F4060]';
      dotColor = 'bg-[#4A90E2] animate-pulse';
      displayLabel = label || (
        norm === 'PUBLISHING' 
          ? 'Publishing...' 
          : norm === 'QA_PENDING' 
          ? 'QA Validation...' 
          : 'Generating...'
      );
      break;
    case 'FAILED':
    case 'REJECTED':
      styles = 'bg-[#2C1418] text-[#E05260] border-[#5B2129]';
      dotColor = 'bg-[#E05260]';
      displayLabel = label || (norm === 'REJECTED' ? 'Rejected' : 'Failed');
      break;
    case 'DRAFT':
    case 'QUEUED':
      styles = 'bg-[#1D1D25] text-[#A9A4AA] border-[#2B2B35]';
      dotColor = 'bg-[#A9A4AA]';
      displayLabel = label || (norm === 'QUEUED' ? 'Queued' : 'Draft');
      break;
    case 'REAL':
      styles = 'bg-[#2A141A] text-[#FF7A93] border-[#8E1B32]';
      dotColor = 'bg-[#C62845]';
      displayLabel = label || 'Real Account';
      break;
    case 'SANDBOX':
      styles = 'bg-[#1F1E2A] text-[#9D93E8] border-[#3F3A66]';
      dotColor = 'bg-[#7C6CE6]';
      displayLabel = label || 'Sandbox / Test';
      break;
    case 'NOT_CONNECTED':
      styles = 'bg-[#1D1D25] text-[#736E76] border-[#2B2B35]';
      dotColor = 'bg-[#555]';
      displayLabel = label || 'NOT CONNECTED';
      break;
  }

  const sizeClasses = size === 'sm' 
    ? 'text-[11px] px-2 py-0.5 font-medium' 
    : 'text-xs px-2.5 py-1 font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border tracking-wide uppercase ${sizeClasses} ${styles} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{displayLabel}</span>
    </span>
  );
};
