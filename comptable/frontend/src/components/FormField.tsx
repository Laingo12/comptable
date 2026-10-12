import * as React from 'react';
import { cn } from '@/lib/utils';

interface Props {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function FormField({
  label, htmlFor, hint, error, required, children, className,
}: Props) {
  const hintId = htmlFor ? `${htmlFor}-hint` : undefined;
  const errId = htmlFor ? `${htmlFor}-error` : undefined;

  const child = React.isValidElement(children)
    ? React.cloneElement(
        children as React.ReactElement<{
          'aria-describedby'?: string;
          'aria-invalid'?: boolean;
          id?: string;
        }>,
        {
          id: (children as React.ReactElement<{ id?: string }>).props?.id ?? htmlFor,
          'aria-describedby':
            [error ? errId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined,
          'aria-invalid': error ? true : undefined,
        },
      )
    : children;

  return (
    <div className={cn('space-y-1', className)}>
      <label htmlFor={htmlFor} className="text-sm font-medium leading-none">
        {label}
        {required && <span aria-hidden="true" className="ml-1 text-danger">*</span>}
      </label>
      {child}
      {hint && !error && (
        <p id={hintId} className="text-xs text-muted-foreground">{hint}</p>
      )}
      {error && (
        <p id={errId} role="alert" className="text-xs font-medium text-danger">
          {error}
        </p>
      )}
    </div>
  );
}