"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { requireWorkspaceSession } from "@/lib/auth/guard";
import { createDeal, transitionDealStage } from "@/lib/data/deals";
import type { DealStage } from "@/app/generated/prisma/enums";

export async function createDealAction(workspaceId: string, prospectId: string, formData: FormData) {
  await requireWorkspaceSession(workspaceId);

  const stage = String(formData.get("stage") ?? "first_contact") as DealStage;
  const estimatedAmountRaw = String(formData.get("estimatedAmount") ?? "").trim();
  const estimatedAmount = estimatedAmountRaw ? Number(estimatedAmountRaw) : undefined;

  const deal = await createDeal(workspaceId, { prospectId, stage, estimatedAmount });
  redirect(`/w/${workspaceId}/deals/${deal.id}`);
}

export async function transitionDealStageAction(
  workspaceId: string,
  dealId: string,
  formData: FormData
) {
  await requireWorkspaceSession(workspaceId);

  const stage = String(formData.get("stage") ?? "") as DealStage;
  await transitionDealStage(workspaceId, dealId, stage);
  revalidatePath(`/w/${workspaceId}/deals/${dealId}`);
}
