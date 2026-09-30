import test from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';

const built = await build({entryPoints: ['src/components/CompatibilitySummary.tsx'], bundle: true,
  write: false, platform: 'node', format: 'esm', packages: 'external'});
const code = built.outputFiles[0].text.replaceAll('"react/jsx-runtime"', JSON.stringify(import.meta.resolve('react/jsx-runtime')));
const {CompatibilitySummary} = await import('data:text/javascript;base64,' + Buffer.from(code).toString('base64'));
const requirements = [
  {id: 1, name: 'Python', weight: 60, is_mandatory: true},
  {id: 2, name: 'SQL', weight: 40, is_mandatory: false},
];
const evidence = [{requirement_id: 1, state: 'evidenced'}, {requirement_id: 2, state: 'partial'}];
const render = overrides => renderToStaticMarkup(React.createElement(CompatibilitySummary,
  {score: 80, method: 'json-http-v1', requirements, evidence, ...overrides}));

test('compatibility explains the weighted result and names matched and partial requirements', () => {
  const html = render({});
  assert.match(html, /80%/);
  assert.match(html, /Python — obrigatório/);
  assert.match(html, /Contribui 60 de 60 pontos possíveis/);
  assert.match(html, /Contribui 20 de 40 pontos possíveis/);
  assert.match(html, /Requisitos comprovados no CV \(1\)/);
  assert.match(html, /Requisitos parcialmente comprovados \(1\)/);
});

test('mandatory gaps explain why a high score does not prove suitability', () => {
  const html = render({score: 90, recommendation: 'Requisito obrigatório ausente', evidence: [
    {requirement_id: 1, state: 'partial', explanation: 'Experiência introdutória em Python.'},
    {requirement_id: 2, state: 'evidenced'},
  ]});
  assert.match(html, /Requisitos obrigatórios por comprovar/);
  assert.match(html, /Falta comprovação completa.*Python/);
  assert.match(html, /Experiência introdutória em Python/);
  assert.match(html, /Contribui 30 de 60 pontos possíveis/);
  assert.match(html, /decisão do recrutador/);
});

test('missing evidence is shown as pending rather than an absent competency', () => {
  const html = render({evidence: []});
  assert.match(html, /Requisitos por avaliar \(2\)/);
  assert.match(html, /Contributo por determinar/);
  assert.ok(!html.includes('Contribui 0'));
});

test('unevidenced and contradictory requirements contribute zero with clear explanations', () => {
  const html = render({score: 0, evidence: [
    {requirement_id: 1, state: 'not_evidenced'},
    {requirement_id: 2, state: 'contradictory'},
  ]});
  assert.match(html, /Requisitos não comprovados no CV \(1\)/);
  assert.match(html, /Requisitos com informação contraditória \(1\)/);
  assert.match(html, /Contribui 0 de 60 pontos possíveis/);
  assert.match(html, /não significa que o candidato não possui/);
});

test('simulation does not claim missing competencies or display a fabricated percentage', () => {
  const html = render({method: 'mock-v1'});
  assert.match(html, /Compatibilidade ainda não calculada/);
  assert.ok(!html.includes('80%'));
  assert.ok(!html.includes('Sem comprovação no CV'));
});

test('zero is a valid score and missing score is not shown as zero', () => {
  assert.match(render({score: 0}), />0%</);
  assert.ok(!render({score: null}).includes('0%'));
});
