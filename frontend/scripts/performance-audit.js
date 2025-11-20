#!/usr/bin/env node

/**
 * Performance Audit Script
 *
 * Runs Lighthouse audits locally and generates performance reports
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const URLS = [
  'http://localhost:3000',
  'http://localhost:3000/search',
];

const THRESHOLDS = {
  performance: 0.9,
  accessibility: 0.95,
  'best-practices': 0.9,
  seo: 0.9,
};

async function runAudit(url, chrome) {
  console.log(`\nRunning audit for: ${url}`);

  const options = {
    logLevel: 'info',
    output: ['json', 'html'],
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    port: chrome.port,
  };

  try {
    const runnerResult = await lighthouse(url, options);
    return runnerResult;
  } catch (error) {
    console.error(`Failed to audit ${url}:`, error.message);
    return null;
  }
}

function checkThresholds(lhr) {
  const { categories } = lhr;
  const scores = {};
  let passed = true;

  console.log('\n=== Lighthouse Scores ===');

  Object.entries(categories).forEach(([category, data]) => {
    const score = data.score * 100;
    const threshold = THRESHOLDS[category] * 100;
    const status = score >= threshold ? '✓' : '✗';

    scores[category] = {
      score: score.toFixed(1),
      threshold: threshold.toFixed(1),
      status,
    };

    if (score < threshold) {
      passed = false;
    }

    console.log(
      `${status} ${category.padEnd(20)} ${score.toFixed(1).padStart(5)}% (threshold: ${threshold.toFixed(1)}%)`
    );
  });

  return { scores, passed };
}

function generateReport(results) {
  const report = {
    timestamp: new Date().toISOString(),
    urls: [],
  };

  results.forEach(({ url, lhr }) => {
    if (!lhr) return;

    const scores = Object.entries(lhr.categories).reduce((acc, [name, cat]) => {
      acc[name] = (cat.score * 100).toFixed(1);
      return acc;
    }, {});

    report.urls.push({
      url,
      scores,
    });
  });

  const reportPath = path.join(process.cwd(), 'performance-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\nReport saved to: ${reportPath}`);

  return report;
}

async function main() {
  console.log('Starting Lighthouse performance audits...');
  console.log(`URLs to audit: ${URLS.join(', ')}`);

  let chrome = null;

  try {
    chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--disable-dev-shm-usage', '--no-sandbox'],
    });

    const results = [];
    for (const url of URLS) {
      const result = await runAudit(url, chrome);
      if (result) {
        results.push({
          url,
          lhr: result.lhr,
          html: result.report,
        });

        const { passed } = checkThresholds(result.lhr);
        if (!passed) {
          process.exitCode = 1;
        }
      }
    }

    generateReport(results);

  } finally {
    if (chrome) {
      await chrome.kill();
    }
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { runAudit, checkThresholds, generateReport };
