export function IconElevator({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="4" y="2.5" width="16" height="19" rx="2" />
      <path d="M12 2.5v19" />
      <path d="M8 8.5l2-2 2 2" />
      <path d="M16 15.5l-2 2-2-2" />
    </svg>
  );
}

export function IconFloors({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M4 7h16M4 12h16M4 17h16" />
      <rect x="3" y="3.5" width="18" height="17" rx="2" />
    </svg>
  );
}

export function IconCapacity({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3.5" y="4" width="17" height="16" rx="2" />
      <circle cx="9" cy="10" r="1.6" />
      <circle cx="15" cy="10" r="1.6" />
      <path d="M6.5 16.5c.8-1.8 2.1-2.7 3.5-2.7s2.7.9 3.5 2.7" />
      <path d="M12.5 16.5c.5-1.1 1.3-1.8 2.5-1.8 1.2 0 2 .7 2.5 1.8" />
    </svg>
  );
}

export function IconPeople({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="8" cy="8" r="2.2" />
      <circle cx="16" cy="8.5" r="1.8" />
      <path d="M3.8 18c.8-2.8 2.6-4.2 4.2-4.2S11.4 15.2 12.2 18" />
      <path d="M13 17.5c.6-2 2-3.1 3.2-3.1 1.3 0 2.5 1.1 3.1 3.1" />
    </svg>
  );
}

export function IconSpeed({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="13" r="8" />
      <path d="M12 13l4.5-4.5" />
      <path d="M8 5.5c1.2-.6 2.6-1 4-1" />
    </svg>
  );
}

export function IconRoute({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="6" cy="6" r="2" />
      <circle cx="18" cy="18" r="2" />
      <path d="M8 6h6a4 4 0 014 4v6" />
    </svg>
  );
}

export function IconBell({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M6 16V11a6 6 0 1112 0v5" />
      <path d="M5 16h14" />
      <path d="M10 19a2 2 0 004 0" />
    </svg>
  );
}

export function IconPerson({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="8" r="3" />
      <path d="M5.5 19.5c1.2-3.4 3.4-5 6.5-5s5.3 1.6 6.5 5" />
    </svg>
  );
}
