const path = require('path');
const { listPublishedRoutes, resolveSiteUrl } = require('./lib/sitemap-source');

/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: resolveSiteUrl(),
  generateRobotsTxt: true,
  trailingSlash: false,
  exclude: ['/api/*'],
  outDir: 'public',
  robotsTxtOptions: {
    policies: [
      {
        userAgent: '*',
        allow: '/',
      },
    ],
  },
  additionalPaths: async () =>
    listPublishedRoutes(path.join(__dirname, 'content')),
};
