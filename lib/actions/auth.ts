"use server";

import { redirect } from "next/navigation";
import { AuthError } from "next-auth";
import { signIn } from "@/auth";
import { getUserByEmail, createUser } from "@/lib/data/users";
import { createWorkspaceWithOwner } from "@/lib/data/workspaces";

export async function signupAction(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const name = String(formData.get("name") ?? "").trim();
  const workspaceName = String(formData.get("workspaceName") ?? "").trim();

  if (!email || !password || !workspaceName) {
    redirect("/signup?error=missing_fields");
  }

  const existing = await getUserByEmail(email);
  if (existing) {
    redirect("/signup?error=email_taken");
  }

  const user = await createUser({ email, password, name: name || undefined });
  const workspace = await createWorkspaceWithOwner(user.id, workspaceName);

  try {
    await signIn("credentials", { email, password, redirectTo: `/w/${workspace.id}` });
  } catch (error) {
    if (error instanceof AuthError) {
      redirect("/login?error=invalid_credentials");
    }
    throw error; // rethrow NEXT_REDIRECT (the success path) and anything else
  }
}

export async function loginAction(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  try {
    await signIn("credentials", { email, password, redirectTo: "/" });
  } catch (error) {
    if (error instanceof AuthError) {
      redirect("/login?error=invalid_credentials");
    }
    throw error;
  }
}
