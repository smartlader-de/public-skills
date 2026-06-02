'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { parseDotenv } = require('../scripts/parse-dotenv.js');

test('parses simple KEY=value pairs', () => {
  const result = parseDotenv('DATABASE_URL=placeholder\nAPI_KEY=secret');
  assert.deepEqual(result.names, ['DATABASE_URL', 'API_KEY']);
});

test('parses export KEY=value syntax', () => {
  const result = parseDotenv('export DATABASE_URL=placeholder\nexport API_KEY=secret');
  assert.deepEqual(result.names, ['DATABASE_URL', 'API_KEY']);
});

test('ignores comment lines and counts comments', () => {
  const result = parseDotenv('# This is a comment\nKEY=value\n# another comment');
  assert.deepEqual(result.names, ['KEY']);
  assert.equal(result.commentCount, 2);
});

test('ignores blank lines and counts blanks', () => {
  const result = parseDotenv('\n\nKEY=value\n\n');
  assert.deepEqual(result.names, ['KEY']);
  assert.equal(result.blankCount, 3);
});

test('handles double-quoted values', () => {
  const result = parseDotenv('MY_VAR="hello world"');
  assert.deepEqual(result.names, ['MY_VAR']);
});

test('handles single-quoted values', () => {
  const result = parseDotenv("MY_VAR='hello world'");
  assert.deepEqual(result.names, ['MY_VAR']);
});

test('handles empty values', () => {
  const result = parseDotenv('EMPTY_VAR=');
  assert.deepEqual(result.names, ['EMPTY_VAR']);
});

test('handles values containing equals signs', () => {
  const result = parseDotenv('ENCODED=abc=def=ghi');
  assert.deepEqual(result.names, ['ENCODED']);
});

test('rejects lines without equals sign', () => {
  const result = parseDotenv('NOT_A_VARIABLE\nGOOD_VAR=val');
  assert.deepEqual(result.names, ['GOOD_VAR']);
});

test('rejects keys with invalid characters', () => {
  const result = parseDotenv('123INVALID=val\nVALID_KEY=val');
  assert.deepEqual(result.names, ['VALID_KEY']);
});

test('does not include values in output', () => {
  const result = parseDotenv('SECRET_KEY=super-secret-value-12345');
  assert.equal(result.names.length, 1);
  assert.equal(result.names[0], 'SECRET_KEY');
  assert.ok(!JSON.stringify(result).includes('super-secret-value-12345'));
});

test('counts comment and blank lines accurately', () => {
  const content = [
    '# comment 1',
    '',
    'KEY1=val',
    '# comment 2',
    '',
    'KEY2=val',
    '',
  ].join('\n');
  const result = parseDotenv(content);
  assert.equal(result.commentCount, 2);
  assert.equal(result.blankCount, 3);
  assert.equal(result.names.length, 2);
});
