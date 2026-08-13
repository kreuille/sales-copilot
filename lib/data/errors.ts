export class NotFoundInWorkspaceError extends Error {
  constructor(entity: string, id: string) {
    super(`${entity} ${id} not found in this workspace`);
    this.name = "NotFoundInWorkspaceError";
  }
}
