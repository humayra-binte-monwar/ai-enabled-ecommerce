import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // The scraped catalog uses remote CloudFront assets. Let the browser load
    // them directly so local development and a serverless deployment do not
    // depend on Next's image optimisation proxy reaching that host.
    unoptimized: true,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "d2t8nl1y0ie1km.cloudfront.net",
      },
    ],
  },
};

export default nextConfig;
