import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "d2t8nl1y0ie1km.cloudfront.net",
      },
    ],
  },
};

export default nextConfig;
