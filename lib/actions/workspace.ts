"use server";

import { revalidatePath } from "next/cache";
import { requireWorkspaceSession } from "@/lib/auth/guard";
import { createWorkspaceContextVersion } from "@/lib/data/workspace-context";
import { createProspect } from "@/lib/data/prospects";

export async function updateWorkspaceContextAction(workspaceId: string, formData: FormData) {
  await requireWorkspaceSession(workspaceId);

  const offerDescription = String(formData.get("offerDescription") ?? "").trim();
  const icpDescription = String(formData.get("icpDescription") ?? "").trim();
  const tone = String(formData.get("tone") ?? "").trim();
  const pricingSummary = String(formData.get("pricingSummary") ?? "").trim();

  if (!offerDescription || !icpDescription || !tone) {
    throw new Error("offerDescription, icpDescription et tone sont requis");
  }

  await createWorkspaceContextVersion(workspaceId, {
    offerDescription,
    icpDescription,
    tone,
    pricingSummary: pricingSummary || undefined,
  });
  revalidatePath(`/w/${workspaceId}`);
}

export async function createProspectAction(workspaceId: string, formData: FormData) {
  await requireWorkspaceSession(workspaceId);

  const fullName = String(formData.get("fullName") ?? "").trim();
  if (!fullName) {
    throw new Error("fullName est requis");
  }
  const company = String(formData.get("company") ?? "").trim();

  await createProspect(workspaceId, { fullName, company: company || undefined });
  revalidatePath(`/w/${workspaceId}`);
}
