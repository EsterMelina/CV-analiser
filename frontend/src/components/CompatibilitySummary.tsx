export interface AnalysisRequirement {
  id: number;
  name: string;
  description?: string | null;
  weight: number;
  is_mandatory: boolean;
}

interface Props {
  score: number | null;
  method: string;
  requirements: AnalysisRequirement[];
  evidence: {requirement_id: number; state: string; explanation?: string}[];
  recommendation?: string | null;
  summary?: string;
}

const groups = [
  ["evidenced", "Requisitos comprovados no CV"],
  ["partial", "Requisitos parcialmente comprovados"],
  ["not_evidenced", "Requisitos não comprovados no CV"],
  ["contradictory", "Requisitos com informação contraditória"],
  ["unknown", "Requisitos por avaliar"],
] as const;

export function CompatibilitySummary({score, method, requirements, evidence, recommendation, summary}: Props) {
  if (method.startsWith("mock")) return <div role="status">
    <h2 className="text-xl">Compatibilidade ainda não calculada</h2>
    <p>Este registo antigo foi criado pelo simulador. Execute uma nova análise com IA para avaliar este CV.</p>
  </div>;
  if (score == null) return <p>Não foi possível calcular a compatibilidade deste documento.</p>;
  const totalWeight = requirements.reduce((total, item) => total + item.weight, 0);
  const states = new Map(evidence.map(item => [item.requirement_id, item.state]));
  const format = (value: number) => value.toLocaleString("pt-PT", {maximumFractionDigits: 2});
  const knownStates = groups.map(([state]) => state as string);
  const stateOf = (id: number) => knownStates.includes(states.get(id) ?? "") ? states.get(id) : "unknown";
  const missingMandatory = requirements.filter(item => item.is_mandatory && stateOf(item.id) !== "evidenced");
  const contribution = (state: string | undefined) => state === "evidenced" ? 1 : state === "partial" ? 0.5 : 0;
  return <div className="space-y-5">
    <div className="rounded-lg border border-line bg-brand-soft p-5 sm:p-6">
      <p className="text-xs font-semibold uppercase tracking-wider text-ink-soft">Avaliação do perfil</p>
      <div className="mt-3 flex flex-wrap items-center gap-5"><p className="text-4xl font-semibold tabular-nums text-brand-dark">{format(score)}%</p>
        <div><h2 className="font-semibold">Compatibilidade com os requisitos da vaga</h2><p className="text-sm text-ink-soft mt-1">Resultado da comparação entre o CV e os critérios definidos.</p></div></div>
      {recommendation && <h3 className="mt-5 font-semibold">{recommendation === "Requisito obrigatório ausente" ? "Requisitos obrigatórios por comprovar" : recommendation}</h3>}
      <p className="mt-2 text-sm leading-relaxed">Com base nas evidências disponíveis no CV e no peso de cada requisito, foi apurada uma compatibilidade de {format(score)}%.</p>
      {missingMandatory.length > 0 ? <p className="mt-2 text-sm"><strong>A adequação à vaga ainda não está comprovada.</strong> Falta comprovação completa dos seguintes requisitos obrigatórios: {missingMandatory.map(item => item.name).join(", ")}. Estes requisitos condicionam a recomendação, mesmo quando a percentagem é elevada.</p> : summary && <p className="mt-2 text-sm">{summary}</p>}
      <p className="mt-3 text-xs text-ink-soft">Esta avaliação apoia a triagem. A selecção ou contratação é uma decisão do recrutador, registada na etapa da candidatura.</p>
    </div>
    <div><h3 className="font-semibold">O que sustenta este resultado</h3><p className="mt-1 text-sm text-ink-soft">Compare o que a vaga exige com o que foi possível confirmar no CV.</p></div>
    <div className="grid gap-4 md:grid-cols-2">
    {groups.map(([state, label]) => {
      const matches = requirements.filter(item => stateOf(item.id) === state);
      if (!matches.length) return null;
      return <div key={state} className="rounded-lg border border-line bg-surface p-4"><h3 className="font-semibold text-sm">{label} ({matches.length})</h3>
        <ul className="mt-3 divide-y divide-line">{matches.map(item => <li key={item.id} className="py-3 first:pt-0 last:pb-0 text-sm">
          <p className="font-medium">{item.name}{item.is_mandatory ? " — obrigatório" : ""}</p>
          {item.description && <p className="mt-1 text-ink-soft">Exigido: {item.description}</p>}
          {evidence.find(entry => entry.requirement_id === item.id)?.explanation && <p className="mt-2 text-ink-soft">{evidence.find(entry => entry.requirement_id === item.id)?.explanation}</p>}
          {totalWeight > 0 && <p className="mt-2 text-xs font-medium text-brand-dark">{state === "unknown" ? "Contributo por determinar" : `Contribui ${format(item.weight / totalWeight * 100 * contribution(state))} de ${format(item.weight / totalWeight * 100)} pontos possíveis`}</p>}
        </li>)}</ul>
      </div>;
    })}
    </div>
    <details className="rounded-lg border border-line bg-canvas p-4 text-sm"><summary className="cursor-pointer font-medium">Como é calculada a percentagem?</summary>
      <p className="mt-3">Cada requisito tem um peso na avaliação. Quando está comprovado, recebe a totalidade dos seus pontos; quando está parcialmente comprovado, recebe metade; sem comprovação ou com informação contraditória, recebe zero. A soma dos contributos determina a percentagem final.</p>
      <p className="mt-2 text-ink-soft">Por exemplo: um requisito com 40 pontos possíveis contribui com 40 se comprovado, 20 se parcial e 0 se não comprovado. Os valores apresentados são arredondados a duas casas decimais.</p>
    </details>
    <p className="text-xs text-ink-soft">«Não comprovado» significa que o CV não apresenta evidência suficiente; não significa que o candidato não possui a competência. A percentagem não representa a probabilidade de sucesso na função.</p>
  </div>;
}
