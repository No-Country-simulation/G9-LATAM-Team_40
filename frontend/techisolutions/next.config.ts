import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Salida standalone para imagen Docker liviana (ver Dockerfile)
  output: "standalone",
  serverExternalPackages: ["pdfjs-dist"],
}

export default nextConfig
