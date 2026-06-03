'use strict';

const fs = require('node:fs');

function normalizeBinding(binding) {
  return {
    project: binding.project || null,
    context: binding.context || null,
    environmentName: binding.environment_name || binding.environmentName || null,
    accountId: binding.account_id || binding.accountId || null,
    environmentId: binding.environment_id || binding.environmentId || null,
  };
}

function findBinding(data, target) {
  const bindings = Array.isArray(data.bindings) ? data.bindings : [];
  const normalized = bindings.map(normalizeBinding);

  if (target.environmentName) {
    const exactEnvironment = normalized.find(
      (binding) => binding.environmentName === target.environmentName
    );
    if (exactEnvironment) {
      return exactEnvironment;
    }
  }

  return normalized.find(
    (binding) =>
      binding.project === target.project &&
      binding.context === target.context
  ) || null;
}

function checkAccountBinding(data, target) {
  const binding = findBinding(data, target);

  if (!binding) {
    return {
      status: 'no_binding',
      okToContinue: true,
      message: 'No saved 1Password account binding found for target.',
    };
  }

  if (!binding.accountId) {
    return {
      status: 'invalid_binding',
      okToContinue: false,
      savedEnvironmentName: binding.environmentName,
      message: 'Saved 1Password account binding is missing account_id.',
    };
  }

  if (binding.accountId !== target.accountId) {
    return {
      status: 'account_mismatch',
      okToContinue: false,
      savedAccountId: binding.accountId,
      currentAccountId: target.accountId,
      savedEnvironmentName: binding.environmentName,
      savedEnvironmentId: binding.environmentId,
      message:
        '1Password authentication succeeded, but this project is bound to a different account.',
    };
  }

  return {
    status: 'match',
    okToContinue: true,
    savedAccountId: binding.accountId,
    currentAccountId: target.accountId,
    savedEnvironmentName: binding.environmentName,
    savedEnvironmentId: binding.environmentId,
    message: '1Password account binding matches authenticated account.',
  };
}

function parseArgs(argv) {
  const args = {
    file: '.1password/environments.json',
    accountId: null,
    project: null,
    context: null,
    environmentName: null,
  };

  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === '--file') {
      args.file = next;
      index += 1;
    } else if (arg === '--account-id') {
      args.accountId = next;
      index += 1;
    } else if (arg === '--project') {
      args.project = next;
      index += 1;
    } else if (arg === '--context') {
      args.context = next;
      index += 1;
    } else if (arg === '--environment-name') {
      args.environmentName = next;
      index += 1;
    }
  }

  return args;
}

function main(argv) {
  const args = parseArgs(argv);

  if (!args.accountId) {
    process.stderr.write(
      'Usage: check-account-binding.js --account-id ACCOUNT_ID ' +
      '[--environment-name NAME | --project PROJECT --context CONTEXT] ' +
      '[--file .1password/environments.json]\n'
    );
    process.exitCode = 1;
    return;
  }

  if (!fs.existsSync(args.file)) {
    process.stdout.write(JSON.stringify({
      status: 'no_binding_file',
      okToContinue: true,
      message: 'No .1password account binding file found.',
    }, null, 2) + '\n');
    return;
  }

  const data = JSON.parse(fs.readFileSync(args.file, 'utf8'));
  const result = checkAccountBinding(data, args);
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');

  if (!result.okToContinue) {
    process.exitCode = 2;
  }
}

if (require.main === module) {
  main(process.argv);
}

module.exports = { checkAccountBinding, findBinding };
