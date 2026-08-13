import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { prisma } from "@/lib/db/client";
import { createProspect, getProspect, listProspects } from "@/lib/data/prospects";
import { createDeal, getDeal, listDeals } from "@/lib/data/deals";
import { NotFoundInWorkspaceError } from "@/lib/data/errors";

// Explicit regression test required by security-architecture.md
// ("un utilisateur du workspace A ne peut jamais lire/écrire une donnée du
// workspace B") — runs against a real Postgres database, not a mock, so it
// actually exercises the workspace_id filter in lib/data/*.
describe("workspace isolation", () => {
  let workspaceA: { id: string };
  let workspaceB: { id: string };

  beforeAll(async () => {
    workspaceA = await prisma.workspace.create({ data: { name: "Workspace A" } });
    workspaceB = await prisma.workspace.create({ data: { name: "Workspace B" } });
  });

  afterAll(async () => {
    await prisma.workspace.deleteMany({ where: { id: { in: [workspaceA.id, workspaceB.id] } } });
    await prisma.$disconnect();
  });

  it("does not leak a workspace B prospect into workspace A's list", async () => {
    const prospectA = await createProspect(workspaceA.id, { fullName: "Prospect A" });
    await createProspect(workspaceB.id, { fullName: "Prospect B" });

    const listA = await listProspects(workspaceA.id);

    expect(listA.map((p) => p.id)).toEqual([prospectA.id]);
  });

  it("refuses to read a prospect by id across workspaces", async () => {
    const prospectB = await createProspect(workspaceB.id, { fullName: "Cross-workspace target" });

    await expect(getProspect(workspaceA.id, prospectB.id)).rejects.toThrow(
      NotFoundInWorkspaceError
    );
    await expect(getProspect(workspaceB.id, prospectB.id)).resolves.toMatchObject({
      id: prospectB.id,
    });
  });

  it("refuses to read a deal by id across workspaces", async () => {
    const prospectB = await createProspect(workspaceB.id, { fullName: "Deal owner B" });
    const dealB = await createDeal(workspaceB.id, {
      prospectId: prospectB.id,
      stage: "first_contact",
    });

    await expect(getDeal(workspaceA.id, dealB.id)).rejects.toThrow(NotFoundInWorkspaceError);

    const dealsInA = await listDeals(workspaceA.id);
    expect(dealsInA.find((d) => d.id === dealB.id)).toBeUndefined();
  });
});
