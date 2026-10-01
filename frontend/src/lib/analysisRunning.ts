export function analysisRunning(executionId: string | null, executionStatus: string | undefined,
  applicationStatus: string | undefined, hasExecutionError: boolean) {
  if (executionId && executionStatus) return ["queued", "running"].includes(executionStatus);
  return !hasExecutionError && (!!executionId || ["queued", "running"].includes(applicationStatus ?? ""));
}
