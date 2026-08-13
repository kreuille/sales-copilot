import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { prisma } from "@/lib/db/client";
import { requireMembership } from "@/lib/data/workspace-members";

describe("requireMembership", () => {
  let workspace: { id: string };
  let owner: { id: string };
  let member: { id: string };
  let outsider: { id: string };

  beforeAll(async () => {
    workspace = await prisma.workspace.create({ data: { name: "Guard test workspace" } });
    owner = await prisma.user.create({
      data: { email: "owner@example.com", passwordHash: "x" },
    });
    member = await prisma.user.create({
      data: { email: "member@example.com", passwordHash: "x" },
    });
    outsider = await prisma.user.create({
      data: { email: "outsider@example.com", passwordHash: "x" },
    });
    await prisma.workspaceMember.createMany({
      data: [
        { workspaceId: workspace.id, userId: owner.id, role: "owner" },
        { workspaceId: workspace.id, userId: member.id, role: "member" },
      ],
    });
  });

  afterAll(async () => {
    await prisma.workspace.delete({ where: { id: workspace.id } });
    await prisma.user.deleteMany({
      where: { id: { in: [owner.id, member.id, outsider.id] } },
    });
    await prisma.$disconnect();
  });

  it("allows a member to access their workspace", async () => {
    await expect(requireMembership(workspace.id, member.id)).resolves.toMatchObject({
      role: "member",
    });
  });

  it("rejects a user who is not a member of the workspace", async () => {
    await expect(requireMembership(workspace.id, outsider.id)).rejects.toThrow(
      /not a member/
    );
  });

  it("rejects a member (non-owner) when an owner role is required", async () => {
    await expect(requireMembership(workspace.id, member.id, "owner")).rejects.toThrow(
      /must be an owner/
    );
  });

  it("allows an owner when an owner role is required", async () => {
    await expect(
      requireMembership(workspace.id, owner.id, "owner")
    ).resolves.toMatchObject({ role: "owner" });
  });
});
