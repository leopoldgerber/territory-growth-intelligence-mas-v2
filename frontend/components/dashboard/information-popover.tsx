'use client';

import { CircleHelp } from 'lucide-react';
import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type InformationPopoverProps = {
  ariaLabel: string;
  children: ReactNode;
  className?: string;
  title: string;
};

type PanelPosition = {
  left: number;
  top: number;
};

export function InformationPopover({ ariaLabel, children, className, title }: InformationPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [panelPosition, setPanelPosition] = useState<PanelPosition>({ left: 0, top: 0 });
  const infoRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const panelId = useId();

  useEffect(() => {
    function close_outside(event: PointerEvent): void {
      const target = event.target as Node;
      if (
        infoRef.current &&
        !infoRef.current.contains(target) &&
        !panelRef.current?.contains(target)
      ) {
        setIsOpen(false);
      }
    }

    function close_escape(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('pointerdown', close_outside);
    document.addEventListener('keydown', close_escape);
    return () => {
      document.removeEventListener('pointerdown', close_outside);
      document.removeEventListener('keydown', close_escape);
    };
  }, []);

  useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }

    function update_position(): void {
      const triggerElement = infoRef.current;
      const panelElement = panelRef.current;
      if (!triggerElement || !panelElement) {
        return;
      }

      const viewportPadding = 12;
      const panelGap = 8;
      const triggerRect = triggerElement.getBoundingClientRect();
      const panelRect = panelElement.getBoundingClientRect();
      const spaceAbove = triggerRect.top - viewportPadding;
      const spaceBelow = window.innerHeight - triggerRect.bottom - viewportPadding;
      const openAbove = spaceBelow < panelRect.height + panelGap && spaceAbove > spaceBelow;
      const preferredTop = openAbove
        ? triggerRect.top - panelRect.height - panelGap
        : triggerRect.bottom + panelGap;
      const top = Math.min(
        Math.max(viewportPadding, preferredTop),
        window.innerHeight - panelRect.height - viewportPadding,
      );
      const left = Math.min(
        Math.max(viewportPadding, triggerRect.right - panelRect.width),
        window.innerWidth - panelRect.width - viewportPadding,
      );
      setPanelPosition({ left, top });
    }

    update_position();
    window.addEventListener('resize', update_position);
    window.addEventListener('scroll', update_position, true);
    return () => {
      window.removeEventListener('resize', update_position);
      window.removeEventListener('scroll', update_position, true);
    };
  }, [isOpen]);

  return (
    <div className="relative inline-flex shrink-0" ref={infoRef}>
      <Button
        aria-controls={panelId}
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        className="h-6 w-6"
        onClick={() => setIsOpen((currentValue) => !currentValue)}
        size="icon"
        title={ariaLabel}
        type="button"
        variant="ghost"
      >
        <CircleHelp className="h-3.5 w-3.5" />
      </Button>
      {isOpen
        ? createPortal(
            <div
              aria-label={title}
              className={cn(
                'fixed z-50 w-[min(22rem,calc(100vw-1.5rem))] rounded-md border bg-background p-4 text-left shadow-lg',
                className,
              )}
              id={panelId}
              ref={panelRef}
              role="dialog"
              style={panelPosition}
            >
              <p className="text-sm font-semibold text-foreground">{title}</p>
              <div className="mt-1 text-xs font-normal leading-5 text-muted-foreground">{children}</div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
