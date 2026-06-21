export type ChannelScopeTone = 'neutral' | 'company' | 'competitor';

export const channelValueClasses: Record<ChannelScopeTone, string> = {
  neutral: 'text-foreground',
  company: 'text-emerald-500',
  competitor: 'text-sky-500',
};

export const channelBarClasses: Record<ChannelScopeTone, string> = {
  neutral: 'bg-primary',
  company: 'bg-emerald-500',
  competitor: 'bg-sky-500',
};

export const channelBorderClasses: Record<ChannelScopeTone, string> = {
  neutral: 'border-primary',
  company: 'border-emerald-500',
  competitor: 'border-sky-500',
};
