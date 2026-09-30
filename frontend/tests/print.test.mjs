import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const built = await build({ entryPoints: ['src/components/QuestionnaireSheet.tsx'], bundle: true,
  write: false, platform: 'node', format: 'esm', packages: 'external' });
const source = built.outputFiles[0].text.replaceAll('"react"', JSON.stringify(import.meta.resolve('react')))
  .replaceAll('"react/jsx-runtime"', JSON.stringify(import.meta.resolve('react/jsx-runtime')));
const { QuestionnaireSheet } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
test('question sheet never renders internal answer or rubric, even if supplied', () => {
  const data = {job: 'Gestor de Armazém', code: 'ARM-1', version: 3, status: 'draft', mode: 'questions',
    questions: [{prompt: 'Como verifica o inventário?', options: ['Contagem', 'Estimativa'], expected_answer: 'SECRET-ANSWER', rubric: 'SECRET-RUBRIC', correct_index: 0}]};
  const sheet = renderToStaticMarkup(React.createElement(QuestionnaireSheet, {data}));
  assert.ok(sheet.includes('Gestor de Armazém'));
  assert.ok(sheet.includes('RASCUNHO'));
  assert.ok(!sheet.includes('SECRET'));
  const guide = renderToStaticMarkup(React.createElement(QuestionnaireSheet, {data: {...data, mode: 'guide'}}));
  assert.ok(guide.includes('SECRET-ANSWER'));
  assert.ok(guide.includes('SECRET-RUBRIC'));
});
