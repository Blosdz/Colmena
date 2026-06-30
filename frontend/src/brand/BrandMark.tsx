import { cn } from "../utils/cn";

type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <svg
      aria-label="Colmena"
      className={cn("h-10 w-10 shrink-0", className)}
      viewBox="260 15 380 380"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="bm-y-top" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#FFD500"/><stop offset="100%" stopColor="#FFC000"/></linearGradient>
        <linearGradient id="bm-y-right" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stopColor="#E6A800"/><stop offset="100%" stopColor="#CC9600"/></linearGradient>
        <linearGradient id="bm-y-left" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#FFB300"/><stop offset="100%" stopColor="#E69500"/></linearGradient>
        <linearGradient id="bm-o-top" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#FF7B00"/><stop offset="100%" stopColor="#FF6200"/></linearGradient>
        <linearGradient id="bm-o-right" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stopColor="#E64A00"/><stop offset="100%" stopColor="#CC3F00"/></linearGradient>
        <linearGradient id="bm-o-left" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#FF5500"/><stop offset="100%" stopColor="#D94000"/></linearGradient>
        <linearGradient id="bm-t-top" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#00D2D6"/><stop offset="100%" stopColor="#00BCC0"/></linearGradient>
        <linearGradient id="bm-t-right" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stopColor="#009EA3"/><stop offset="100%" stopColor="#00858A"/></linearGradient>
        <linearGradient id="bm-t-left" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#00B5B8"/><stop offset="100%" stopColor="#009194"/></linearGradient>
      </defs>
      <g transform="translate(450, 235)">
        {/* TOP HEX (yellow) */}
        <g transform="translate(0, -114)">
          <polygon points="0,-92 80,-46 80,46 0,92 -80,46 -80,-46" fill="url(#bm-y-right)"/>
          <polygon points="0,-92 -80,-46 -80,46 0,0" fill="url(#bm-y-left)"/>
          <polygon points="0,-92 80,-46 0,0" fill="url(#bm-y-top)"/>
          <polygon points="0,-64 55,-32 55,32 0,64 -55,32 -55,-32" fill="#FFFFFF"/>
        </g>
        {/* BOTTOM LEFT HEX (orange) */}
        <g transform="translate(-97, 54)">
          <polygon points="0,-92 80,-46 80,46 0,92 -80,46 -80,-46" fill="url(#bm-o-right)"/>
          <polygon points="0,-92 -80,-46 -80,46 0,0" fill="url(#bm-o-left)"/>
          <polygon points="0,-92 80,-46 0,0" fill="url(#bm-o-top)"/>
          <polygon points="0,-64 55,-32 55,32 0,64 -55,32 -55,-32" fill="#FFFFFF"/>
        </g>
        {/* BOTTOM RIGHT HEX (teal) */}
        <g transform="translate(97, 54)">
          <polygon points="0,-92 80,-46 80,46 0,92 -80,46 -80,-46" fill="url(#bm-t-right)"/>
          <polygon points="0,-92 -80,-46 -80,46 0,0" fill="url(#bm-t-left)"/>
          <polygon points="0,-92 80,-46 0,0" fill="url(#bm-t-top)"/>
          <polygon points="0,-64 55,-32 55,32 0,64 -55,32 -55,-32" fill="#FFFFFF"/>
        </g>
      </g>
    </svg>
  );
}
