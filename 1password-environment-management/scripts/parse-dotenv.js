'use strict';

const fs = require('node:fs');
const path = require('node:path');

const NAME_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;

function parseDotenv(content) {
  const names = [];
  let commentCount = 0;
  let blankCount = 0;

  const lines = content.split(/\r?\n/);
  let lastNonBlankIndex = -1;

  for (let index = lines.length - 1; index >= 0; index -= 1) {
    if (lines[index].trim() !== '') {
      lastNonBlankIndex = index;
      break;
    }
  }

  let trailingBlankCounted = false;

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const line = rawLine.trim();

    if (line === '') {
      if (index <= lastNonBlankIndex) {
        blankCount++;
      } else if (!trailingBlankCounted) {
        blankCount++;
        trailingBlankCounted = true;
      }
      continue;
    }

    trailingBlankCounted = false;

    if (line.startsWith('#')) {
      commentCount++;
      continue;
    }

    const entry = line.startsWith('export ') ? line.slice(7).trimStart() : line;
    const equalsIndex = entry.indexOf('=');

    if (equalsIndex === -1) {
      continue;
    }

    const name = entry.slice(0, equalsIndex).trim();

    if (!NAME_PATTERN.test(name)) {
      continue;
    }

    names.push(name);
  }

  return {
    names,
    variableCount: names.length,
    commentCount,
    blankCount,
  };
}

function main(argv) {
  const filePaths = argv.slice(2);

  if (filePaths.length === 0) {
    console.error('Usage: parse-dotenv.js <file> [file...]');
    process.exitCode = 1;
    return;
  }

  const results = filePaths.map((filePath) => {
    const content = fs.readFileSync(filePath, 'utf8');
    const parsed = parseDotenv(content);

    return {
      file: path.basename(filePath),
      path: filePath,
      variableCount: parsed.variableCount,
      commentCount: parsed.commentCount,
      blankCount: parsed.blankCount,
      names: parsed.names,
    };
  });

  process.stdout.write(JSON.stringify(results));
}

if (require.main === module) {
  main(process.argv);
}

module.exports = { parseDotenv };
