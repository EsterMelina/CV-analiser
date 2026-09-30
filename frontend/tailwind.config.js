/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        // =====================
        // Tokens legados (compat)
        // =====================
        canvas: "#F8F9FF",
        surface: "#FFFFFF",          // ⚠️ colide com o DS; ver nota abaixo
        subtle: "#F1F5F9",
        ink: "#0B1C30",
        "ink-soft": "#434655",
        "ink-faint": "#737686",
        "ink-inverse": "#EAF1FF",
        line: "#E2E8F0",
        "line-strong": "#C3C6D7",
        "line-input": "#CBD5E1",

        brand: {
          DEFAULT: "#2563EB",
          dark: "#1D4ED8",
          deep: "#004AC6",
          soft: "#DBE1FF",
          "soft-dim": "#B4C5FF",
          ink: "#00174B",
          tint: "#0053DB",
        },
        "brand-deep": "#004AC6",
        "brand-dark": "#1D4ED8",
        "brand-soft": "#DBE1FF",

        slate2: {
          DEFAULT: "#565E74",
          deep: "#0F172A",
          soft: "#DAE2FD",
          ink: "#131B2E",
        },

        success: {
          DEFAULT: "#10B981",
          deep: "#006242",
          container: "#007D55",
          soft: "#ECFDF5",
          ink: "#065F46",
          border: "#A7F3D0",
          bright: "#6FFBBE",
          dim: "#4EDEA3",
          "ink-strong": "#002113",
        },
        warning: {
          DEFAULT: "#F59E0B",
          soft: "#FFFBEB",
          ink: "#92400E",
          border: "#FDE68A",
        },
        danger: {
          DEFAULT: "#EF4444",
          deep: "#DC2626",
          strongest: "#BA1A1A",
          soft: "#FEF2F2",
          container: "#FFDAD6",
          ink: "#991B1B",
          "ink-strong": "#93000A",
          border: "#FECACA",
          "border-strong": "#FCA5A5",
        },
        ai: {
          DEFAULT: "#2563EB",
          soft: "#EFF6FF",
          ink: "#1E40AF",
          border: "#BFDBFE",
        },

        // =====================
        // Tokens do DS oficial
        // =====================
        "surface-canvas": "#f8f9ff",
        "surface-dim": "#cbdbf5",
        "surface-bright": "#f8f9ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eff4ff",
        "surface-container": "#e5eeff",
        "surface-container-high": "#dce9ff",
        "surface-container-highest": "#d3e4fe",
        "on-surface": "#0b1c30",
        "on-surface-variant": "#434655",
        "inverse-surface": "#213145",
        "inverse-on-surface": "#eaf1ff",
        outline: "#737686",
        "outline-variant": "#c3c6d7",
        "surface-tint": "#0053db",
        "surface-variant": "#d3e4fe",

        primary: "#004ac6",
        "on-primary": "#ffffff",
        "primary-container": "#2563eb",
        "on-primary-container": "#eeefff",
        "inverse-primary": "#b4c5ff",
        "primary-fixed": "#dbe1ff",
        "primary-fixed-dim": "#b4c5ff",
        "on-primary-fixed": "#00174b",
        "on-primary-fixed-variant": "#003ea8",

        secondary: "#565e74",
        "on-secondary": "#ffffff",
        "secondary-container": "#dae2fd",
        "on-secondary-container": "#5c647a",
        "secondary-fixed": "#dae2fd",
        "secondary-fixed-dim": "#bec6e0",
        "on-secondary-fixed": "#131b2e",
        "on-secondary-fixed-variant": "#3f465c",

        tertiary: "#006242",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#007d55",
        "on-tertiary-container": "#bdffdb",
        "tertiary-fixed": "#6ffbbe",
        "tertiary-fixed-dim": "#4edea3",
        "on-tertiary-fixed": "#002113",
        "on-tertiary-fixed-variant": "#005236",

        error: "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",

        background: "#f8f9ff",
        "on-background": "#0b1c30",
      },

      fontSize: {
        "headline-xl": ["32px", { lineHeight: "40px", fontWeight: "700" }],
        "headline-lg": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "headline-md": ["20px", { lineHeight: "28px", fontWeight: "600" }],
        "headline-sm": ["16px", { lineHeight: "24px", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "20px", fontWeight: "400" }],
        "body-sm": ["12px", { lineHeight: "16px", fontWeight: "400" }],
        "label-lg": ["14px", { lineHeight: "20px", fontWeight: "500" }],
        "label-md": ["12px", { lineHeight: "16px", fontWeight: "500" }],
        "label-sm": ["11px", { lineHeight: "14px", fontWeight: "600", letterSpacing: "0.025em" }],
      },

      borderRadius: {
        sm: "0.25rem",
        DEFAULT: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },

      spacing: {
        gutter: "1.5rem",
        "gutter-mobile": "1rem",
        margin: "2rem",
        "margin-mobile": "1rem",
        xs: "0.25rem",
        sm: "0.5rem",
        md: "1rem",
        lg: "1.5rem",
        xl: "2rem",
        "2xl": "3rem",
      },

      maxWidth: {
        container: "1600px",
      },

      boxShadow: {
        card: "0 1px 3px 0 rgba(15,23,42,0.04), 0 1px 2px -1px rgba(15,23,42,0.03)",
        popover: "0 10px 15px -3px rgba(15,23,42,0.08), 0 4px 6px -4px rgba(15,23,42,0.04)",
        modal: "0 20px 25px -5px rgba(15,23,42,0.10), 0 8px 10px -6px rgba(15,23,42,0.04)",
      },
    },
  },
  plugins: [],
};