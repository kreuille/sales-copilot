import { NextResponse } from "next/server";
import { requireWorkspaceSession, UnauthenticatedError } from "@/lib/auth/guard";
import { createProspect, listProspects } from "@/lib/data/prospects";

// Reference implementation of the auth + workspace-authorization pattern
// (FR-3.1) that every future workspace-scoped route should follow.
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ workspaceId: string }> }
) {
  const { workspaceId } = await params;
  try {
    await requireWorkspaceSession(workspaceId);
  } catch (error) {
    return unauthorizedResponse(error);
  }
  const prospects = await listProspects(workspaceId);
  return NextResponse.json({ prospects });
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ workspaceId: string }> }
) {
  const { workspaceId } = await params;
  try {
    await requireWorkspaceSession(workspaceId);
  } catch (error) {
    return unauthorizedResponse(error);
  }
  const body = await request.json();
  if (typeof body.fullName !== "string" || body.fullName.trim() === "") {
    return NextResponse.json({ error: "fullName is required" }, { status: 400 });
  }
  const prospect = await createProspect(workspaceId, {
    fullName: body.fullName,
    company: body.company,
    roleTitle: body.roleTitle,
    rawNotes: body.rawNotes,
  });
  return NextResponse.json({ prospect }, { status: 201 });
}

function unauthorizedResponse(error: unknown) {
  const status = error instanceof UnauthenticatedError ? 401 : 403;
  const message = error instanceof Error ? error.message : "Unauthorized";
  return NextResponse.json({ error: message }, { status });
}
