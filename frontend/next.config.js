/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  devIndicators: false,
  images: {
    remotePatterns: [],
  },
}

module.exports = nextConfig
