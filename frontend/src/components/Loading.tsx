import { clsx } from 'clsx';

export function Loading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <div className="animate-spin rounded-full h-10 w-10 border-3 border-primary-200 border-t-primary-600" />
      <p className="text-gray-600">{message}</p>
    </div>
  );
}

export function LoadingInline({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-6 w-6 border-2',
    lg: 'h-8 w-8 border-3',
  };
  return (
    <div className={clsx('animate-spin rounded-full border-gray-200 border-t-primary-600', sizeClasses[size])} />
  );
}