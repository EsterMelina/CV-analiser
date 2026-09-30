import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { transform } from 'esbuild';
import axios from 'axios';

const stored = new Map();
globalThis.localStorage = { getItem: key => stored.get(key) ?? null,
  setItem: (key, value) => stored.set(key, value), removeItem: key => stored.delete(key) };
globalThis.window = new EventTarget();
const source = await readFile(new URL('../src/lib/api.ts', import.meta.url), 'utf8');
const compiled = await transform(source, { loader: 'ts', format: 'esm' });
const module = compiled.code.replace('"axios"', JSON.stringify(import.meta.resolve('axios')));
const { api, tokenStorage, refreshSession } = await import('data:text/javascript;base64,' + Buffer.from(module).toString('base64'));

test('expired /auth/me renews once and concurrent failures all settle', async () => {
  tokenStorage.clear();
  tokenStorage.set('expired', 'refresh');
  let renewals = 0;
  api.defaults.adapter = async config => {
    if (config.headers.Authorization !== 'Bearer fresh') {
      throw new axios.AxiosError('expired', '401', config, null, {status: 401});
    }
    return {data: {id: 1}, status: 200, config};
  };
  axios.defaults.adapter = async config => {
    renewals++;
    await new Promise(resolve => setTimeout(resolve, 5));
    return {data: {access_token: 'fresh', refresh_token: 'rotated'}, status: 200, config};
  };
  const responses = await Promise.all([api.get('/auth/me'), api.get('/jobs')]);
  assert.equal(responses[0].data.id, 1);
  assert.equal(renewals, 1);

  tokenStorage.clear(); tokenStorage.set('expired', 'invalid');
  axios.defaults.adapter = async () => { throw new Error('unavailable'); };
  const failures = await Promise.allSettled([api.get('/auth/me'), api.get('/jobs')]);
  assert.ok(failures.every(result => result.status === 'rejected'));
  assert.equal(tokenStorage.getAccess(), null);
});

test('late renewal cannot replace a different login', async () => {
  tokenStorage.clear(); tokenStorage.set('old', 'old-refresh');
  let finish;
  axios.defaults.adapter = config => new Promise(resolve => {
    finish = () => resolve({data: {access_token: 'stale', refresh_token: 'stale-refresh'}, status: 200, config});
  });
  const renewing = refreshSession();
  await new Promise(resolve => setTimeout(resolve, 0));
  tokenStorage.clear(); tokenStorage.set('new-user', 'new-refresh');
  finish();
  await assert.rejects(renewing);
  assert.equal(tokenStorage.getAccess(), 'new-user');
});
