'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { checkAccountBinding } = require('../scripts/check-account-binding.js');

const bindingFile = {
  version: 1,
  bindings: [
    {
      project: 'ovh-bits',
      context: 'production',
      environment_name: 'ovh-bits/production',
      account_id: 'FSUTNS7VXBBPHBSOA6ZP7BYY7Y',
      environment_id: 'avnw46sj6xhztmmcwfzffycmrq',
    },
  ],
};

test('allows matching authenticated account', () => {
  const result = checkAccountBinding(bindingFile, {
    accountId: 'FSUTNS7VXBBPHBSOA6ZP7BYY7Y',
    environmentName: 'ovh-bits/production',
  });

  assert.equal(result.status, 'match');
  assert.equal(result.okToContinue, true);
});

test('stops on account mismatch before writes', () => {
  const result = checkAccountBinding(bindingFile, {
    accountId: 'DIFFERENTACCOUNTID',
    environmentName: 'ovh-bits/production',
  });

  assert.equal(result.status, 'account_mismatch');
  assert.equal(result.okToContinue, false);
  assert.equal(result.savedAccountId, 'FSUTNS7VXBBPHBSOA6ZP7BYY7Y');
  assert.equal(result.currentAccountId, 'DIFFERENTACCOUNTID');
});

test('finds binding by project and context when environment name is absent', () => {
  const result = checkAccountBinding(bindingFile, {
    accountId: 'FSUTNS7VXBBPHBSOA6ZP7BYY7Y',
    project: 'ovh-bits',
    context: 'production',
  });

  assert.equal(result.status, 'match');
});

test('allows metadata discovery when no binding exists', () => {
  const result = checkAccountBinding(bindingFile, {
    accountId: 'FSUTNS7VXBBPHBSOA6ZP7BYY7Y',
    environmentName: 'other/project',
  });

  assert.equal(result.status, 'no_binding');
  assert.equal(result.okToContinue, true);
});

test('does not include secret-shaped fields in output', () => {
  const result = checkAccountBinding(bindingFile, {
    accountId: 'DIFFERENTACCOUNTID',
    environmentName: 'ovh-bits/production',
  });
  const serialized = JSON.stringify(result);

  assert.ok(!serialized.includes('value'));
  assert.ok(!serialized.includes('secret'));
  assert.ok(!serialized.includes('hash'));
});
