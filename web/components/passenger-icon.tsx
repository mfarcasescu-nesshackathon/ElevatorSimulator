export function PassengerGlyph({
  icon,
  role,
  name,
  dest,
  size = "md",
}: {
  icon: string;
  role: "employee" | "guest";
  name?: string;
  dest?: number;
  size?: "sm" | "md";
}) {
  const palette = role === "employee" ? "bg-cyan-500 text-slate-950" : "bg-amber-400 text-slate-950";
  const box = size === "sm" ? "h-7 w-7" : "h-9 w-9";
  return (
    <span className="inline-flex flex-col items-center gap-0.5">
      <span className={`inline-flex ${box} items-center justify-center rounded-full ${palette} shadow`}>
        <Glyph icon={icon} className={size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4"} />
      </span>
      {name ? (
        <span className="max-w-[72px] truncate text-[9px] font-medium text-white">
          {name}
          {dest !== undefined ? ` →${dest}` : ""}
        </span>
      ) : null}
    </span>
  );
}

function Glyph({ icon, className }: { icon: string; className?: string }) {
  const common = { className, fill: "none", stroke: "currentColor", strokeWidth: 1.9, viewBox: "0 0 24 24" };
  if (icon === "briefcase") {
    return (
      <svg {...common}>
        <rect x="4" y="8" width="16" height="11" rx="2" />
        <path d="M9 8V6.5A2.5 2.5 0 0111.5 4h1A2.5 2.5 0 0115 6.5V8" />
      </svg>
    );
  }
  if (icon === "badge") {
    return (
      <svg {...common}>
        <rect x="5" y="7" width="14" height="12" rx="2" />
        <circle cx="12" cy="12" r="2" />
        <path d="M9 4h6" />
      </svg>
    );
  }
  if (icon === "laptop") {
    return (
      <svg {...common}>
        <rect x="5" y="6" width="14" height="9" rx="1.5" />
        <path d="M3 17h18" />
      </svg>
    );
  }
  if (icon === "star") {
    return (
      <svg {...common}>
        <path d="M12 4l2.2 4.6L19 9.3l-3.5 3.4.8 4.8L12 15.8 7.7 17.5l.8-4.8L5 9.3l4.8-.7L12 4z" />
      </svg>
    );
  }
  if (icon === "coffee") {
    return (
      <svg {...common}>
        <path d="M5 9h11v5a4 4 0 01-4 4H9a4 4 0 01-4-4V9z" />
        <path d="M16 10h2a2 2 0 010 4h-2" />
      </svg>
    );
  }
  if (icon === "camera") {
    return (
      <svg {...common}>
        <rect x="4" y="8" width="16" height="11" rx="2" />
        <circle cx="12" cy="13.5" r="3" />
        <path d="M9 8l1.2-2h3.6L15 8" />
      </svg>
    );
  }
  if (icon === "gift") {
    return (
      <svg {...common}>
        <rect x="4" y="10" width="16" height="9" rx="1.5" />
        <path d="M4 13h16M12 10v9" />
        <path d="M8 7c1.5 0 4 2.5 4 3s-2-3-4-3zM16 7c-1.5 0-4 2.5-4 3s2-3 4-3z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="12" cy="8" r="3" />
      <path d="M5.5 19.5c1.2-3.4 3.4-5 6.5-5s5.3 1.6 6.5 5" />
    </svg>
  );
}
