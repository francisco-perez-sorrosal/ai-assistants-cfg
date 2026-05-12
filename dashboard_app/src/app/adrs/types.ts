/**
 * Shape of a loaded ADR record — used by both the server page and the client
 * filter component. Must not import server-only modules.
 */
export type AdrRecord = {
  readonly body: string;
  readonly data: Record<string, unknown>;
  readonly isDraft: boolean;
  readonly path: string;
};
