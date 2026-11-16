import type {NextConfig} from 'next';
const config: NextConfig = {
    agentRules:false,
  poweredByHeader: false,
  reactStrictMode: true,
  experimental: {serverActions: {bodySizeLimit: '2mb'}},
};
export default config;
