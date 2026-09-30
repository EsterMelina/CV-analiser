import "./CompatibilitySummary.css";

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
  evidence: { requirement_id: number; state: string; explanation?: string }[];
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

export function CompatibilitySummary({
  score,
  method,
  requirements,
  evidence,
  recommendation,
  summary,
}: Props) {
  if (method.startsWith("mock"))
    return (
      <div role="status" className="cs__status">
        <h2>Compatibilidade ainda não calculada</h2>
        <p>
          Este registo antigo foi criado pelo simulador. Execute uma nova análise com IA para
          avaliar este CV.
        </p>
      </div>
    );

  if (score == null)
    return <p className="cs__none">Não foi possível calcular a compatibilidade deste documento.</p>;

  const totalWeight = requirements.reduce((total, item) => total + item.weight, 0);
  const states = new Map(evidence.map((item) => [item.requirement_id, item.state]));
  const format = (value: number) =>
    value.toLocaleString("pt-PT", { maximumFractionDigits: 2 });
  const knownStates = groups.map(([state]) => state as string);
  const stateOf = (id: number) =>
    knownStates.includes(states.get(id) ?? "") ? states.get(id) : "unknown";
  const missingMandatory = requirements.filter(
    (item) => item.is_mandatory && stateOf(item.id) !== "evidenced",
  );
  const contribution = (state: string | undefined) =>
    state === "evidenced" ? 1 : state === "partial" ? 0.5 : 0;

  return (
    <div className="cs">
      {/* Hero */}
      <div className="cs__hero">
        <p className="cs__eyebrow">Avaliação do perfil</p>

        <div className="cs__hero-top">
          <p className="cs__score">{format(score)}%</p>
          <div>
            <h2 className="cs__score-title">Compatibilidade com os requisitos da vaga</h2>
            <p className="cs__score-sub">
              Resultado da comparação entre o CV e os critérios definidos.
            </p>
          </div>
        </div>

        {recommendation && (
          <h3 className="cs__recommendation">
            {recommendation === "Requisito obrigatório ausente"
              ? "Requisitos obrigatórios por comprovar"
              : recommendation}
          </h3>
        )}

        <p className="cs__summary">
          Com base nas evidências disponíveis no CV e no peso de cada requisito, foi apurada uma
          compatibilidade de {format(score)}%.
        </p>

        {missingMandatory.length > 0 ? (
          <p className="cs__warn">
            <strong>A adequação à vaga ainda não está comprovada.</strong> Falta comprovação
            completa dos seguintes requisitos obrigatórios:{" "}
            {missingMandatory.map((item) => item.name).join(", ")}. Estes requisitos condicionam a
            recomendação, mesmo quando a percentagem é elevada.
          </p>
        ) : (
          summary && <p className="cs__summary">{summary}</p>
        )}

        <p className="cs__disclaimer">
          Esta avaliação apoia a triagem. A selecção ou contratação é uma decisão do recrutador,
          registada na etapa da candidatura.
        </p>
      </div>

      {/* Secção */}
      <div>
        <h3 className="cs__section-title">O que sustenta este resultado</h3>
        <p className="cs__section-sub">
          Compare o que a vaga exige com o que foi possível confirmar no CV.
        </p>
      </div>

      {/* Grid */}
      <div className="cs__grid">
        {groups.map(([state, label]) => {
          const matches = requirements.filter((item) => stateOf(item.id) === state);
          if (!matches.length) return null;
          return (
            <div key={state} className={`cs__group cs__group--${state}`}>
              <h3 className="cs__group-title">
                {label} ({matches.length})
              </h3>
              <ul className="cs__list">
                {matches.map((item) => (
                  <li key={item.id} className="cs__item">
                    <p className="cs__item-name">
                      {item.name}
                      {item.is_mandatory && <em> — obrigatório</em>}
                    </p>
                    {item.description && (
                      <p className="cs__item-desc">Exigido: {item.description}</p>
                    )}
                    {evidence.find((entry) => entry.requirement_id === item.id)?.explanation && (
                      <p className="cs__item-expl">
                        {evidence.find((entry) => entry.requirement_id === item.id)?.explanation}
                      </p>
                    )}
                    {totalWeight > 0 && (
                      <p className="cs__item-contrib">
                        {state === "unknown"
                          ? "Contributo por determinar"
                          : `Contribui ${format(
                              (item.weight / totalWeight) * 100 * contribution(state),
                            )} de ${format((item.weight / totalWeight) * 100)} pontos possíveis`}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      {/* Details */}
      <details className="cs__details">
        <summary>Como é calculada a percentagem?</summary>
        <p>
          Cada requisito tem um peso na avaliação. Quando está comprovado, recebe a totalidade dos
          seus pontos; quando está parcialmente comprovado, recebe metade; sem comprovação ou com
          informação contraditória, recebe zero. A soma dos contributos determina a percentagem
          final.
        </p>
        <p>
          <em>
            Por exemplo: um requisito com 40 pontos possíveis contribui com 40 se comprovado, 20 se
            parcial e 0 se não comprovado. Os valores apresentados são arredondados a duas casas
            decimais.
          </em>
        </p>
      </details>

      <p className="cs__footer">
        «Não comprovado» significa que o CV não apresenta evidência suficiente; não significa que o
        candidato não possui a competência. A percentagem não representa a probabilidade de sucesso
        na função.
      </p>
    </div>
  );
}