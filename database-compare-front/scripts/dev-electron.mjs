import { spawn } from 'node:child_process';

const env = { ...process.env, NODE_ENV: 'development' };
delete env.ELECTRON_RUN_AS_NODE;

console.log(`[electron] ELECTRON_RUN_AS_NODE=${env.ELECTRON_RUN_AS_NODE ?? '<empty>'}`);

const extraArgs = process.argv.slice(2);
const electronArgs = extraArgs.length > 0 ? extraArgs : ['.'];
const npxBin = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const child = spawn(npxBin, ['electron', ...electronArgs], {
  env,
  stdio: 'inherit',
  shell: false,
});

child.on('exit', (code) => {
  process.exit(code ?? 0);
});

child.on('error', (error) => {
  console.error('[electron] failed to start:', error);
  process.exit(1);
});
