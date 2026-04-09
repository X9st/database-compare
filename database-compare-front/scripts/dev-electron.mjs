import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const electronBinary = String(require('electron')).trim();

const env = { ...process.env, NODE_ENV: 'development' };
delete env.ELECTRON_RUN_AS_NODE;

console.log(`[electron] ELECTRON_RUN_AS_NODE=${env.ELECTRON_RUN_AS_NODE ?? '<empty>'}`);
console.log(`[electron] binary=${electronBinary}`);

const extraArgs = process.argv.slice(2);
const electronArgs = extraArgs.length > 0 ? extraArgs : ['.'];
const child = spawn(electronBinary, electronArgs, {
  env,
  stdio: 'inherit',
  shell: false,
  cwd: process.cwd(),
});

child.on('exit', (code) => {
  process.exit(code ?? 0);
});

child.on('error', (error) => {
  console.error('[electron] failed to start:', error);
  process.exit(1);
});
