import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {transform, build} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const source = await readFile(new URL('../src/lib/analysisPresentation.ts', import.meta.url), 'utf8');
const compiled = await transform(source, {loader: 'ts', format: 'esm'});
const {analysisPresentation} = await import('data:text/javascript;base64,' + Buffer.from(compiled.code).toString('base64'));
const built = await build({entryPoints: ['src/components/AnalysisStatusBadge.tsx'], bundle: true, write: false,
  platform: 'node', format: 'esm', packages: 'external'});
const code = built.outputFiles[0].text.replaceAll('"react/jsx-runtime"', JSON.stringify(import.meta.resolve('react/jsx-runtime')));
const {AnalysisStatusBadge} = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));

test('completed outcomes without a score open the result instead of offering another analysis', () => {
  for (const analysis_status of ['review_required', 'reviewed', 'not_evaluable', 'completed']) {
    const view = analysisPresentation({analysis_status, score: null});
    assert.equal(view.action, 'view');
    assert.equal(view.actionLabel, 'Ver análise');
    assert.ok(!view.label.includes('pendente'));
  }
});

test('ranking renders one accurate status for simulation and human review', () => {
  for (const value of [{analysis_status: 'review_required', analysis_method: 'mock-v1'},
    {analysis_status: 'reviewed', analysis_method: 'human-review'}]) {
    const markup = renderToStaticMarkup(React.createElement(AnalysisStatusBadge, {value}));
    assert.equal((markup.match(/<span/g) ?? []).length, 1);
    assert.ok(!markup.includes('pendente'));
    assert.ok(markup.includes(value.analysis_method === 'mock-v1' ? 'sem avaliação real' : 'Revisto'));
  }
});

test('queued work cannot be submitted again and a new document can be analysed', () => {
  assert.equal(analysisPresentation({analysis_status: 'queued'}).action, 'busy');
  assert.equal(analysisPresentation({analysis_status: 'running'}).action, 'busy');
  assert.equal(analysisPresentation({analysis_status: 'pending'}).actionLabel, 'Analisar');
  assert.equal(analysisPresentation({analysis_status: 'stale', stale: true}).actionLabel, 'Actualizar análise');
  assert.equal(analysisPresentation({analysis_status: 'error'}).actionLabel, 'Tentar novamente');
});
