import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {transform} from 'esbuild';
const source = await readFile(new URL('../src/lib/analysisRunning.ts', import.meta.url), 'utf8');
const built = await transform(source, {loader: 'ts', format: 'esm'});
const {analysisRunning} = await import('data:text/javascript;base64,' + Buffer.from(built.code).toString('base64'));

test('failed and completed executions override a stale running application', () => {
  for (const status of ['failed', 'succeeded']) assert.equal(analysisRunning('id', status, 'running', false), false);
  assert.equal(analysisRunning('id', 'running', 'received', false), true);
  assert.equal(analysisRunning('id', undefined, 'running', true), false);
  assert.equal(analysisRunning(null, undefined, 'running', false), true);
});
