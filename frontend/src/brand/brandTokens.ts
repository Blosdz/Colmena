export const brandTokens = {
  colors: {
    yellow: "#F5B21A",
    orange: "#FF6A2A",
    turquoise: "#11B7B2",
    black: "#111111",
    graphite: "#1C1F24",
    gray: "#6A7380",
    border: "#E6E8EB",
    background: "#FAFAF8",
    white: "#FFFFFF",
    yellowSoft: "#FFF4D6",
    yellowMid: "#FDE7AB",
    yellowDark: "#D99712",
    orangeSoft: "#FFE2D6",
    orangeMid: "#FFC3AD",
    orangeDark: "#E25318",
    turquoiseSoft: "#D9F7F5",
    turquoiseMid: "#AEEDEA",
    turquoiseDark: "#0C9897",
  },
  gradients: {
    hero:
      "radial-gradient(circle at top left, rgba(245, 178, 26, 0.18), transparent 28%), radial-gradient(circle at top right, rgba(255, 106, 42, 0.12), transparent 24%), radial-gradient(circle at bottom left, rgba(17, 183, 178, 0.12), transparent 25%)",
  },
} as const;

export type BrandTokenMap = typeof brandTokens;
